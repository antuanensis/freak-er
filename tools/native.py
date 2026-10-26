"""Build the exact-version native sequencer experiment; no device operations.

Reuse the pinned upstream ELF relocation/linker and MFF verification. Firmware
prologue fragments are read from the user's official image, never shipped here.
"""

from __future__ import annotations

import hashlib
import importlib.util
import struct
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from tools import firmware

# firmware initializes the pinned upstream import path.
# isort: split
from freakpatch import thumb
from freakpatch.patcher import Edit, Hook, Part, Patch

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "vendor/ThisFirmwareDoesNotExist"
SPEC = importlib.util.spec_from_file_location("native_linker", UPSTREAM / "tools/build_patch.py")
assert SPEC and SPEC.loader
LINKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LINKER)
SCAN_SPEC = importlib.util.spec_from_file_location("native_refscan", UPSTREAM / "tests/refscan.py")
assert SCAN_SPEC and SCAN_SPEC.loader
SCANNER = importlib.util.module_from_spec(SCAN_SPEC)
SCAN_SPEC.loader.exec_module(SCANNER)
LINKER.CLANG_ARGS += [
    "-Oz",
    "-ffreestanding",
    "-fno-builtin",
    "-ffunction-sections",
    "-fno-jump-tables",
    "-fno-unwind-tables",
    "-fno-asynchronous-unwind-tables",
    "-mno-movt",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-Wno-unused-parameter",
]

# Use the append window, eight proven factory commands and the oled-only helper.
# The stock synth's audio/conf/filter/ioc boot commands remain present.
REGIONS = (
    (0x0807FA60, 0x0807FFFF),
    (0x0802BE90, 0x0802C132),
    (0x0802CA94, 0x0802CC04),
    (0x0802C2F4, 0x0802C3E2),
    (0x0802D44C, 0x0802D530),
    (0x0802BB60, 0x0802BC00),
    (0x0802BC00, 0x0802BC84),
    (0x0802BC84, 0x0802BD10),
    (0x0802BD94, 0x0802BE90),
    (0x0802EE74, 0x0802EF26),
)
TRAMPOLINES = {
    "original_set": 0x08023C9C,
    "original_note": 0x08048524,
    "original_load": 0x080284F0,
    "original_clear": 0x08027F48,
    "original_transport": 0x0802880C,
    "original_builtin": 0x08028264,
}
ENTRIES = {
    0x08023C9C: "set_parameter",
    0x08048524: "note",
    0x080284F0: "load_sequence",
    0x08027F48: "clear_pattern",
    0x0802880C: "transport",
    0x08052F1C: "popup",
    0x08028264: "builtin_pattern",
    0x08023C2C: "get_parameter",
    0x0802C480: "encoder_value",
}
CALLS = {
    0x0801103C: ("boot", 0x0800E730),
    0x08029112: ("boundary", 0x080281F8),
    0x0803A824: ("poll", 0x08039DA4),
    # Editable sample/type values only. Model/sync context reads stay global.
    0x08040D82: ("scaled_parameter", 0x0800E644),
    0x08040DFC: ("scaled_parameter", 0x0800E644),
}
WORDS = {
    0x08074C44: ("press", 0x0804347D),
    0x08074C48: ("release", 0x08043495),
    0x08074C70: ("encoder", 0x08042BC9),
    0x08074C54: ("pot", 0x08040221),
}


def read_stock(payload: bytes, address: int, size: int) -> bytes:
    offset = address - firmware.MAIN_BASE
    if offset < 0 or offset + size > len(payload):
        raise ValueError("stock address out of bounds")
    return payload[offset : offset + size]


def displaced_prologue(payload: bytes, original: int, destination: int) -> bytes:
    """Relocate only audited entry forms; reject PC-relative instructions otherwise."""
    raw = read_stock(payload, original, 4)
    first, second = struct.unpack("<HH", raw)
    if original == 0x0802682C:
        # PUSH + literal LDR: keep the register load, relocate its literal value.
        if first & 0xFE00 != 0xB400 or second & 0xF800 != 0x4800:
            raise ValueError("unexpected send prologue")
        literal = ((original + 6) & ~3) + (second & 255) * 4
        register = (second >> 8) & 7
        return (
            struct.pack("<HH", first, 0x4801 | register << 8)
            + thumb.b_w(destination + 4, original + 4)
            + read_stock(payload, literal, 4)
        )
    wide_push = first == 0xE92D and not second & 0x8000
    push_add = first & 0xFE00 == 0xB400 and second & 0xF800 == 0x1800
    movw = first & 0xFBF0 == 0xF240
    if not (wide_push or push_add or movw):
        raise ValueError(f"unaudited prologue at {original:#x}")
    return raw + thumb.b_w(destination + 4, original + 4)


def section_alignments(source: Path, sections: dict[str, bytes]) -> dict[str, int]:
    """Read ELF alignment without changing the pinned assembler's interface."""
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "alignment.o"
        subprocess.run(["clang", *LINKER.CLANG_ARGS, str(source), "-o", str(output)], check=True)
        elf = output.read_bytes()
    names, headers = LINKER._headers(elf)
    alignment = {}
    for name, header in zip(names, headers, strict=True):
        if name in sections:
            if sections[name] != elf[header[4] : header[4] + header[5]]:
                raise ValueError("native code changed between compiler passes")
            align = header[8]
            if align not in (2, 4) or (align == 4 and len(sections[name]) % 4):
                raise ValueError(f"unsupported native section alignment: {name}")
            alignment[name] = align
    return alignment


def place_sections(sections: dict[str, bytes], alignment: dict[str, int]) -> dict[str, int]:
    """Bounded exact packing: word-aligned sections first, then halfword sections."""
    order = sorted(sections, key=lambda name: (-alignment[name], -len(sections[name]), name))
    reachable = [1] * (len(order) + 1)
    remaining = [0] * (len(order) + 1)
    for i in range(len(order) - 1, -1, -1):
        size = len(sections[order[i]])
        reachable[i] = reachable[i + 1] | (reachable[i + 1] << size)
        remaining[i] = remaining[i + 1] + size
    visits = 0

    @lru_cache(None)
    def solve(i: int, capacities: tuple[int, ...]) -> tuple[int, ...] | None:
        nonlocal visits
        visits += 1
        if visits > 1_000_000:
            raise ValueError("native placement search limit exceeded")
        if i == len(order):
            return ()
        waste = sum(cap - ((reachable[i] & ((1 << (cap + 1)) - 1)).bit_length() - 1) for cap in capacities)
        if waste > sum(capacities) - remaining[i]:
            return None
        size = len(sections[order[i]])
        tried = set()
        for j, cap in enumerate(capacities):
            if cap in tried or size > cap:
                continue
            tried.add(cap)
            next_caps = list(capacities)
            next_caps[j] -= size
            result = solve(i + 1, tuple(sorted(next_caps)))
            if result is not None:
                return (cap, *result)
        return None

    capacities = tuple(sorted(hi - lo for lo, hi in REGIONS))
    result = solve(0, capacities)
    if result is None:
        raise ValueError("native sections do not fit proven regions")
    free = list(REGIONS)
    placement = {}
    for name, capacity in zip(order, result, strict=True):
        index = next(i for i, (lo, hi) in enumerate(free) if hi - lo == capacity)
        lo, hi = free[index]
        if lo % alignment[name]:
            raise ValueError(f"misaligned native section: {name}")
        placement[name] = lo
        free[index] = lo + len(sections[name]), hi
    return placement


def build(raw: bytes, *, stage: str = "features") -> tuple[Patch, dict]:
    if stage not in ("placement", "passthrough", "features"):
        raise ValueError("unknown native build stage")
    hooks = stage != "placement"
    firmware.inspect(raw)
    update = firmware.mff.Update.from_bytes(raw)
    payload = firmware.mff.main_payload(update.read(update.main_name))
    first, second = struct.unpack("<HH", read_stock(payload, 0x0802C480, 4))
    # Audited inline LDRSH: r6 <- [r3 + r9*2], no flag changes.
    if not (
        first & 0xFFF0 == 0xF930
        and first & 15 == 3
        and second >> 12 == 6
        and second & 15 == 9
        and (second >> 4) & 3 == 1
    ):
        raise ValueError("inline encoder value-read contract changed")
    for lo, hi, expected in (
        (0x0802BE90, 0x0802C132, {(0x08074094, "word"), (0x0802BE40, "ldr/adr")}),
        (0x0802CA94, 0x0802CC04, {(0x080740D4, "word")}),
        (0x0802C2F4, 0x0802C3E2, {(0x08073FF4, "word"), (0x0802C154, "ldr/adr")}),
        (0x0802D44C, 0x0802D530, {(0x080740B4, "word")}),
        (0x0802BB60, 0x0802BC00, {(0x08074054, "word"), (0x0802B7B2, "ldr/adr")}),
        (0x0802BC00, 0x0802BC84, {(0x08074034, "word")}),
        (0x0802BC84, 0x0802BD10, {(0x08073FD4, "word")}),
        (0x0802BD94, 0x0802BE90, {(0x08074134, "word")}),
        # Retired oled callers; a data word and a Thumb-32 second halfword
        # also decode as references. See native-integration.md.
        (
            0x0802EE74,
            0x0802EF26,
            {(0x0802BC42, "bl/b.w"), (0x0802BC6C, "bl/b.w"), (0x0802E92C, "b"), (0x0802EB16, "ldr/adr")},
        ),
    ):
        if set(SCANNER.references(payload, firmware.MAIN_BASE, lo, hi)) != expected:
            raise ValueError("unexpected reference into a retired factory region")
    arguments = list(LINKER.CLANG_ARGS)
    if stage == "passthrough":
        LINKER.CLANG_ARGS += ["-DFREAKER_PASSTHROUGH=1"]
    try:
        sections, symbols, relocations = LINKER.assemble(ROOT / "native/stock_sequencer.c")
        sections = {k: v for k, v in sections.items() if v}
        alignment = section_alignments(ROOT / "native/stock_sequencer.c", sections)
    finally:
        LINKER.CLANG_ARGS = arguments
    place = place_sections(sections, alignment)
    code = LINKER.link(sections, relocations, place)
    addresses = {name: place[section] + (offset & ~1) for name, (section, offset) in symbols.items()}
    for name, original in TRAMPOLINES.items():
        section, offset = symbols[name]
        offset &= ~1
        moved = displaced_prologue(payload, original, addresses[name])
        if offset + len(moved) != len(code[section]):
            raise ValueError(f"invalid trampoline size: {name}")
        code[section][offset:] = moved
    branches = []
    edits = []
    for site, (name, target) in CALLS.items():
        if read_stock(payload, site, 4) != thumb.bl(site, target):
            raise ValueError(f"stock call mismatch: {site:#x}")
        if hooks:
            branches.append(Hook(site, "bl", name))
    for site, name in ENTRIES.items():
        if hooks and not (stage == "passthrough" and name == "popup"):
            branches.append(Hook(site, "b.w", name))
    for site, (name, target) in WORDS.items():
        if struct.unpack("<I", read_stock(payload, site, 4))[0] != target:
            raise ValueError(f"stock vtable mismatch: {site:#x}")
        if hooks:
            edits.append(Edit(site, "word", addresses[name] | 1))
    for slot, entry in (
        (0x08074094, 0x0802BE91),
        (0x080740D4, 0x0802CA95),
        (0x08073FF4, 0x0802C2F5),
        (0x080740B4, 0x0802D44D),
        (0x08074054, 0x0802BB61),
        (0x08074034, 0x0802BC01),
        (0x08073FD4, 0x0802BC85),
        (0x08074134, 0x0802BD95),
    ):
        if struct.unpack("<I", read_stock(payload, slot, 4))[0] != entry:
            raise ValueError("factory command slot mismatch")
        edits.append(Edit(slot, "word", 0x0802B8ED))
    # Parts stay word-aligned for the upstream verifier; individual functions
    # inside them retain their ELF alignment, including word-aligned literals.
    parts = []
    for lo, hi in REGIONS:
        members = [s for s in code if lo <= place[s] < hi]
        if not members:
            continue
        end = max(place[s] + len(code[s]) for s in members)
        block = bytearray(b"\xff" * (end - lo))
        for section in members:
            offset = place[section] - lo
            block[offset : offset + len(code[section])] = code[section]
        parts.append(
            Part(
                (lo, end),
                bytes(block),
                {name: address - lo for name, address in addresses.items() if lo <= address < end},
            )
        )
    patch = Patch(
        f"stock-sequencer-{stage}",
        "Stock sequencer probability and live editing",
        tuple(parts),
        tuple(branches),
        tuple(edits),
        {},
    )
    report = {
        "native_bytes": sum(map(len, code.values())),
        "capacity_bytes": sum(hi - lo for lo, hi in REGIONS),
        "runtime_bytes": 12,
        "symbols": addresses,
        "hooks_enabled": hooks,
        "features_enabled": stage == "features",
        "device_tested": False,
        "stage": stage,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "source_sha256": hashlib.sha256((ROOT / "native/stock_sequencer.c").read_bytes()).hexdigest(),
        "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "upstream_revision": "083b15cabde98fc31eb89b40562aeeea38224968",
        "compiler": subprocess.run(
            ["clang", "--version"], check=True, capture_output=True, text=True
        ).stdout.splitlines()[0],
        "sections": {s: {"address": place[s], "bytes": len(c), "alignment": alignment[s]} for s, c in code.items()},
    }
    return patch, report

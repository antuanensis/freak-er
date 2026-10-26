# FREAKOS development instructions

This repository develops incremental patches for Arturia MicroFreak 5.0.0.2084.
The C code extends stock sequencing; it must never become a second playback
engine. Native hooks, RAM, UI and raw persistence now have emulation evidence;
r2 has a positive user hardware report; r3, MCC compatibility and timing still
require validation. Never describe host tests or a generated MFF as device
validation.

## Recover context

Read this file, `docs/session.md`, `docs/tasks.md`, the active spec in `docs/specs/`,
then relevant architecture/ADRs and implementation/tests. `idea.md` is the original
vision; the ordered queue controls the current implementation scope.

## Layout and commands

- `core/`: allocation-free C11 probability/editor extension; no device addresses,
  note bank, modulation bank, clock, or advancing playhead.
- `native/stock_sequencer.c`: exact-version ARM adapter; preserve its stock ABI.
- `tools/native.py`, `tools/firmware.py`: staged native builds, strict inspection,
  verified publication and historical upstream baseline reproduction.
- `tests/`, `examples/`: behavioral tests and reference demonstrations.
- `vendor/ThisFirmwareDoesNotExist/`: pinned upstream source, tests, and analysis.
  Follow its own `AGENTS.md` when working there. Keep it unchanged unless explicitly
  updating the upstream snapshot; record provenance and review the whole update.
- `docs/`: specifications, evidence, ordered work, and current handoff.
- `make test`, `make demo`, `make check-arm`: dependency-free local checks.
- `make setup`, `make lint`, `make upstream-test`: pinned Python development tools.
  Set `FREAKPATCH_STOCK_MFF` to the official local file for firmware/emulation tests.
- `make test-sanitize`: C tests with AddressSanitizer and UndefinedBehaviorSanitizer.
- `make stock-test`: real stock-function/C integration tests through Unicorn and
  a host shared library. Apple Silicon sandbox restrictions may require normal
  host test access; see testing.md.
- `make native-test`: native adapter plus stock routines under Unicorn. Run after
  native C, hook, state-layout or placement changes; includes register/APSR,
  transport, recorder, smoothing and persistence checks.
- `build --stage placement|passthrough|features`: separate local experiments with
  manifests. Always start from official input; never stack patched images.

## Implementation rules

- Implement phases and feature slices in queue order. Do not silently substitute
  an external MIDI companion for native firmware.
- Current scope is spec 004 (extending spec 003): per-step probability and live
  editing within stock’s A/B, shared 4..64-step length and existing four modulation
  tracks only. No conditional triggers or additional sequencer. Do not expand
  scope from idea.md.
- Specify nontrivial behavior before coding. Keep algorithms independent of native
  hooks; use fixed-size state and deterministic seeds. Stock supplies each actual
  boundary; never increment its cursor from the extension or reroll on queries.
- Forward stock parameter IDs/raw 16-bit values after stock eligibility checks.
  Preserve signed matrix amounts and stock oscillator/sample automation. Keep
  stock four-track capacity, restoration, smoothing, note-offs and tie behavior.
- New probability applies only to new sequencer note/chord starts. It must not
  filter modulation playback, note-offs, tie continuation, MIDI/keyboard or arp.
- Edit and tick calls are serialized by the caller. Host live editing proves
  transport continuity, not interrupt-safe concurrent access on hardware.
- New native patches require official-image evidence for every hook, displaced
  instruction, register contract, and RAM/code region. Check static references and
  fall-through; compose patches before applying them, never stack patched files.
- New state may use only proven RAM or stock-managed preset parameters. Never call
  flash writers or alter bootloader, calibration, or update-status regions.
- Current storage contract is ADR 0003 and docs/native-integration.md. Runtime
  stays in twelve unused table bytes; never allocate an arbitrary heap/stack gap.
- Relative controls need selected-value reads and a raw increment cache. Preserve
  the inline encoder hook's registers, LR metadata and APSR flags. Never swap
  global values/table pointers temporarily to fake a future edit.
- A newly assigned Shift/local track needs baseline snapshots on other steps;
  an unshifted/global assignment initializes the full track to the new value.
  Existing global edits scale proportionally, preserve absent cells and use a
  bounded offset for zero/sign-changing references. Keep signed conversion.
- Reuse stock target assignment and proven record fields; require parity against
  the actual recorder for all 57 eligible IDs. The position getter and normal
  set-and-send stay unhooked. Do not restore the cloned recorder/position shim.
- r3 also owns Oct tap/600-ms delete, Shift+Hold cleanup, Record+Rate+release copy
  and Preset first-note editing. Preserve flags, other chord tones and rests.
- Code budget is 3,809 audited bytes; r3 uses 3,778. Retire only the eight proven
  factory commands and oled-only helper. Keep boot audio/conf/filter/ioc intact.
  Pack whole functions using actual ELF alignment and word-aligned region Parts.
  Recheck references, input identity, output verification and three staged builds
  after changes. Never solve overflow by using an arbitrary address.
- UI fields are serialized in main-loop context; random/allowed/close_pending
  remain volatile interrupt-owned fields. Runtime size remains twelve bytes.
- No production dependencies or broad framework changes without a concrete need.

## Boundaries and completion

Never commit, distribute, or print firmware bytes, calibration/unit data, stock
disassembly, or dumps. Keep `original_firmware/`, `.mff`, binaries, and generated
artifacts ignored. Do not flash hardware, publish, or commit without explicit user
instruction. Hardware tests belong to the user under `docs/recovery.md`.
The initial checkpoint contains r3 source and documented r2 history; see
`docs/revisions.md`. Keep supplied manuals and local editor settings ignored;
input setup is in `docs/local-inputs.md`. Shrinking and new feature implementation
are separate work after this checkpoint, with existing behavior preserved.

A slice is done when its behavior is tested, relevant commands pass, limitations
are explicit, and its spec matches reality. Update tasks when priorities/status
change, replace stale session state, and append meaningful milestones to devlog.
Record consequential architecture decisions in `docs/adr/`. Never mark a hardware
gate complete from upstream reports or single-function emulation alone.
Record r2’s user report without inventing its hash or conditions. Keep r3’s
hardware gates pending until actual target-device results exist. Never replace
device evidence with emulator results.

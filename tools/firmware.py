"""Inspect official input or build local experimental firmware; never flash."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor/ThisFirmwareDoesNotExist/src"))

from freakpatch import mff  # noqa: E402
from freakpatch.patcher import (  # noqa: E402
    APPEND_BASE,
    LATEST_SHA256,
    LATEST_VERSION,
    MAIN_BASE,
    MAIN_END,
    Patch,
    apply,
    check_latest,
)

BASELINE_SHA256 = "282ec291a73e89800c52872e4446664e350818978824e1e89003bdadda7d4834"


def inspect(raw: bytes) -> dict[str, str | int]:
    check_latest(raw)
    update = mff.Update.from_bytes(raw)
    payload = mff.main_payload(update.read(update.main_name))
    return {
        "firmware": LATEST_VERSION,
        "sha256": LATEST_SHA256,
        "update_bytes": len(raw),
        "main_payload_bytes": len(payload),
        "main_base": f"{MAIN_BASE:#010x}",
        "append_base": f"{APPEND_BASE:#010x}",
        "append_window_bytes_including_checksum": MAIN_END - APPEND_BASE,
    }


def baseline(raw: bytes) -> bytes:
    patched = apply(raw, Patch.load("release"))
    if hashlib.sha256(patched).hexdigest() != BASELINE_SHA256:
        raise ValueError("baseline differs from the pinned upstream Release build")
    return patched


def publish_new(output: Path, data: bytes) -> None:
    """Publish a complete file atomically without replacing an existing path."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "baseline"):
        child = commands.add_parser(command)
        child.add_argument("firmware", type=Path)
        if command == "baseline":
            child.add_argument("-o", "--output", type=Path, required=True)
    child = commands.add_parser("build")
    child.add_argument("firmware", type=Path)
    child.add_argument("--stage", choices=("placement", "passthrough", "features"), required=True)
    child.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw = args.firmware.read_bytes()
        details = inspect(raw)
        if args.command == "inspect":
            for key, value in details.items():
                print(f"{key}: {value}")
        elif args.command == "baseline":
            patched = baseline(raw)
            publish_new(args.output, patched)
            print(f"wrote {args.output}")
            print(f"sha256: {BASELINE_SHA256}")
            print("Upstream Release baseline only; no native FREAKOS features. Nothing flashed.")
        else:
            from tools import native

            if args.output.suffix.lower() != ".mff":
                raise ValueError("native output must have a .mff extension")
            patch, report = native.build(raw, stage=args.stage)
            patched = apply(raw, patch)
            report["output_sha256"] = hashlib.sha256(patched).hexdigest()
            report["output_bytes"] = len(patched)
            manifest = args.output.with_suffix(".json")
            if args.output.exists() or manifest.exists():
                raise FileExistsError("output or manifest already exists")
            # Publish a verified manifest first; never leave an unexplained image.
            publish_new(manifest, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
            try:
                publish_new(args.output, patched)
            except OSError:
                manifest.unlink()
                raise
            print(f"wrote {args.output}")
            print(f"manifest: {manifest}")
            print(f"sha256: {report['output_sha256']}")
            print(f"stage: {args.stage}; native bytes: {report['native_bytes']}; runtime bytes: 12")
            print("Experimental; no device validation. Nothing flashed. See docs/recovery.md.")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"firmware: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

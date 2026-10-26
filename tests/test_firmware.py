"""Tooling boundaries plus optional integration against the user's official file."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import firmware


class NativePlacement(unittest.TestCase):
    def test_halfword_sections_pack_without_misaligning_word_sections(self):
        from tools import native

        sections = {"word": b"x" * 8, "half": b"y" * 6, "tiny": b"z" * 2}
        with patch.object(native, "REGIONS", ((0x1000, 0x100A), (0x2000, 0x2006))):
            result = native.place_sections(sections, {"word": 4, "half": 2, "tiny": 2})
        self.assertEqual(result, {"word": 0x1000, "half": 0x2000, "tiny": 0x1008})

    def test_oversized_whole_function_is_rejected(self):
        from tools import native

        with (
            patch.object(native, "REGIONS", ((0x1000, 0x100A), (0x2000, 0x2006))),
            self.assertRaisesRegex(ValueError, "do not fit"),
        ):
            native.place_sections({"large": b"x" * 12}, {"large": 4})


class FirmwareBoundaries(unittest.TestCase):
    def test_unknown_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "not the official"):
            firmware.inspect(b"not firmware")
        with self.assertRaisesRegex(ValueError, "not the official"):
            firmware.baseline(b"not firmware")

    def test_invalid_input_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.mff"
            output = Path(directory) / "result.mff"
            source.write_bytes(b"unrecognized")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(firmware.main(["baseline", str(source), "-o", str(output)]), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), b"unrecognized")

    def test_atomic_publication_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.mff"
            firmware.publish_new(output, b"complete verified result")
            with self.assertRaises(FileExistsError):
                firmware.publish_new(output, b"replacement")
            self.assertEqual(output.read_bytes(), b"complete verified result")
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_publication_does_not_follow_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "official.mff"
            source.write_bytes(b"original")
            output = Path(directory) / "link.mff"
            output.symlink_to(source)
            with self.assertRaises(FileExistsError):
                firmware.publish_new(output, b"replacement")
            self.assertEqual(source.read_bytes(), b"original")
            self.assertTrue(output.is_symlink())

    def test_missing_input_is_clean_error(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(firmware.main(["inspect", str(Path(directory) / "absent.mff")]), 1)
            self.assertIn("firmware:", error.getvalue())
            self.assertNotIn("Traceback", error.getvalue())


class OfficialFirmware(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        default = firmware.ROOT / "original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff"
        cls.path = Path(os.environ.get("FREAKPATCH_STOCK_MFF", default))
        if not cls.path.is_file():
            raise unittest.SkipTest("official firmware absent; set FREAKPATCH_STOCK_MFF")
        cls.raw = cls.path.read_bytes()
        firmware.inspect(cls.raw)  # A supplied but incorrect version must fail, not skip.

    def test_inspection_and_deterministic_baseline(self):
        details = firmware.inspect(self.raw)
        self.assertEqual(details["main_payload_bytes"], 473695)
        result = firmware.baseline(self.raw)
        self.assertEqual(result, firmware.baseline(self.raw))
        self.assertEqual(hashlib.sha256(result).hexdigest(), firmware.BASELINE_SHA256)
        self.assertEqual(len(result), len(self.raw))
        with self.assertRaisesRegex(ValueError, "not the official"):
            firmware.baseline(result)

    def test_cli_build_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release.mff"
            args = ["baseline", str(self.path), "-o", str(output)]
            with contextlib.redirect_stdout(io.StringIO()) as message:
                self.assertEqual(firmware.main(args), 0)
            self.assertIn("no native FREAKOS features", message.getvalue())
            first = output.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(firmware.main(args), 1)
                self.assertEqual(firmware.main(["baseline", str(self.path), "-o", str(self.path)]), 1)
            self.assertEqual(first, output.read_bytes())
            self.assertEqual(self.raw, self.path.read_bytes())

    def test_native_cli_stage_manifest_reproducibility_and_overwrite_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "experiment.mff"
            args = ["build", str(self.path), "--stage", "features", "-o", str(output)]
            with contextlib.redirect_stdout(io.StringIO()) as message:
                self.assertEqual(firmware.main(args), 0)
            self.assertIn("no device validation", message.getvalue())
            manifest = output.with_suffix(".json")
            report = json.loads(manifest.read_text())
            result = output.read_bytes()
            self.assertEqual(report["output_sha256"], hashlib.sha256(result).hexdigest())
            self.assertFalse(report["device_tested"])
            self.assertEqual(report["stage"], "features")
            self.assertEqual(sum(r["used_bytes"] for r in report["regions"]), report["native_bytes"])
            self.assertEqual(
                sum(r["free_bytes"] for r in report["regions"]), report["capacity_bytes"] - report["native_bytes"]
            )
            self.assertTrue(report["stack_frame_bytes"])
            self.assertIn("-Oz", report["compiler_arguments"])
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(firmware.main(args), 1)
            self.assertEqual(output.read_bytes(), result)
            self.assertEqual(manifest.read_text(), json.dumps(report, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(ValueError, "not the official"):
                firmware.inspect(result)


if __name__ == "__main__":
    unittest.main()

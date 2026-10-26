"""Compare the size pass with original r3 source from the Git checkpoint.

Only synthetic test state is compared. Firmware is built privately from the
user's official input, never stored in fixtures or sent to hardware.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

import test_native as scenarios

from tools import firmware, native

BASELINE_COMMIT = "6a5c4128c31012464abfb66754a596490e285cfd"
BASELINE_SOURCE = "26735831138fd1af331c4e4b5900fcf494eaaf9ad5726069054e5ce140ab52ef"


@unittest.skipUnless(scenarios.HAS_UNICORN, "native equivalence needs Unicorn")
class NativeEquivalence(unittest.TestCase):
    def test_r3_scenarios_preserve_state_messages_and_stack_bound(self):
        path = Path(
            os.environ.get(
                "FREAKPATCH_STOCK_MFF",
                firmware.ROOT / "original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff",
            )
        )
        if not path.is_file():
            self.skipTest("official input absent; set FREAKPATCH_STOCK_MFF")
        result = subprocess.run(
            ["git", "show", f"{BASELINE_COMMIT}:native/stock_sequencer.c"],
            cwd=firmware.ROOT,
            capture_output=True,
        )
        if result.returncode:
            self.skipTest("equivalence needs the r3 source checkpoint in Git history")
        self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), BASELINE_SOURCE)
        sys.path.insert(0, str(firmware.ROOT / "vendor/ThisFirmwareDoesNotExist/tests"))
        from emu import Emu
        from unicorn import UC_HOOK_CODE

        class Traced(Emu):
            peaks: ClassVar[dict[str, int]] = {}
            messages: ClassVar[list] = []
            symbols: ClassVar[dict[int, str]] = {}

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.low = None

                def track(uc, pc, size, data):
                    if self.low is not None:
                        self.low = min(self.low, self.reg("sp"))

                self.uc.hook_add(UC_HOOK_CODE, track)

            def run(self, start, until, count=200_000):
                # The base constructor runs before instrumentation is installed.
                if not hasattr(self, "low"):
                    return super().run(start, until, count)
                before = self.reg("sp")
                self.low = before
                try:
                    return super().run(start, until, count)
                finally:
                    key = self.symbols.get(start, f"stock:{start:08x}")
                    self.peaks[key] = max(self.peaks.get(key, 0), before - self.low)
                    self.low = None

            def stub(self, address, action=None):
                if address not in (0x080557E8, 0x080558C0, 0x08055E40):
                    return super().stub(address, action)

                def capture(e):
                    if address == 0x080557E8:
                        size = e.reg("r2")
                        value = e.read(e.reg("r1"), size) if size <= 4 else size
                    elif address == 0x080558C0:
                        value = e.reg("r1")
                    else:
                        value = 0
                    self.messages.append((address, value))
                    if action:
                        action(e)

                return super().stub(address, capture)

        def snapshot(e):
            params = []
            for group in range(e.read32(scenarios.PARAMS + 0x24C)):
                size = e.read(0x20000408 + group, 1)[0] * 2
                params.append(e.read(e.read32(scenarios.PARAMS + 0x2C + group * 4), size))
            return (
                e.read(scenarios.SEQ, 0x830),
                e.read(scenarios.MOD, 0x94),
                e.read(scenarios.STATE, 12),
                tuple(params),
                tuple(Traced.messages),
            )

        raw = path.read_bytes()
        stock = firmware.mff.Update.from_bytes(raw)
        stock_payload = firmware.mff.main_payload(stock.read(stock.main_name))

        def exercise(source):
            patch, report = native.build(raw, source=source)
            data = firmware.apply(raw, patch)
            update = firmware.mff.Update.from_bytes(data)
            case_type = type(
                "EquivalenceScenario",
                (scenarios.NativeSequencer,),
                {
                    "emulator": Traced,
                    "native": native,
                    "raw": raw,
                    "stock": stock_payload,
                    "payload": firmware.mff.main_payload(update.read(update.main_name)),
                    "update_bytes": data,
                    "patch": patch,
                    "report": report,
                },
            )
            Traced.symbols = {address: name for name, address in report["symbols"].items()}
            states, stacks = {}, {}
            for method in unittest.defaultTestLoader.getTestCaseNames(case_type):
                Traced.peaks, Traced.messages = {}, []
                case = case_type(method)
                outcome = unittest.TestResult()
                case.run(outcome)
                self.assertEqual(outcome.skipped, [], method)
                self.assertTrue(outcome.wasSuccessful(), outcome.errors + outcome.failures)
                states[method] = snapshot(case.e)
                stacks[method] = dict(Traced.peaks)
            return report, states, stacks

        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "r3.c"
            baseline.write_bytes(result.stdout)
            old_report, old_states, old_stacks = exercise(baseline)
        report, states, stacks = exercise(None)
        self.assertLess(report["native_bytes"], old_report["native_bytes"])
        self.assertEqual(report["runtime_bytes"], old_report["runtime_bytes"])
        self.assertEqual(states.keys(), old_states.keys())
        for method, state in states.items():
            with self.subTest(scenario=method):
                self.assertEqual(state, old_states[method])
                for operation, peak in stacks[method].items():
                    self.assertIn(operation, old_stacks[method])
                    self.assertLessEqual(peak, old_stacks[method][operation], operation)
        summary = {
            "baseline_commit": BASELINE_COMMIT,
            "scenarios": len(states),
            "baseline_native_bytes": old_report["native_bytes"],
            "native_bytes": report["native_bytes"],
            "baseline_max_observed_stack_bytes": max(max(s.values()) for s in old_stacks.values()),
            "max_observed_stack_bytes": max(max(s.values()) for s in stacks.values()),
            "baseline_operation_stack_bytes": old_stacks,
            "operation_stack_bytes": stacks,
        }
        output = firmware.ROOT / "build/r4-equivalence.json"
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

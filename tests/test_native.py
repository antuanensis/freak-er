"""Native ARM adapter plus real stock routines. Peripheral queues are stubbed.

These are emulator tests, never hardware validation. Run with make native-test.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from itertools import pairwise
from pathlib import Path

from tools import firmware

ROOT = Path(__file__).resolve().parents[1]
SEQ, MOD, STATE = 0x20000EEC, 0x20000E30, 0x2001C9D8
PARAMS, UI, PANEL, REQUEST = 0x2001C898, 0x20003704, 0x20010000, 0x20000A14
HAS_UNICORN = importlib.util.find_spec("unicorn") is not None


@unittest.skipUnless(HAS_UNICORN, "native emulation needs make setup and make native-test")
class NativeSequencer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "vendor/ThisFirmwareDoesNotExist/tests"))
        from emu import Emu

        from tools import native

        cls.emulator = Emu
        cls.native = native
        path = Path(
            os.environ.get("FREAKPATCH_STOCK_MFF", ROOT / "original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff")
        )
        if not path.is_file():
            raise unittest.SkipTest("official input absent; set FREAKPATCH_STOCK_MFF")
        cls.raw = path.read_bytes()
        cls.patch, cls.report = native.build(cls.raw)
        cls.update_bytes = firmware.apply(cls.raw, cls.patch)
        update = firmware.mff.Update.from_bytes(cls.update_bytes)
        cls.payload = firmware.mff.main_payload(update.read(update.main_name))
        stock = firmware.mff.Update.from_bytes(cls.raw)
        cls.stock = firmware.mff.main_payload(stock.read(stock.main_name))

    def setUp(self):
        self.e = self.emulator(self.payload)
        self.events = []
        self.e.stub(0x08021414, lambda e: self.events.append(("queue", e.reg("r0"))))
        self.e.stub(0x080558C0, lambda e: self.events.append(("page", e.reg("r1"))))
        self.e.stub(0x08055E40, lambda e: self.events.append(("close",)))
        for pattern in (0, 1):
            self.e.call(0x08027F48, SEQ, pattern)
        self.e.call(0x08028014, SEQ, 64)
        self.e.call(0x08028244, SEQ, 17)
        self.e.call(0x08026320, MOD)
        self.e.write32(MOD, SEQ)
        self.e.write32(0x20003714 + 8, UI)
        self.e.write(UI, bytes([0, 2, 2, 0, 1, 0, 1, 0]))
        self.e.write(0x20003A80, b"\x01")
        self.e.write(0x20003AC4, b"\x03")
        from unicorn import UC_HOOK_MEM_WRITE

        def forbid_flash(uc, access, address, size, value, data):
            self.fail(f"unexpected emulated flash write at {address:#x}")

        self.e.uc.hook_add(UC_HOOK_MEM_WRITE, forbid_flash, begin=0x08000000, end=0x0807FFFF)
        self.e.uc.mem_map(0x40023000, 0x1000)
        self.e.uc.hook_add(UC_HOOK_MEM_WRITE, forbid_flash, begin=0x40023C00, end=0x40023C18)

    def call(self, name, *args):
        return self.e.call(self.report["symbols"][name], *args)

    def editor(self, pattern=0, step=63):
        self.e.write(SEQ + 2, bytes([pattern]))
        self.e.write(STATE + 4, bytes([0x71, step | pattern << 6, 1, 0]))

    def flags(self):
        return self.e.read(STATE + 4, 1)[0] & 15

    def track(self):
        return self.e.read(STATE + 4, 1)[0] >> 4 & 7

    def capture(self, parameter, value, caller=0x0804028B):
        panel = caller == 0x0804028B
        if panel:
            self.e.write(STATE + 4, bytes([self.e.read(STATE + 4, 1)[0] | 8]))
            self.e.write(STATE + 5, bytes([self.e.read(STATE + 5, 1)[0] | 128]))
        self.e.set_regs(r0=PARAMS, r1=parameter, r2=value & 0xFFFFFFFF, r3=1, lr=caller)
        self.e.run(self.report["symbols"]["set_parameter"], caller & ~1)
        if panel:
            self.e.write(STATE + 4, bytes([self.e.read(STATE + 4, 1)[0] & ~8]))
            self.e.write(STATE + 5, bytes([self.e.read(STATE + 5, 1)[0] & 127]))
        return self.e.reg("r0")

    def step_address(self, pattern, step):
        return SEQ + 4 + pattern * 0x412 + step * 16

    def test_boot_uses_only_unused_table_slots_and_keeps_twenty_groups(self):
        self.assertEqual(self.e.read32(PARAMS + 0x24C), 20)
        self.assertEqual(self.e.read32(STATE), 42)
        self.assertEqual(self.e.read(STATE + 6, 1), b"\x01")
        stock = self.emulator(self.stock)
        # The hook preserves all stock constructor output except its 12-byte state.
        self.assertEqual(self.e.read(PARAMS, 0x140), stock.read(PARAMS, 0x140))
        self.assertEqual(self.e.read(PARAMS + 0x14C, 0x1800 - 0x14C), stock.read(PARAMS + 0x14C, 0x1800 - 0x14C))

    def test_probabilities_default_save_load_clear_and_partial_metadata(self):
        for pattern in (0, 1):
            self.editor(pattern)
            self.assertEqual(self.call("probability", SEQ, pattern, 63), 100)
            self.call("set_probability", 25 + pattern * 50)
        buffer = 0x20011000
        self.e.call(0x080284BC, SEQ, buffer, 32)
        saved = self.e.read(buffer + 32, 0x824)
        self.e.call(0x08027F48, SEQ, 0)
        self.e.call(0x08027F48, SEQ, 1)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 100)
        self.e.call(0x080284F0, SEQ, buffer, 32, 0xFFFFFFFF)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 25)
        self.assertEqual(self.call("probability", SEQ, 1, 63), 75)
        self.assertEqual(self.e.read(SEQ + 4, 0x824), saved)
        self.assertEqual(self.e.read(STATE + 4, 1)[0] & 1, 0)
        self.e.write(self.step_address(0, 20) + 15, b"\x00")
        self.assertEqual(self.call("probability", SEQ, 0, 63), 100)
        self.editor(0, 5)
        self.call("set_probability", 0)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 100)
        self.assertEqual(self.call("probability", SEQ, 0, 5), 0)

    def test_empty_legacy_load_and_inline_clear_cannot_resurrect_probabilities(self):
        self.editor()
        self.call("set_probability", 0)
        # Stock also has inlined clears; its empty marker invalidates all tags.
        self.e.write(SEQ + 0x414, b"\xff")
        self.assertEqual(self.call("probability", SEQ, 0, 63), 100)
        self.e.write(STATE + 5, b"\x05")
        self.call("set_probability", 50)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 100)
        self.e.write(0x20011000, bytes([255]) * 0x824)
        self.e.call(0x080284F0, SEQ, 0x20011000, 0, 0xFFFFFFFF)
        self.assertEqual(self.call("probability", SEQ, 0, 5), 100)

    def test_stock_boundary_rolls_once_chords_share_cache_and_edits_do_not_reroll(self):
        self.editor(0, 18)
        self.call("set_probability", 0)
        sequence = self.e.read(SEQ + 4, 0x824)
        expected = (42 * 1664525 + 1013904223) & 0xFFFFFFFF
        self.assertEqual(self.call("boundary", SEQ), 18)
        self.assertEqual(self.e.read32(STATE), expected)
        self.assertEqual(self.e.read(STATE + 6, 1), b"\x00")
        self.call("set_probability", 100)
        self.assertEqual(self.e.read32(STATE), expected)
        self.assertEqual(self.e.read(STATE + 6, 1), b"\x00")
        self.assertEqual(self.e.call(0x0802821C, SEQ), 18)
        self.assertEqual(self.call("boundary", SEQ), 19)
        self.assertEqual(self.e.read(STATE + 6, 1), b"\x01")
        # Only the edited probability changed, never note or modulation bytes.
        after = self.e.read(SEQ + 4, 0x824)
        differences = [i for i, (a, b) in enumerate(zip(sequence, after, strict=True)) if a != b]
        self.assertEqual(differences, [18 * 16 + 14])

    def test_intermediate_probability_follows_reference_grid_across_both_patterns(self):
        random = 42
        for pattern in (0, 1):
            self.editor(pattern, 0)
            self.call("set_probability", 37)
            for step in range(64):
                self.e.write(self.step_address(pattern, step) + 14, b"\x25")
            for _ in range(128):
                self.call("boundary", SEQ)
                random = (random * 1664525 + 1013904223) & 0xFFFFFFFF
                self.assertEqual(self.e.read32(STATE), random)
                self.assertEqual(self.e.read(STATE + 6, 1)[0], int((random >> 16) * 100 < 37 * 65536))

    def test_note_gate_forwards_all_six_arguments_and_preserves_releases_other_sources(self):
        calls = []

        def original(e):
            calls.append([e.reg("r" + str(i)) for i in range(4)] + [e.read32(e.reg("sp")), e.read32(e.reg("sp") + 4)])
            e.set_regs(r0=73)

        self.e.stub(self.report["symbols"]["original_note"], original)
        self.e.write(STATE + 6, b"\x00")
        for source, message, forwarded in [
            (5, 0x643C90, False),
            (5, 0x643C80, True),
            (5, 0x003C90, True),
            (4, 0x643C90, True),
            (0, 0x643C90, True),
        ]:
            before = len(calls)
            stack = self.e.reg("sp")
            self.e.write32(stack, 123)
            self.e.write32(stack + 4, 456)
            result = self.e.call(0x08048524, 0x20003778, message, source, 2)
            self.assertEqual(len(calls) - before, int(forwarded))
            self.assertEqual(result, 73 if forwarded else 1)
            self.assertEqual(self.e.reg("sp"), stack)
            if forwarded:
                self.assertEqual(calls[-1], [0x20003778, message, source, 2, 123, 456])
        self.e.write(0x20003A80, b"\x00")
        self.assertEqual(self.e.call(0x08048524, 0, 0x643C90, 5, 0), 73)
        self.e.write(0x20003A80, b"\x01")
        self.e.write(0x20003AC4, b"\x01")
        self.assertEqual(self.e.call(0x08048524, 0, 0x643C90, 5, 0), 73)

    def test_future_edit_uses_real_recorder_signed_conversion_and_four_track_limit(self):
        self.editor()
        before_notes = [self.e.read(self.step_address(0, i), 8) for i in range(64)]
        initial = self.e.read32(STATE)
        for track, (pid, value, encoded) in enumerate(
            [(0x101, 12345, 96), (0xA00, -32768, 128), (0xD01, 32767, 127), (0x102, 24576, 192)]
        ):
            self.e.set_param(pid, 2000)
            self.assertEqual(self.capture(pid, value), 3)
            self.assertEqual(self.e.param(pid), 2000)
            self.assertEqual(self.e.call(0x08027FB4, SEQ, track), pid)
            self.assertEqual(self.e.call(0x08028074, SEQ, 63, track), encoded)
            self.assertEqual(self.e.call(0x08028090, SEQ, 63, track), 1)
            shift = 8 if 0xA00 <= pid <= 0x1005 else 7
            self.assertEqual(self.e.call(0x08028074, SEQ, 17, track), 2000 >> shift)
        bank = self.e.read(SEQ + 4, 0x824)
        self.assertEqual(self.capture(0x601, 8000), 3)
        self.assertEqual(self.track(), 4)
        self.assertEqual(self.e.read(SEQ + 4, 0x824), bank)
        self.assertEqual(self.e.call(0x0802821C, SEQ), 17)
        self.assertEqual(self.e.read32(STATE), initial)
        self.assertEqual([self.e.read(self.step_address(0, i), 8) for i in range(64)], before_notes)

    def test_edit_existing_track_current_step_and_incoming_controls(self):
        self.editor(1, 63)
        self.assertEqual(self.capture(0xA00, -16384), 3)
        self.assertEqual(self.capture(0xA00, -8192), 3)
        self.assertEqual(self.e.call(0x08027FB4, SEQ, 1), 0xFFFF)
        self.e.call(0x08028244, SEQ, 63)
        sends = []
        self.e.stub(0x0802682C, lambda e: sends.append((e.reg("r1"), e.reg("r2"))))
        self.assertEqual(self.capture(0xA00, -24576), 3)
        self.assertEqual(sends, [(0xA00, 0xFFFFA000)])
        self.assertEqual(self.e.call(0x08028074, SEQ, 63, 0), 160)
        bank = self.e.read(SEQ + 4, 0x824)
        self.capture(0x101, 12345, caller=0x08047901)
        self.assertEqual(self.e.param(0x101), 12345)
        self.assertEqual(self.e.read(SEQ + 4, 0x824), bank)
        # A non-recordable panel parameter also keeps stock behavior.
        self.capture(0x600, 8000)
        self.assertEqual(self.e.param(0x600), 8000)

    def test_new_cutoff_and_resonance_tracks_restore_baseline_after_selected_step(self):
        for pattern in (0, 1):
            self.setUp()
            self.editor(pattern, 3)
            self.call("set_probability", 37)
            notes = [self.e.read(self.step_address(pattern, i), 8) for i in range(64)]
            metadata = [self.e.read(self.step_address(pattern, i) + 14, 2) for i in range(64)]
            other = self.e.read(SEQ + 4 + (1 - pattern) * 0x412, 0x412)
            self.e.write(0x200007EA, b"\x01")
            self.e.write(PANEL + 0x28, b"\x01")
            self.e.stub(0x08047DF8)
            self.e.stub(0x08047FC4)
            handler = self.e.read32(0x08074C54) & ~1
            for track, (pid, base, edited) in enumerate(((0x101, 10000, 24000), (0x102, 8000, 16000))):
                self.e.set_param(pid, base)
                self.e.call(handler, PANEL, pid, edited, 0)
                self.assertEqual(self.e.param(pid), base)
                for step in range(64):
                    self.assertEqual(self.e.call(0x08028090, SEQ, step, track), 1)
                    expected = edited if step == 3 else base
                    self.assertEqual(self.e.call(0x08028074, SEQ, step, track), expected >> 7)
            self.e.write32(MOD + 4, 0x20013000)
            self.e.write32(MOD + 8, 0x20013200)
            phase = [0]
            self.e.stub(0x0802B024, lambda e, phase=phase: e.set_regs(r0=phase[0]))
            self.e.stub(0x0802B02C, lambda e: e.set_regs(r0=1000))
            self.e.stub(0x08027B9C, lambda e: e.set_regs(r0=0))
            self.e.stub(0x08027B5C, lambda e: e.set_regs(r0=1000))
            for step in (*range(64), 0):
                self.e.call(0x08028244, SEQ, step)
                phase[0] = 0
                self.e.call(0x08027448, MOD)
                self.e.call(0x080269EC, MOD)
                phase[0] = 1000
                self.e.call(0x080269EC, MOD)
                # Untouched stock applies this fixture's lock on its own step.
                # Following steps must return to baseline instead of holding.
                self.assertEqual(self.e.param(0x101), (24000 if step == 3 else 10000) >> 7 << 7)
                self.assertEqual(self.e.param(0x102), (16000 if step == 3 else 8000) >> 7 << 7)
            self.assertEqual([self.e.read(self.step_address(pattern, i), 8) for i in range(64)], notes)
            self.assertEqual([self.e.read(self.step_address(pattern, i) + 14, 2) for i in range(64)], metadata)
            self.assertEqual(self.e.read(SEQ + 4 + (1 - pattern) * 0x412, 0x412), other)

    def test_editing_existing_sparse_track_does_not_replace_its_other_snapshots(self):
        self.editor(0, 3)
        self.capture(0x101, 24000)
        self.e.call(0x08028104, SEQ, 0, 0, 71)
        self.e.call(0x08028128, SEQ, 1, 0, 0)
        # A recorder cache need not have been initialized for a loaded track.
        self.e.write16(MOD + 0x18, 0xFFFF)
        before = self.e.read(SEQ + 4, 0x400)
        self.capture(0x101, 16000)
        after = self.e.read(SEQ + 4, 0x400)
        for step in range(64):
            if step != 3:
                self.assertEqual(after[step * 16 : (step + 1) * 16], before[step * 16 : (step + 1) * 16])

    def test_stock_position_getter_remains_unhooked_and_preserves_signed_sentinel(self):
        self.editor()
        for flags, caller, expected in [(1, 0x08026F3B, 17), (3, 0x08026F3B, 17), (3, 0x08030001, 17)]:
            self.e.write(STATE + 4, bytes([flags]))
            self.e.set_regs(r0=SEQ, lr=caller)
            self.e.run(0x0802821C, caller & ~1)
            self.assertEqual(self.e.reg("r0"), expected)
            self.assertEqual(self.e.read(SEQ + 0x828, 1), b"\x11")
        self.e.call(0x08028244, SEQ, 255)
        self.assertEqual(self.e.call(0x0802821C, SEQ), 0xFFFFFFFF)

    def test_stock_copy_single_pattern_reload_and_builtin_reset(self):
        self.editor(0, 63)
        self.call("set_probability", 12)
        self.e.call(0x0802824C, SEQ, 1, 0)
        self.assertEqual(self.call("probability", SEQ, 1, 63), 12)
        self.editor(1, 63)
        self.call("set_probability", 87)
        self.e.call(0x080284BC, SEQ, 0x20011000, 0)
        self.editor(0, 63)
        self.call("set_probability", 55)
        self.e.call(0x080284F0, SEQ, 0x20011000, 0, 0)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 12)
        self.assertEqual(self.call("probability", SEQ, 1, 63), 87)
        self.e.write(SEQ + 1, b"\x01")  # Stock chromatic built-in pattern.
        self.e.call(0x08028264, SEQ)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 100)
        self.assertEqual(self.call("probability", SEQ, 1, 63), 87)

    def test_real_playback_keeps_locks_at_zero_probability_and_current_edit_persists(self):
        self.editor(0, 63)
        self.e.set_param(0x101, 10000)
        self.capture(0x101, 24000)
        self.assertEqual(self.e.param(0x101), 10000)
        self.e.write32(MOD + 4, 0x20013000)
        self.e.write32(MOD + 8, 0x20013200)
        phase = [0]
        self.e.stub(0x0802B024, lambda e: e.set_regs(r0=phase[0]))
        self.e.stub(0x0802B02C, lambda e: e.set_regs(r0=1000))
        self.e.stub(0x08027B9C, lambda e: e.set_regs(r0=0))
        self.e.stub(0x08027B5C, lambda e: e.set_regs(r0=1000))
        self.e.stub(0x08047DF8)
        self.e.stub(0x08047FC4)
        self.editor(0, 63)
        self.call("set_probability", 0)
        self.e.call(0x08028244, SEQ, 62)
        self.call("boundary", SEQ)
        self.assertEqual(self.e.read(STATE + 6, 1), b"\x00")
        self.e.call(0x08027448, MOD)
        for time, value in [(250, 23936), (500, 23936), (1000, 23936)]:
            phase[0] = time
            self.e.call(0x080269EC, MOD)
            self.assertEqual(self.e.param(0x101), value)
        self.assertEqual(self.capture(0x101, 12345), 3)
        self.assertEqual(self.e.param(0x101), 12345)
        for time in (1100, 1200, 1500):
            phase[0] = time
            self.e.call(0x080269EC, MOD)
            self.assertEqual(self.e.param(0x101), 12345)  # Stock leaves this unsmoothed value until the next event.

    def test_real_driver_chords_ties_and_releases_at_zero_and_full_probability(self):
        driver, engine = 0x20003AC8, 0x20003AA8
        self.e.write32(engine, UI)
        self.e.write32(engine + 8, SEQ)
        self.e.write32(engine + 12, 0x20012000)
        self.e.write32(engine + 16, MOD)
        self.e.call(0x08028EB8, engine, 0x20003778, 0x08023B85)
        self.e.call(0x080292A0, driver, engine, 0x20003778)
        notes = []

        def note(e):
            notes.append((e.reg("r1"), e.reg("r2")))
            e.set_regs(r0=1)

        self.e.stub(self.report["symbols"]["original_note"], note)
        self.e.stub(0x080496A4)
        self.e.stub(0x0804DE48)
        for step, tied, p, expected in [
            (0, False, 100, 3),
            (1, True, 0, 0),
            (2, False, 0, 0),
            (3, True, 100, 0),
            (4, False, 100, 3),
        ]:
            self.editor(0, step)
            self.call("set_probability", p)
            pitches = [188, 192, 195, 255] if tied else [60, 64, 67, 255]
            self.e.write(self.step_address(0, step), bytes([*pitches, 100, 100, 100, 0]))
            self.e.write(self.step_address(0, step) + 12, bytes([2 if tied else 1]))
            self.e.call(0x08028244, SEQ, (step - 1) % 64)
            self.call("boundary", SEQ)
            notes.clear()
            self.e.call(0x08029398, driver)
            self.assertEqual(sum(message & 0xF0 == 0x90 for message, _ in notes), expected)
            self.assertTrue(all(source == 5 for _, source in notes))

    def test_actual_stock_boundary_hook_and_arp_exclusion(self):
        engine = 0x20003AA8
        self.e.write32(engine, UI)
        self.e.write32(engine + 8, SEQ)
        self.e.write32(engine + 12, 0x20012000)
        for advance, expected in [(0, 17), (1, 18), (1, 19), (0, 19)]:
            random = self.e.read32(STATE)
            self.e.call(0x080290DC, engine, advance)
            self.assertEqual(self.e.call(0x0802821C, SEQ), expected)
            self.assertEqual(self.e.read32(STATE) != random, bool(advance))
        self.e.write(engine + 28, b"\x01")
        random = self.e.read32(STATE)
        self.e.write32(engine + 4, 0x20013000)
        self.e.call(0x080290DC, engine, 1)
        self.assertEqual(self.e.read32(STATE), random)
        # Stock also advances this shared cursor in arp mode. Preserve that
        # behavior while leaving the extension's PRNG untouched.
        self.assertEqual(self.e.call(0x0802821C, SEQ), 20)

    def test_real_transport_start_continue_stop_and_main_loop_editor_close(self):
        engine, driver, clock, transport = 0x20003AA8, 0x20003AC8, 0x20000EC4, 0x20003A64
        self.e.write32(engine, UI)
        self.e.write32(engine + 8, SEQ)
        self.e.write32(engine + 12, 0x20012000)
        self.e.write32(engine + 16, MOD)
        self.e.call(0x08028EB8, engine, 0x20003778, 0x08023B85)
        self.e.call(0x080292A0, driver, engine, 0x20003778)
        self.e.call(0x0802776C, clock, driver, engine)
        self.e.call(0x08028798, transport)
        self.e.write32(transport, clock)
        self.e.write32(transport + 4, driver)
        self.e.write32(transport + 32, 0x0802B8ED)  # Neutral transport observer.
        self.e.write32(0x2001E8D0, 0x20014000)  # Synthetic timer registers, not FLASH.
        self.e.stub(self.report["symbols"]["original_note"], lambda e: e.set_regs(r0=1))
        self.e.stub(0x080496A4)
        self.e.stub(0x0804DE48)
        self.e.stub(0x08039DA4, lambda e: e.set_regs(r0=7))
        first_draw = (42 * 1664525 + 1013904223) & 0xFFFFFFFF
        self.e.call(0x0802880C, transport, 1)
        self.assertEqual(self.e.call(0x0802821C, SEQ), 0)
        self.assertEqual(self.e.read32(STATE), first_draw)
        self.e.call(0x080290DC, engine, 1)
        second_draw = self.e.read32(STATE)
        self.editor(0, 1)
        self.e.call(0x0802880C, transport, 0)
        self.assertEqual(self.e.read(transport + 28, 1), b"\x00")
        self.assertEqual(self.flags(), 1)
        self.assertEqual(self.call("poll", 0x20003714), 7)
        self.assertEqual(self.flags(), 0)
        self.e.call(0x0802880C, transport, 3)
        self.assertEqual(self.e.read32(STATE), second_draw)
        self.assertEqual(self.e.call(0x0802821C, SEQ), 1)
        self.e.call(0x0802880C, transport, 2)
        self.e.call(0x0802880C, transport, 4)
        self.assertEqual(self.e.read32(STATE), first_draw)
        self.assertEqual(self.e.call(0x0802821C, SEQ), 0)
        self.e.call(0x0802880C, transport, 5)
        self.assertEqual(self.e.read32(STATE), first_draw)
        self.editor(0, 0)
        self.e.call(0x0802880C, transport, 0)
        self.e.call(0x0802880C, transport, 1)
        self.assertEqual(self.e.read(transport + 28, 1), b"\x01")
        self.call("poll", 0x20003714)
        self.assertEqual(self.flags(), 0)

    def test_normal_stock_note_and_modulation_accessors_preserve_step_metadata(self):
        for pattern in (0, 1):
            self.editor(pattern, 0)
            self.call("set_probability", 37)
            before = [self.e.read(self.step_address(pattern, i) + 14, 2) for i in range(64)]
            source = 0x20015000
            self.e.write(source, bytes([60, 64, 67, 255, 80, 80, 80, 0, 0, 0, 0, 0, 1, 0, 99, 88]))
            for step in range(64):
                self.e.call(0x08028170, SEQ, step, source)
                self.e.call(0x08028104, SEQ, step, step % 4, step + 100)
                self.e.call(0x08028128, SEQ, step, step % 4, 1)
                for function in (0x08028020, 0x08028044, 0x08028060, 0x08028074, 0x08028090):
                    self.e.call(function, SEQ, step, 0)
            self.assertEqual([self.e.read(self.step_address(pattern, i) + 14, 2) for i in range(64)], before)

    def test_real_pot_vtable_path_and_outside_editor_passthrough(self):
        self.editor()
        self.e.write(0x200007EA, b"\x01")
        self.e.write(PANEL + 0x28, b"\x01")  # Stock Local Control.
        self.e.stub(0x08047DF8)
        self.e.stub(0x08047FC4)
        handler = self.e.read32(0x08074C54)
        self.e.call(handler & ~1, PANEL, 0x101, 24576, 0)
        self.assertEqual(self.e.param(0x101), 0)
        self.assertEqual(self.e.call(0x08028074, SEQ, 63, 0), 192)
        self.assertEqual(self.flags(), 1)
        self.e.write(STATE + 4, b"\x00")
        bank = self.e.read(SEQ + 4, 0x824)
        self.e.call(handler & ~1, PANEL, 0x101, 12345, 0)
        self.assertEqual(self.e.param(0x101), 12345)
        self.assertEqual(self.e.read(SEQ + 4, 0x824), bank)

    def test_real_lfo_and_matrix_encoder_routes_capture_stock_destinations(self):
        self.editor()
        self.e.write(0x200007EA, b"\x01")
        self.e.write(PANEL + 0x28, b"\x01")
        self.e.stub(0x08047DF8)
        self.e.stub(0x08047FC4)
        handler = self.e.read32(0x08074C70) & ~1
        self.e.call(handler, PANEL, 0x502, 1, 0)
        self.assertEqual(self.e.read16(STATE + 8), 0x502)
        self.assertEqual(self.track(), 0)
        # Full boot normally installs the matrix screen object and amount mode.
        self.e.write32(0x200035A4, UI)
        self.e.write(0x200035A8, b"\x01")
        self.e.write(UI, b"\x02")
        self.e.call(handler, PANEL, 0x900, 1, 0)
        self.assertEqual(self.e.read16(STATE + 8), 0xA00)
        self.assertEqual(self.track(), 1)
        record = self.step_address(0, 63)
        self.assertEqual(self.e.read(record + 13, 1)[0] & 3, 3)

    def test_relative_encoder_accumulates_fine_edits_from_selected_snapshot(self):
        self.editor()
        self.e.set_param(0x101, 10000)
        self.capture(0x101, 24000)
        self.e.write(0x200007EA, b"\x01")
        self.e.write(PANEL + 0x28, b"\x01")
        # The normal oscillator-control lookup is installed during full boot.
        # Reuse its official three-control list for this isolated panel fixture.
        self.e.write32(0x200009F0, 0x080737A0)
        self.e.stub(0x08047DF8)
        self.e.stub(0x08047FC4)
        handler = self.e.read32(0x08074C70) & ~1
        for turn in range(1, 6):
            self.e.call(handler, PANEL, 0x101, 1, 0)
            self.assertEqual(self.e.read16(STATE + 10), 24000 + turn * 32)
            self.assertEqual(self.e.param(0x101), 10000)
        self.assertEqual(self.e.call(0x08028074, SEQ, 63, 0), 188)
        # Moving the edit cursor invalidates the fine-resolution cache.
        self.e.write(PANEL + 0x28, b"\x00")
        self.e.call(handler, PANEL, 0x403, -1 & 0xFFFF, 0)
        self.assertEqual(self.e.read(STATE + 4, 1)[0] & 128, 0)

    def test_discrete_type_encoder_accumulates_while_model_context_stays_global(self):
        self.editor()
        self.e.write(0x200007EA, b"\x01")
        self.e.write(PANEL + 0x28, b"\x01")
        self.e.write32(0x200009F0, 0x080737A0)
        self.e.set_param(0, 0)
        self.e.stub(0x08047DF8)
        self.e.stub(0x08047FC4)
        handler = self.e.read32(0x08074C70) & ~1
        for expected in (1489, 2979, 4468, 5958, 7447):
            self.e.call(handler, PANEL, 0, 1, 0)
            self.assertEqual(self.e.read16(STATE + 10), expected)
            self.assertEqual(self.e.param(0), 0)
            self.assertEqual(self.e.call(0x08027FB4, SEQ, 0), 0)
        # Wave's model lookup must still see the actual active model, rather
        # than a future Type lock whose engine/assets are not active now.
        self.e.write(STATE + 4, bytes([self.e.read(STATE + 4, 1)[0] | 8]))
        self.e.set_regs(r0=PARAMS, r1=0)
        self.e.run(0x08040B9E, 0x08040BA2)
        self.assertEqual(self.e.reg("r0"), 0)
        self.assertEqual(self.e.param(0), 0)

    def test_inline_encoder_read_preserves_registers_comparison_flags_and_signedness(self):
        from unicorn import arm_const as arm

        self.e.set_param(0xA00, 0x8000)
        for i in range(13):
            self.e.set_regs(**{"r" + str(i): 0x1200 + i})
        self.e.set_regs(r8=PARAMS, r9=0, r10=PARAMS + 10 * 4, lr=0x12345678)
        self.e.uc.reg_write(arm.UC_ARM_REG_APSR, 0xF80F0000)
        flags = self.e.uc.reg_read(arm.UC_ARM_REG_APSR)
        before = self.e.regs()
        self.e.run(self.report["symbols"]["encoder_value"], 0x0802C484)
        after = self.e.regs()
        self.assertEqual(after.pop("r6"), 0xFFFF8000)
        before.pop("r6")
        self.assertEqual(after, before)
        self.assertEqual(self.e.uc.reg_read(arm.UC_ARM_REG_APSR), flags)

    def test_selected_raw_getter_excludes_recorder_midi_and_unscoped_reads(self):
        self.editor()
        self.e.set_param(0xA00, 2000)
        self.capture(0xA00, -8191)
        self.e.write(STATE + 4, bytes([self.e.read(STATE + 4, 1)[0] | 8]))
        for caller, expected in [(0x08042CF1, 0xE001), (0x08026F01, 2000), (0x08047901, 2000)]:
            self.e.set_regs(r0=PARAMS, r1=0xA00, lr=caller)
            self.e.run(0x08023C2C, caller & ~1)
            self.assertEqual(self.e.reg("r0"), expected)
        self.e.write(STATE + 4, bytes([self.e.read(STATE + 4, 1)[0] & ~8]))
        self.assertEqual(self.e.call(0x08023C2C, PARAMS, 0xA00), 2000)

    def test_placement_and_passthrough_stages_have_no_feature_behavior(self):
        placement, _ = self.native.build(self.raw, stage="placement")
        self.assertEqual(placement.hooks, ())
        self.assertEqual(len(placement.edits), 8)
        passthrough, report = self.native.build(self.raw, stage="passthrough")
        data = firmware.apply(self.raw, passthrough)
        update = firmware.mff.Update.from_bytes(data)
        e = self.emulator(firmware.mff.main_payload(update.read(update.main_name)))
        e.call(0x08027F48, SEQ, 0)
        e.call(0x08028014, SEQ, 64)
        e.call(0x08028244, SEQ, 17)
        random = e.read32(STATE)
        self.assertEqual(e.call(report["symbols"]["boundary"], SEQ), 18)
        self.assertEqual(e.read32(STATE), random)
        e.write(0x200007EA, b"\x01")
        e.stub(0x08047DF8)
        e.stub(0x08047FC4)
        e.call(e.read32(0x08074C54) & ~1, PANEL, 0x101, 12345, 0)
        self.assertEqual(e.param(0x101), 12345)
        self.assertFalse(any(h.symbol == "popup" for h in passthrough.hooks))

    def test_shift_record_release_order_rate_probability_and_recording_exclusion(self):
        original = []
        self.e.stub(0x08043224, lambda e: original.append((e.reg("r1"), e.reg("r2"))))
        self.e.write(PANEL + 0x28, b"\x01")
        self.call("press", PANEL, 0x1103, 0)
        self.assertEqual(self.flags(), 5)
        self.assertEqual(original, [])
        self.e.write(PANEL + 0x28, b"\x00")
        self.call("release", PANEL, 0x804, 0)
        self.call("release", PANEL, 0x1103, 0)
        self.assertEqual(original, [(0, 0x804)])
        self.assertEqual(self.flags(), 1)
        self.e.call(self.e.read32(0x08074C70) & ~1, PANEL, 0x403, 46, 0)
        self.assertEqual(self.e.read(STATE + 5, 1), b"\x3f")
        self.assertEqual(self.e.call(0x0802821C, SEQ), 17)
        self.e.write(PANEL + 0x28, b"\x01")
        self.call("encoder", PANEL, 0x402, (-200) & 0xFFFF, 0)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 0)
        self.call("encoder", PANEL, 0x402, 200, 0)
        self.assertEqual(self.call("probability", SEQ, 0, 63), 100)
        self.call("press", PANEL, 0x405, 0)
        self.assertEqual(self.e.read(STATE + 4, 1)[0] & 1, 0)
        self.assertEqual(original[-1], (1, 0x405))
        for submode in (0, 1, 3, 4, 6):
            self.e.write(UI + 1, bytes([submode]))
            self.call("press", PANEL, 0x1103, 0)
            self.assertEqual(self.e.read(STATE + 4, 1)[0] & 1, 0)
            self.assertEqual(original[-1], (1, 0x1103))

    def test_oled_uses_stock_page_and_four_byte_text_messages(self):
        self.editor()
        self.capture(0x101, 12345)
        chunks, commands = [], []

        def text(e):
            size = e.reg("r2")
            if size != 0x7F:
                self.assertLessEqual(size, 4)
                chunks.append(e.read(e.reg("r1"), size))

        self.e.stub(0x080557E8, text)
        self.e.stub(0x0805579C, lambda e: commands.append((e.reg("r1"), e.reg("r2"))))
        self.call("draw_editor")
        output = b"".join(chunks)
        self.assertTrue(output.startswith(b"A E64/64 N-\n%100 T1\n"), output)
        self.assertNotIn(b" P18", output)
        self.assertIn(b"96", output)
        self.assertEqual(output[-1], 0)
        self.assertEqual(commands, [(0x12, 0x02001A00)])

    def test_oled_numbers_cover_all_snapshot_values_without_leading_zeroes(self):
        address = 0x20015000
        for value in range(256):
            end = self.call("number", address, value)
            self.assertEqual(self.e.read(address, end - address), str(value).encode())

    def test_all_57_destinations_match_stock_recorder_conversion_baseline_and_led(self):
        stock = self.emulator(self.stock)
        stock.stub(0x08021414)
        stock.stub(0x0802682C)
        eligible = []
        for group in range(self.e.read32(PARAMS + 0x24C)):
            flags = self.e.read32(PARAMS + 0x8C + group * 4)
            for index in range(self.e.read(0x20000408 + group, 1)[0]):
                if self.e.read(flags + index * 2 + 1, 1)[0] & 0x40:
                    eligible.append(group * 256 + index)
        self.assertEqual(len(eligible), 57)
        for pid in eligible:
            with self.subTest(parameter=hex(pid)):
                self.setUp()
                self.editor(1, 63)
                for pattern in (0, 1):
                    stock.call(0x08027F48, SEQ, pattern)
                stock.write(SEQ + 2, b"\x01")
                stock.call(0x08028014, SEQ, 64)
                stock.call(0x08028244, SEQ, 63)
                stock.call(0x08026320, MOD)
                stock.write32(MOD, SEQ)
                stock.write(MOD + 0x88, b"\xff")
                stock.write(MOD + 0x90, b"\x01")
                base = 0xC000 if 0xA00 <= pid <= 0x1005 else 10000
                value = 0xFFFFA000 if 0xA00 <= pid <= 0x1005 else 24000
                self.e.set_param(pid, base)
                stock.set_param(pid, base)
                stock.call(0x08026DB8, MOD, pid, value, 0)
                self.assertEqual(self.capture(pid, value), 3)
                self.assertEqual(self.e.call(0x08027FB4, SEQ, 0), stock.call(0x08027FB4, SEQ, 0))
                self.assertEqual(self.e.call(0x08028074, SEQ, 63, 0), stock.call(0x08028074, SEQ, 63, 0))
                self.assertEqual(self.e.read(MOD + 0x28, 4), stock.read(MOD + 0x28, 4))
                self.assertEqual(self.e.read(MOD + 0x48, 48), stock.read(MOD + 0x48, 48))

    def test_global_knob_scales_existing_curve_and_preserves_empty_steps(self):
        self.editor(0, 0)
        self.capture(0x101, 12800)
        self.editor(0, 1)
        self.capture(0x101, 25600)
        self.editor(0, 2)
        self.capture(0x101, 6400)
        self.e.call(0x08028128, SEQ, 3, 0, 0)
        self.editor(0, 0)
        other = self.e.read(SEQ + 4 + 0x412, 0x412)
        self.e.write(0x200007EA, b"\x01")
        self.e.stub(0x08047DF8)
        self.e.stub(0x08047FC4)
        self.call("pot", PANEL, 0x101, 6400, 0)
        self.assertEqual([self.e.call(0x08028074, SEQ, i, 0) for i in range(3)], [50, 100, 25])
        self.assertEqual(self.e.call(0x08028090, SEQ, 3, 0), 0)
        self.assertEqual(self.e.read(SEQ + 4 + 0x412, 0x412), other)
        self.assertEqual(self.e.call(0x0802821C, SEQ), 17)

    def test_global_signed_scaling_and_zero_reference_remain_bounded(self):
        self.editor(0, 0)
        self.capture(0xA00, -16384)
        self.editor(0, 1)
        self.capture(0xA00, 8192)
        self.editor(0, 0)
        self.e.write(STATE + 4, bytes([self.e.read(STATE + 4, 1)[0] | 8]))
        self.call("set_parameter", PARAMS, 0xA00, 0xE000, 1)
        self.assertEqual([self.e.call(0x08028074, SEQ, i, 0) for i in range(2)], [224, 16])
        self.e.call(0x08028104, SEQ, 0, 0, 0)
        self.call("set_parameter", PARAMS, 0xA00, 0x7F00, 1)
        self.assertEqual([self.e.call(0x08028074, SEQ, i, 0) for i in range(2)], [127, 127])

    def test_shift_rise_edits_time_and_preserves_stock_alternate_outside_editor(self):
        self.editor()
        self.e.write(0x200007EA, b"\x01")
        self.e.write(PANEL + 0x28, b"\x01")
        self.e.stub(0x08047DF8)
        self.e.stub(0x08047FC4)
        self.call("pot", PANEL, 0x201, 16000, 0)
        self.assertEqual(self.e.call(0x08027FB4, SEQ, 0), 0x201)
        self.assertEqual(self.e.read(PANEL + 0x28, 1), b"\x01")
        self.call("close_editor")
        self.call("pot", PANEL, 0x201, 10000, 0)
        self.assertEqual(self.e.param(0x202), 10000)

    def test_oct_tap_selects_and_hold_erases_one_lock_at_threshold_and_wrap(self):
        self.editor(1, 63)
        self.capture(0x101, 24000)
        self.capture(0x102, 16000)
        self.e.stub(0x08039DA4, lambda e: e.set_regs(r0=7))
        for start in (1000, 32700):
            self.capture(0x101, 24000)
            self.e.write32(0x2001E1D8, start)
            self.call("press", PANEL, 0x401, 0)
            self.e.write32(0x2001E1D8, start + 599)
            self.call("poll", 0x20003714)
            self.assertEqual(self.e.call(0x08028090, SEQ, 63, 0), 1)
            self.e.write32(0x2001E1D8, start + 600)
            self.call("poll", 0x20003714)
            self.assertEqual(self.e.call(0x08028090, SEQ, 63, 0), 0)
            self.assertEqual(self.e.call(0x08028090, SEQ, 63, 1), 1)
            self.call("release", PANEL, 0x401, 0)
            self.assertEqual(self.track(), 0)
        self.call("press", PANEL, 0x401, 0)
        self.call("release", PANEL, 0x401, 0)
        self.assertEqual(self.track(), 1)

    def test_shift_hold_cleans_step_locks_and_probability_only(self):
        for pattern in (0, 1):
            self.editor(pattern, 63)
            self.capture(0x101, 24000)
            self.capture(0x102, 16000)
            self.call("set_probability", 13)
            before = self.e.read(SEQ + 4, 0x824)
            self.e.write(PANEL + 0x28, b"\x01")
            self.call("press", PANEL, 0x1105, 0)
            self.call("release", PANEL, 0x1105, 0)
            self.assertEqual(self.call("probability", SEQ, pattern, 63), 100)
            self.assertEqual(self.e.read(self.step_address(pattern, 63) + 13, 1)[0] & 15, 0)
            after = self.e.read(SEQ + 4, 0x824)
            allowed = {pattern * 0x412 + 63 * 16 + i for i in (13, 14)}
            self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(before, after, strict=True))))

    def test_record_rate_release_copies_locks_without_notes_or_probability(self):
        for pattern in (0, 1):
            self.editor(pattern, 0)
            self.capture(0x101, 24000)
            self.capture(0x102, 16000)
            self.e.call(0x08028128, SEQ, 0, 1, 0)
            self.call("set_probability", 13)
            self.e.write(self.step_address(pattern, 63), bytes([60, 64, 67, 255, 80, 90, 100, 0]))
            notes = self.e.read(self.step_address(pattern, 63), 8)
            self.e.write(PANEL + 0x28, b"\x00")
            self.call("press", PANEL, 0x1103, 0)
            self.call("encoder", PANEL, 0x403, 63, 0)
            self.call("release", PANEL, 0x1103, 0)
            self.assertEqual(
                self.e.read(self.step_address(pattern, 63) + 8, 4), self.e.read(self.step_address(pattern, 0) + 8, 4)
            )
            self.assertEqual(self.e.read(self.step_address(pattern, 63) + 13, 1)[0] & 15, 1)
            self.assertEqual(self.e.read(self.step_address(pattern, 63), 8), notes)
            self.assertEqual(self.call("probability", SEQ, pattern, 63), 100)
            self.assertEqual(self.e.call(0x0802821C, SEQ), 17)

    def test_live_pitch_changes_first_note_only_preserving_flags_velocity_and_transport(self):
        self.editor(1, 63)
        address = self.step_address(1, 63)
        self.e.write(address, bytes([60 | 128, 64, 67, 255, 80, 90, 100, 0]))
        original = self.e.read(address, 16)
        random = self.e.read32(STATE)
        self.call("encoder", PANEL, 0x800, 2, 0)
        self.assertEqual(self.e.read(address, 1), bytes([62 | 128]))
        self.assertEqual(self.e.read(address + 1, 15), original[1:])
        self.call("encoder", PANEL, 0x800, 200, 0)
        self.assertEqual(self.e.read(address, 1), b"\xfe")
        self.call("encoder", PANEL, 0x800, (-300) & 0xFFFF, 0)
        self.assertEqual(self.e.read(address, 1), b"\x80")
        self.assertEqual(self.e.call(0x0802821C, SEQ), 17)
        self.assertEqual(self.e.read32(STATE), random)
        self.e.write(address, b"\xff")
        rest = self.e.read(address, 16)
        self.call("encoder", PANEL, 0x800, 1, 0)
        self.assertEqual(self.e.read(address, 16), rest)

    def test_native_playback_matches_untouched_stock_with_identical_ram_and_steps(self):
        for pattern in (0, 1):
            self.setUp()
            self.editor(pattern, 63)
            self.e.set_param(0x101, 10000)
            self.capture(0x101, 24000)
            self.e.write32(MOD + 4, 0x20013000)
            self.e.write32(MOD + 8, 0x20013200)
            reference = self.emulator(self.stock)
            reference.write(0x20000000, self.e.read(0x20000000, 0x20000))
            phase = [0]
            for e in (self.e, reference):
                e.stub(0x08021414)
                e.stub(0x08047DF8)
                e.stub(0x08047FC4)
                e.stub(0x0802B024, lambda e, phase=phase: e.set_regs(r0=phase[0]))
                e.stub(0x0802B02C, lambda e: e.set_regs(r0=1000))
                e.stub(0x08027B9C, lambda e: e.set_regs(r0=0))
                e.stub(0x08027B5C, lambda e: e.set_regs(r0=1000))
            for step in range(64):
                phase[0] = 0
                for e in (self.e, reference):
                    e.call(0x08028244, SEQ, step)
                    e.call(0x08027448, MOD)
                for time in (0, 500, 1000):
                    phase[0] = time
                    for e in (self.e, reference):
                        e.call(0x080269EC, MOD)
                    self.assertEqual(self.e.param(0x101), reference.param(0x101))
                    self.assertEqual(self.e.read(MOD + 0x38, 16), reference.read(MOD + 0x38, 16))

    def test_copy_cancels_on_exit_and_cleanup_consumes_release_after_shift(self):
        self.editor(0, 0)
        self.capture(0x101, 24000)
        self.e.stub(0x08043224, lambda e: self.fail("editor gesture leaked into stock buttons"))
        self.call("press", PANEL, 0x1103, 0)
        self.call("encoder", PANEL, 0x403, 63, 0)
        before = self.e.read(SEQ + 4, 0x824)
        self.call("close_editor")
        self.call("release", PANEL, 0x1103, 0)
        self.assertEqual(self.e.read(SEQ + 4, 0x824), before)
        self.editor(0, 63)
        self.e.write(PANEL + 0x28, b"\x01")
        self.call("press", PANEL, 0x1105, 0)
        self.e.write(PANEL + 0x28, b"\x00")
        self.call("release", PANEL, 0x1105, 0)

    def test_placement_respects_elf_alignment_regions_and_capacity(self):
        intervals = []
        for section in self.report["sections"].values():
            lo, hi = section["address"], section["address"] + section["bytes"]
            self.assertEqual(lo % section["alignment"], 0)
            self.assertTrue(any(start <= lo < hi <= end for start, end in self.native.REGIONS))
            intervals.append((lo, hi))
        intervals.sort()
        self.assertTrue(all(a[1] <= b[0] for a, b in pairwise(intervals)))
        self.assertLessEqual(self.report["native_bytes"], self.report["capacity_bytes"])
        self.assertTrue(all(part.region[0] % 4 == 0 for part in self.patch.parts))

    def test_regions_have_only_retired_factory_references_and_known_decoder_noise(self):
        from refscan import references

        for lo, hi, expected in [
            (0x0802BE90, 0x0802C132, {(0x08074094, "word"), (0x0802BE40, "ldr/adr")}),
            (0x0802CA94, 0x0802CC04, {(0x080740D4, "word")}),
        ]:
            self.assertEqual(set(references(self.stock, firmware.MAIN_BASE, lo, hi)), expected)
        self.assertLessEqual(len(self.payload), firmware.MAIN_END - firmware.MAIN_BASE - 1)
        self.assertEqual((len(self.payload) + 17) % 16, 0)


if __name__ == "__main__":
    unittest.main()

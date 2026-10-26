"""Reference integration against real stock functions, not an installed native patch."""

from __future__ import annotations

import ctypes
import importlib.util
import os
import sys
import unittest
from pathlib import Path

from tools import firmware

ROOT = Path(__file__).resolve().parents[1]
HAS_UNICORN = importlib.util.find_spec("unicorn") is not None

# Facts established by stock-function probes; these are not proposed hook sites.
SET_LENGTH = 0x08028014
ADVANCE = 0x080281F8
GET_POSITION = 0x0802821C
SET_POSITION = 0x08028244
TRIGGER_PREDICATE = 0x0802906C
GET_TRACK_TARGET = 0x08027FB4
SET_TRACK_TARGET = 0x08027FCC
GET_MODULATION_BYTE = 0x08028074
SET_MODULATION_BYTE = 0x08028104
GET_MODULATION_PRESENT = 0x08028090
SET_MODULATION_PRESENT = 0x08028128
PATTERN_BYTES = 0x412
LENGTH_OFFSETS = (0x40D, 0x81F)

# Synthetic emulator objects only, not native allocations or available RAM claims.
ENGINE = 0x20008000
SEQUENCE = 0x20009000


@unittest.skipUnless(HAS_UNICORN, "optional stock emulation needs make setup and make stock-test")
class StockSequencerContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "vendor/ThisFirmwareDoesNotExist/tests"))
        from emu import Emu

        cls.emulator = Emu
        default = ROOT / "original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff"
        path = Path(os.environ.get("FREAKPATCH_STOCK_MFF", default))
        if not path.is_file():
            raise unittest.SkipTest("official firmware absent; set FREAKPATCH_STOCK_MFF")
        raw = path.read_bytes()
        firmware.inspect(raw)
        update = firmware.mff.Update.from_bytes(raw)
        cls.payload = firmware.mff.main_payload(update.read(update.main_name))

    def setUp(self):
        self.emu = self.emulator(self.payload)
        self.emu.write(ENGINE, bytes(0x100))
        self.emu.write(SEQUENCE, bytes(0x900))
        self.emu.write32(ENGINE + 8, SEQUENCE)
        # Stock mode 3 follows the sequencer's step flags without Spice processing.
        self.emu.write(ENGINE + 0x1C, bytes([3]))

    def flag_address(self, pattern, step):
        return SEQUENCE + 0x10 + pattern * PATTERN_BYTES + step * 16

    def test_shared_length_and_stock_cursor_for_both_patterns(self):
        for length in (4, 16, 64):
            self.emu.call(SET_LENGTH, SEQUENCE, length)
            self.assertEqual([self.emu.read(SEQUENCE + offset, 1)[0] for offset in LENGTH_OFFSETS], [length] * 2)
            for pattern in (0, 1):
                self.emu.write(SEQUENCE + 2, bytes([pattern]))
                self.emu.call(SET_POSITION, SEQUENCE, length - 1)
                for expected in range(length):
                    self.assertEqual(self.emu.call(ADVANCE, SEQUENCE), expected)
                    self.assertEqual(self.emu.call(GET_POSITION, SEQUENCE), expected)
                    self.assertEqual(self.emu.call(GET_POSITION, SEQUENCE), expected)

    def test_trigger_predicate_alone_does_not_identify_new_notes(self):
        for flag, expected in ((0, 0), (1, 1), (3, 1)):
            self.emu.write(self.flag_address(0, 0), bytes([flag]))
            self.assertEqual(self.emu.call(TRIGGER_PREDICATE, ENGINE), expected)
        # A native patch cannot safely gate every predicate call: tied steps also
        # pass. The actual new-note dispatch and note-off paths still need tracing.

    def test_stock_modulation_accessors_edit_step_64_without_moving_cursor(self):
        self.emu.call(SET_LENGTH, SEQUENCE, 64)
        self.emu.call(SET_POSITION, SEQUENCE, 17)
        targets = ((0x0000, 0x0100, 0x0601, 0x0D01), (0x0001, 0x0002, 0x0003, 0x0A00))
        for pattern in (0, 1):
            self.emu.write(SEQUENCE + 2, bytes([pattern]))
            for track, target in enumerate(targets[pattern]):
                self.emu.call(SET_TRACK_TARGET, SEQUENCE, track, target)
                self.assertEqual(self.emu.call(GET_TRACK_TARGET, SEQUENCE, track), target)
                address = SEQUENCE + 4 + pattern * PATTERN_BYTES + 63 * 16
                notes_before = self.emu.read(address, 8)
                value = 192 + pattern * 16 + track
                self.emu.call(SET_MODULATION_BYTE, SEQUENCE, 63, track, value)
                self.emu.call(SET_MODULATION_PRESENT, SEQUENCE, 63, track, 1)
                self.assertEqual(self.emu.call(GET_MODULATION_BYTE, SEQUENCE, 63, track), value)
                self.assertEqual(self.emu.call(GET_MODULATION_PRESENT, SEQUENCE, 63, track), 1)
                self.assertEqual(self.emu.call(GET_MODULATION_BYTE, SEQUENCE, 17, track), 0)
                self.assertEqual(self.emu.read(address, 8), notes_before)
                self.assertEqual(self.emu.call(GET_POSITION, SEQUENCE), 17)
        for pattern in (0, 1):
            self.emu.write(SEQUENCE + 2, bytes([pattern]))
            for track, target in enumerate(targets[pattern]):
                self.assertEqual(self.emu.call(GET_TRACK_TARGET, SEQUENCE, track), target)
                self.assertEqual(self.emu.call(GET_MODULATION_BYTE, SEQUENCE, 63, track), 192 + pattern * 16 + track)

    def test_probability_overlay_uses_real_stock_cursor_without_writing_notes(self):
        library_path = ROOT / "build/libfreaklocks.so"
        if not library_path.is_file():
            self.skipTest("build the host reference library with make stock-test")
        library = ctypes.CDLL(str(library_path))
        pointer = ctypes.c_void_p
        unsigned = ctypes.c_uint
        library.fl_init.argtypes = [pointer, ctypes.c_uint32]
        library.fl_init.restype = None
        library.fl_transport.argtypes = [pointer, ctypes.c_int]
        library.fl_transport.restype = ctypes.c_bool
        library.fl_set_probability.argtypes = [pointer, unsigned, unsigned, unsigned]
        library.fl_set_probability.restype = ctypes.c_bool
        library.fl_on_step.argtypes = [pointer, unsigned, unsigned, unsigned]
        library.fl_on_step.restype = ctypes.c_bool
        library.fl_note_allowed.argtypes = [pointer, ctypes.c_bool]
        library.fl_note_allowed.restype = ctypes.c_bool
        # Header's 160-byte ceiling; uint32 storage supplies required alignment.
        state = (ctypes.c_uint32 * 40)()
        library.fl_init(state, 42)
        self.assertTrue(library.fl_transport(state, 0))
        self.assertTrue(library.fl_set_probability(state, 0, 63, 0))
        self.emu.call(SET_LENGTH, SEQUENCE, 64)
        for pattern in (0, 1):
            self.emu.write(SEQUENCE + 2, bytes([pattern]))
            for step in range(64):
                address = SEQUENCE + 4 + pattern * PATTERN_BYTES + step * 16
                self.emu.write(address, bytes([60, 64, 67, 255]))
                self.emu.write(self.flag_address(pattern, step), bytes([0 if step == 12 else 1]))
            before = self.emu.read(SEQUENCE, 0x824)
            self.emu.call(SET_POSITION, SEQUENCE, 63)
            for step in range(64):
                self.assertEqual(self.emu.call(ADVANCE, SEQUENCE), step)
                position = self.emu.call(GET_POSITION, SEQUENCE)
                self.assertTrue(library.fl_on_step(state, pattern, position, 64))
                stock_result = bool(self.emu.call(TRIGGER_PREDICATE, ENGINE))
                expected = stock_result and not (pattern == 0 and step == 63)
                for _ in range(3):
                    self.assertEqual(library.fl_note_allowed(state, stock_result), expected)
                self.assertEqual(self.emu.call(GET_POSITION, SEQUENCE), step)
            self.assertEqual(self.emu.read(SEQUENCE, 0x824), before)


if __name__ == "__main__":
    unittest.main()

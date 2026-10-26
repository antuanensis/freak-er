# FREAKOS

Experimental MicroFreak firmware based on [idea.md](idea.md) and the pinned
[ThisFirmwareDoesNotExist](https://github.com/ThisFreakDoesntExist/ThisFirmwareDoesNotExist) framework.

**Current delivery: experimental r4**, preserving r3’s stock sequencer features:
per-step probability, live locks and first-note editing, in 116 fewer code bytes.
Stock retains A/B,
4..64 steps, clock/notes and four assignable modulation tracks. The user reports
r2 working on the device; **r3/r4 have no device result**. r4 passed local tests
and comparison against the committed r3 source.
See [device evidence](docs/hardware-validation.md).

## Live editor controls

Start the stock sequencer with recording off, then press **Shift+Record**.
Playback continues while `E` selects the step you edit.

| Gesture inside editor | Behavior |
| --- | --- |
| Rate turn | Select edit step. |
| Shift+Rate | Set that step’s probability, 0..100%. |
| Parameter turn | Scale that destination’s existing locks across the active pattern proportionally. |
| Shift+parameter turn | Edit only the selected step. |
| Tap Oct/Mod | Cycle assigned tracks. |
| Hold Oct/Mod for 600 ms | Remove selected track’s lock on this step; Shift optional. |
| Shift+Hold | Clear all four locks on this step and reset probability to 100%; keep notes. |
| Hold Record, turn Rate, release Record | Copy source step’s four locks to destination step. Start without Shift; notes/probability are not copied. |
| Preset turn | Change this step’s first note by semitones. Other chord tones stay unchanged; rests stay rests. |
| Shift+Record | Exit editor. |
| Stop, A/B, Preset push or other workflow button | Close editor and perform stock action. Matrix selection stays in editor; Rate push remains Sync. |

For example, an existing curve `100, 200, 50` becomes `50, 100, 25` when its
selected value moves from 100 to 50. Missing locks stay absent; the other pattern
is untouched. Zero-reference or signed sign changes use a bounded offset instead
of an undefined/reversing ratio. Values saturate at stock’s byte limits, so
clipping and quantization can reduce differences. A newly assigned destination
gets the same value on all steps for a global edit; a Shift edit instead seeds
other steps with the original sound value before changing the selected step.

All **57 stock-recordable destinations** are accepted through stock eligibility
metadata, including oscillator/sample controls and 35 matrix amounts. Four
tracks remain the limit. Shift is consumed as the single-step modifier for pots;
stock-ineligible Shift-only alternate destinations remain unavailable. Matrix
amounts retain signed conversion. Complete oscillator/sample UI behavior still
needs device testing.

OLED example: `A E12/64 N60`, then `%75 T1`, then destination/value. `A`/`B` is
pattern, `E` edit step/length, `N` first note’s MIDI number (`N-` means rest), `%`
probability, and `T1`–`T4` selected track. `T-` means none selected; `TFULL` means
four destinations already allocated. A dash after the destination means no lock
on this step. Values are stock’s stored numeric bytes, signed for matrix amounts.
There is no playback `P` field or copy indicator. Copy source is the step selected
when Record is pressed; exit, Stop, A/B or another edit cancels copying.

Lock deletion restores stock sparse-value hold, so a preceding lock can carry
through the cleared step. It does not insert a hidden baseline lock. Note, copy,
cleanup and probability edits take effect on the next stock visit; a current
parameter edit updates output immediately. Stock smoothing stays active.
See [full behavior contract](docs/specs/004-live-editor-operations.md).

## Capacity

r4 uses **3,662 / 3,809 audited code bytes**, leaving **147 bytes**, and twelve
runtime bytes. It retires eight unused factory console diagnostics to provide
space, including their diagnostic `boot` command; the bootloader and normal boot
initialization are untouched. No new sequence/clipboard bank or heap is added.
Future features need measured savings or newly proven space. This is close to
the current placement limit; the whole idea.md is not promised to fit. The
[measured size pass](docs/size-pass.md) records savings, rejected candidates and
unchanged behavior. The largest current unused region tail is 133 bytes.

## Build and test

Requirements: Python 3.11+, Make, a C11 compiler, and clang with Cortex-M4 Thumb
support. No new runtime package dependencies. Pinned uv tools provide emulation
and lint; proprietary inputs and generated files stay local and ignored.

```sh
make test
make test-sanitize
make check-arm
make setup
make native-test
make stock-test
make lint
```

Keep the untouched official `MicroFreak_Firmware_Update_5_0_0_2084.mff` under
`original_firmware/`. Other versions and previously patched inputs are rejected.
Firmware files and the optional local Arturia manual are not included in Git;
see [local input setup](docs/local-inputs.md).

```sh
mkdir -p build
stock_mff="original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff"
python3 tools/firmware.py inspect "$stock_mff"
python3 tools/firmware.py build "$stock_mff" --stage placement -o build/freak-er-placement-r4.mff
python3 tools/firmware.py build "$stock_mff" --stage passthrough -o build/freak-er-passthrough-r4.mff
python3 tools/firmware.py build "$stock_mff" --stage features -o build/freak-er-stock-sequencer-experimental-r4.mff
```

Each build gets a matching JSON manifest with hashes, compiler, placement and
stage. Existing outputs are never replaced. No command installs/flashes anything.
The images retain stock version identification; distinguish stages by filenames
and manifest hashes. Follow [installation/recovery](docs/recovery.md) and the
[pending device checklist](docs/hardware-validation.md) in order. The feature
experiment is not a validated release or a recommendation to flash immediately.

The earlier `baseline` command reproduces upstream Release only. It contains
neither sequencer addition and is not included in these native builds.

## Development

- [AGENTS.md](AGENTS.md), [current session](docs/session.md), [ordered tasks](docs/tasks.md)
- [Active specification](docs/specs/004-live-editor-operations.md)
- [Architecture](docs/architecture.md), [native contracts and memory evidence](docs/native-integration.md)
- [Testing and limitations](docs/testing.md), [development log](docs/devlog.md)
- [r2/r3 checkpoint and fingerprints](docs/revisions.md), [r4 size pass and fingerprints](docs/size-pass.md)
- [Original stock probes](docs/stock-sequencer-findings.md), [upstream provenance](vendor/README.md)

Only original source/patch definitions may be distributed. Do not publish Arturia
firmware, patched updates, calibration data or dumps. Retain upstream attribution
and [license](LICENSE). Device audio/MIDI timing, interrupts, recovery, full physical-control coverage and MCC persistence remain open release gates.

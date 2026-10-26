# Installation stages and recovery

The user reports probability and r2 working. r3/r4 have no device result; full
hardware validation remains pending. Native MFF builds are experiments with
verified containers, not hardware-validated releases. All
installation steps below are user-operated; repository tools never flash.

## Prepare first

1. Back up presets in MIDI Control Center and verify a saved preset restores.
   Preserve user samples/wavetables and settings separately.
2. Keep the untouched official 5.0.0.2084 update. Verify it using `inspect`.
3. Read Arturia's [V5 procedure](https://support.arturia.com/hc/en-us/articles/9002305582108-MicroFreak-Firmware-V5)
   and your local manual ([setup](local-inputs.md)). Use reliable power and
   direct USB; never interrupt an update.
4. Record stock behavior, clock sources and audio/MIDI timing under four-voice
   load. Record artifact hashes without publishing unit identifiers.
5. Establish official recovery before evaluating a feature build.

Pinned upstream reports recovery by holding **Shift + Arp + Oct** while powering
on, then selecting the untouched official MFF in MIDI Control Center. That is
upstream evidence, not a recovery result from this project. Consult Arturia if
MCC cannot detect the unit. Never modify calibration or the bootloader for recovery.

## Build reproducible local experiments

```sh
mkdir -p build
stock_mff="original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff"
python3 tools/firmware.py build "$stock_mff" --stage placement -o build/freak-er-placement-r4.mff
python3 tools/firmware.py build "$stock_mff" --stage passthrough -o build/freak-er-passthrough-r4.mff
python3 tools/firmware.py build "$stock_mff" --stage features -o build/freak-er-stock-sequencer-experimental-r4.mff
```

Matching JSON manifests record input/output/source/builder hashes, compiler,
placement and stage. Existing paths are never replaced. These images retain
stock's displayed version, so filenames and hashes identify the actual stage.
Do not substitute the old upstream Release baseline; it has neither new feature.

## Evaluate in order

1. **Official stock:** demonstrate backup/restore and recovery; record baseline.
2. **Placement:** in MCC select the placement MFF for manual update. This writes
   native regions but activates no hooks. Eight unused factory console commands
   become no-ops. Verify boot, playing and return to official stock.
3. **Passthrough:** only after placement succeeds, manually install this stage.
   Hooks run while feature behavior is disabled. Compare stock controls,
   sequences, clocks, preset operations and audio/MIDI against the baseline.
4. **Features:** only after prior stages succeed, evaluate the editor/probability
   experiment using the [device checklist](hardware-validation.md). Stop on a
   regression and return to the untouched official image.

MCC's update acceptance and successful device boot are not tested here. There
is no automatic fallback or installation claim. Keep a known-good stock preset
available; modified metadata's MCC/downgrade round trips remain unverified.

## Feature controls to evaluate

While the stock sequencer plays with recording off, Shift+Record toggles editing.
Rate selects a step; Shift+Rate changes its probability. **Unshifted parameter
turns now scale the active pattern’s existing values proportionally. Hold Shift
to change only the selected step.** A new Shift-edited track receives original
baseline snapshots on its other steps; existing gaps are preserved.

Tap Oct/Mod to select a track; hold it for 600 ms to clear that track’s lock on E.
Shift+Hold clears all E locks and resets its probability to 100%. Hold Record
without Shift, turn Rate from source to destination, then release Record to copy
all four lock values/presence bits. Notes/probability are not copied. Preset turns
change only the first existing note by semitones; rests stay rests and other
chord tones stay unchanged. A/B, Stop, Preset push and other workflow buttons
close editing; matrix selection stays inside it. Rate push remains Sync.

OLED labels pattern A/B, edit position E/length, first-note MIDI number N,
probability %, and track T. N- means rest, T- no selected track, TFULL four
allocated destinations. A destination value of dash means no lock at E. P stays
removed. Copy has no additional indicator. Stock sparse hold/smoothing remain;
removing a lock can leave the preceding value sounding. See the complete
[controls and examples](../README.md#live-editor-controls).

r4 preserves r3’s controls and regions while changing code placement. r2 device
success does not replace staged validation of r4. Retain r2/r3 images and matching
manifests as well as untouched official stock. No r3/r4 installation has been
performed by the assistant. See [r4 measurements and hashes](size-pass.md).

Log results and hashes in [hardware validation](hardware-validation.md), including
clock conditions, duration and comparison to stock. No numeric timing tolerance
has been established; derive it from stock measurements before acceptance. No complete r4 boot, recovery, timing, physical-control or endurance gate has
been marked passed.

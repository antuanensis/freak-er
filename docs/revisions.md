# r2/r3 baseline checkpoint

This is the historical checkpoint record. Subsequent r4 measurements and artifacts
are recorded separately in [the size pass](size-pass.md).

Checkpoint date: 2026-10-26. The initial Git commit contains the current **r3
source**, plus records of r2's earlier behavior and local artifacts. It does not
reconstruct separate historical commits or provide a historical r2 source tag.
No shrinking or subsequent feature implementation is included.

All six local MFFs were checked against their JSON manifests before this
checkpoint. Images, manifests and private analysis remain ignored under `build/`;
only build metadata and fingerprints are recorded here. No image was flashed,
published or uploaded by the assistant.

## Shared contract

Both revisions extend official MicroFreak 5.0.0.2084. Stock owns the only
sequencer: A/B, shared 4..64-step length, notes/chords, timing and four modulation
tracks. Probability filters new sequencer note-ons, preserving releases, ties,
modulation playback, keyboard/MIDI and arp. Runtime state occupies twelve bytes.
Persistent probability uses existing step bytes 14/15 with a 0xD3 tag and full-bank
validation. No additional sequence bank, heap or flash writer is added.

Official input SHA-256:
`c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`.
Vendored upstream revision:
`083b15cabde98fc31eb89b40562aeeea38224968`.

## r2: isolated live edits and display correction

- Seed a newly assigned modulation track's other steps with the original value,
  preventing stock sparse-value hold from carrying a single edit around the loop.
- Remove P because it did not refresh as a live playback indicator.
- Retain current/future step editing and stock four-track allocation/signed values.
  Existing sparse tracks are not migrated; use an untouched preset or recreate
  affected tracks when evaluating the fix.
- Historical validation: **39 local Python tests** passed (27 native, eight
  tooling, four stock/model), including full-loop baseline restoration in A/B.
- The user subsequently reported “It works well.” The device's exact artifact
  hash, clock, duration and complete coverage were not supplied. This is positive
  r2 feedback, not completion of the hardware release checklist.

r3 supersedes r2's cloned-recorder/position-hook implementation. In particular,
r3 corrects a playback interpolation difference by removing the old position
replacement; do not treat r2 as having that later correction.

## r3: extended live editor

- Verify all 57 stock-recordable destinations, including signed matrix amounts,
  against the real stock recorder.
- Unshifted knob turns scale existing locks in the active pattern proportionally;
  Shift edits only E. Preserve absent cells and the other pattern, with bounded
  zero/sign-change fallback and stock byte clipping/quantization.
- Tap Oct/Mod to select a track; hold 600 ms to clear its lock on E.
- Shift+Hold clears E's four locks and restores probability to 100%, keeping notes.
- Hold Record, turn Rate, release Record to copy lock values/presence only.
- Preset turns edit the first existing note; preserve rests, other chord tones,
  flags and velocities. OLED adds N and absent-lock dashes; P stays removed.
- Replace the cloned recorder with a narrow stock-target/record adapter. Leave
  position and set-and-send unhooked; playback matches untouched stock with
  identical test RAM over A/B, all steps and three interpolation phases.
- Feature/placement code uses **3,778 / 3,809 audited bytes**, leaving **31 bytes**.
  Eight unused factory diagnostics and an oled-only helper are retired. Normal
  boot audio/conf/filter/ioc, bootloader and calibration remain intact.

Validation: **53 local Python tests** passed without skips (39 native, ten
firmware-tooling, four stock/model). Six C behavior groups, ASan/UBSan, the demo,
Cortex-M4 reference compilation and Ruff lint/format also passed. The r3 staged
artifacts were independently rebuilt with byte-identical output and complete
manifest comparisons. The unchanged upstream previously passed 303 tests;
that suite was not rerun for r3. Source and builder hashes below still match
this checkout, including the later unchanged-source baseline test run.

**No r3 device result exists.** Emulator tests do not prove full boot, audio/MIDI
or interrupt timing, complete oscillator/sample behavior, persistence through
MCC, stack margins, recovery or endurance. See [hardware evidence](hardware-validation.md)
and [controls](../README.md#live-editor-controls).

## Artifact fingerprints

Native sizes count code, including its literal pools. Runtime remains twelve
bytes in all stages. Placement writes regions without activating hooks;
passthrough activates hooks with features disabled. Files retain stock version
identification; identify them by filename and SHA-256.

### r2

| Stage | Local file under build/ | Native bytes | Output bytes | SHA-256 |
| --- | --- | ---: | ---: | --- |
| placement | `freak-er-placement-r2.mff` | 2,922 | 943,012 | `ca9b80d06912fa3ddc317cb6ff3043cfb715b34ef9952365204185aebd89063b` |
| passthrough | `freak-er-passthrough-r2.mff` | 1,542 | 941,972 | `fe9c7a81ad4a1b6d9ecff1fcd4790147be84b1f9db5b6ad916016698881e0d33` |
| features | `freak-er-stock-sequencer-experimental-r2.mff` | 2,922 | 943,012 | `d7cfe1fdb83f6dc7b57b8e6c79add83bb187e8f1b80b2754f762cc44325a5abb` |

Compiler: `Apple clang version 21.0.0 (clang-2100.1.1.101)`.

Native source SHA-256: `23879df6884604af994a8de013f3bc4c921c8065d34f4e9558efcb02cb9e5105`.

Builder SHA-256: `40874270c30c85a3140c2ae54b3e03d4f94407a5d5e8a9d0eaf7f55a54f00f3c`.

### r3

| Stage | Local file under build/ | Native bytes | Output bytes | SHA-256 |
| --- | --- | ---: | ---: | --- |
| placement | `freak-er-placement-r3.mff` | 3,778 | 943,012 | `7d164208abb9987dfac71d55cf1b1f4182c29a6bec601b67eaa684d418bac8a1` |
| passthrough | `freak-er-passthrough-r3.mff` | 1,358 | 941,572 | `f05ab47156636e9b84243733b8dd8bec44ff3809046f674e22fec63c70156157` |
| features | `freak-er-stock-sequencer-experimental-r3.mff` | 3,778 | 943,012 | `313d7a485b2753bdde07be12aef7f34f34962643443cf82c48162b89853a0dbb` |

Compiler: `Apple clang version 21.0.0 (clang-2100.1.1.101)`.

Native source SHA-256: `26735831138fd1af331c4e4b5900fcf494eaaf9ad5726069054e5ce140ab52ef`.

Builder SHA-256: `ce46627a926bcc222529d8b14de50d7fe274b637bcbb599016e8dbf0d9c15cf0`.

## Build commands and historical reproducibility

The source at commit `6a5c412` builds **r3**. Current size-pass source builds r4;
filenames do not select a revision. Use the r3 source checkout for these historical
commands, with your own official input ([setup](local-inputs.md)) and unused paths:

```sh
mkdir -p build
stock_mff="original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff"
python3 tools/firmware.py inspect "$stock_mff"
python3 tools/firmware.py build "$stock_mff" --stage placement -o build/freak-er-placement-r3.mff
python3 tools/firmware.py build "$stock_mff" --stage passthrough -o build/freak-er-passthrough-r3.mff
python3 tools/firmware.py build "$stock_mff" --stage features -o build/freak-er-stock-sequencer-experimental-r3.mff
```

The following are **historical commands**, executed with the r2 source/builder
before r3 changes. Running them against another revision would build that revision
under misleading r2 names; filenames do not select a source revision. The local
r2 source snapshot is incomplete and is not presented as a reproducible release
checkout. Keep the verified existing r2 files and manifests locally.

```sh
# Historical r2 source/builder only; not the current checkout.
python3 tools/firmware.py build "$stock_mff" --stage placement -o build/freak-er-placement-r2.mff
python3 tools/firmware.py build "$stock_mff" --stage passthrough -o build/freak-er-passthrough-r2.mff
python3 tools/firmware.py build "$stock_mff" --stage features -o build/freak-er-stock-sequencer-experimental-r2.mff
```

Output and matching JSON paths are exclusive: existing files are never replaced.
Exact binary reproduction requires the recorded compiler/build environment;
other compilers may produce different code sizes, placement and fingerprints.
For device evaluation follow [installation/recovery](recovery.md) in stage order.

## Next development boundary

Keep this checkpoint unchanged while assessing a separate size optimization.
Preserve existing behavior, metadata, twelve-byte runtime and proven regions;
accept savings only after tests and complete linked-size measurements. The
remaining 31 bytes are current layout headroom, not a promise that every future
feature fits. Later features require separate feasibility work. No remote is
configured or publication performed as part of this checkpoint.

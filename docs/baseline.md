# Firmware baseline and evidence

Last reviewed: 2026-10-23. Target: official **5.0.0.2084** only.

## Reproduced locally

The supplied local official file passed the upstream SHA-256 gate:

```text
c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c
```

Container size is 941,572 bytes. The main payload is 473,695 bytes, excluding its
64-byte header and trailing checksum. `inspect` validated that payload's checksum.
The pinned upstream Release build reproduced deterministically with SHA-256:

```text
282ec291a73e89800c52872e4446664e350818978824e1e89003bdadda7d4834
```

The generated local artifact is `build/upstream-release.mff`. It provides upstream
separate Decay/Release behavior only. It contains no native FreakLocks code and
has not been flashed or listened to by this project.

## Upstream analysis, not independently established hardware facts

The pinned [main-image analysis](../vendor/ThisFirmwareDoesNotExist/docs/main-image.md)
infers an STM32F446 Cortex-M4F with 512 KiB flash and 128 KiB SRAM. Its table labels
the CPU identification as inferred; do not upgrade that to a board inspection.

- Main payload begins at `0x0800C000`. Bootloader and per-unit calibration lie below
  it and are excluded from modification.
- Appended space begins at `0x0807FA60`; the window to `0x08080000` is 1,440 bytes,
  including the final checksum. Alignment/fill consume part of that window.
- Upstream reports practically fully allocated SRAM. Four voice objects alone
  occupy 92,048 bytes. No free native region has been reserved for FREAKOS.
- Retirable console handlers are already used by upstream's combined voice-mode
  build. Baseline Release and combined voice-modes are alternative compositions;
  the latter must not be silently enabled as a FREAKOS foundation.
- Stock offers 20 parameter groups in 24 slots; upstream Release uses group 20.
  Unused group slots do not prove backing RAM or preset capacity is available.
- Stock has A/B sequences of up to 64 steps and four modulation lanes. Reusing
  their data/control paths is preferable to replacing them without evidence.

See [space constraints](../vendor/ThisFirmwareDoesNotExist/docs/free-space-and-dead-code.md)
and [flash writers](../vendor/ThisFirmwareDoesNotExist/docs/flash-writes.md).
Upstream hardware success, emulation, and inference must retain their labels.

## Candidate extension points

These are leads from upstream documentation, not approved new hooks:

- Parameter object: `0x2001C898`; getter `0x08023C2C`, setter `0x08023C40`.
- Sequencer position reader: `0x0802821C`. Local probes established that
  `0x080281F8` **advances** position, despite the upstream page describing its use
  as obtaining position. Never call it just to inspect the cursor. Higher-level
  advancement paths include `0x080290DC` and `0x080292D4`.
- Existing sequencing/randomization behavior:
  [Spice and Dice](../vendor/ThisFirmwareDoesNotExist/docs/spice-and-dice.md).
- Display/control transport:
  [screen and LEDs](../vendor/ThisFirmwareDoesNotExist/docs/screen-and-leds.md).

Before any native adapter: trace the actual playback path against the official
image, prove caller and register contracts, locate state storage, measure timing,
then test placement and an unchanged pass-through hook before feature behavior.
Do not choose an address from this list merely because it appears plausible.

The new [stock sequencer findings](stock-sequencer-findings.md) record reproduced
function behavior and remaining hook gaps. None of these addresses has been
installed as a new FREAKOS hook.

## Manufacturer references

Arturia's [downloads page](https://www.arturia.com/support/downloads-manuals/product/microfreak)
currently lists 5.0.0.2084 and the 5.0.1 English manual. Its
[general FAQ](https://support.arturia.com/hc/en-us/articles/4405748052626-MicroFreak-General-Questions)
documents four paraphonic voices sharing one filter. Per-voice digital modulation
is a research direction; independent simultaneous analog filters are impossible
through software alone. Refer to manufacturer sources for hardware operations,
and to upstream for reverse-engineered addresses.

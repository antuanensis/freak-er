# Spec 001: reproducible patching baseline

Status: Active; software checks implemented, hardware gates pending.

## Scope

Pin and preserve the supplied patch framework. Inspect the exact official update,
reproduce its existing Release build, and establish constraints before native
FREAKOS modifications. Never flash hardware automatically.

## Acceptance

- Accept only official 5.0.0.2084 with SHA-256
  `c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`.
- Parse the container and validate the main-image checksum using upstream code.
- Build the Release baseline deterministically with output SHA-256
  `282ec291a73e89800c52872e4446664e350818978824e1e89003bdadda7d4834`.
- Preserve the input and every existing output; publish a complete verified file.
- Run upstream regression/emulation tests against the local official update.
- Document attribution, memory limits, evidence levels, and manual recovery.
- Hardware exit gate: the user demonstrates official recovery, records stock
  audio/MIDI timing and preset backup/restore, then validates the baseline.
- Native extension exit gate: prove sequencer hook and available RAM/code space
  with displaced-instruction/register contracts and timing measurements.

The last two gates cannot be completed by desktop tests. Reference-core work can
proceed in isolation while they remain open; native feature deployment cannot.

## Validation

`make test`, `make upstream-test` with `FREAKPATCH_STOCK_MFF` set, and the two
`tools/firmware.py` commands in README. Firmware and generated updates stay ignored.

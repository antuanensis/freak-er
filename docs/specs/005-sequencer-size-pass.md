# Spec 005: behavior-preserving sequencer size pass

Status: Implemented and locally validated as r4; hardware pending. Baseline:
commit 6a5c412, experimental r3. Results: [size evidence](../size-pass.md).

Reduce the complete native footprint below 3,778 bytes within the same 3,809
proven bytes. Keep all spec 004 behavior, existing hooks, twelve-byte state,
probability encoding/seed, preset compatibility and stock sequencer ownership.
No new feature, new memory region, firmware stacking or feature removal.

## Ordered changes

1. Replace constant function-pointer calls with typed direct stock symbols,
   using the pinned linker's existing absolute branch relocations. Preserve
   trampolines, six-argument note forwarding and inline register/APSR contracts.
2. Measure selective private-helper extraction and shared setup/cleanup. Keep
   only net linked-size wins. Preserve guard ordering, complete metadata
   validation, raw increments and identical OLED message contents.
3. Record exact compiler arguments and per-region occupancy in build manifests.
   Count literal pools and alignment; moving bytes is not a saving.

No compiler-only saving has been found: baseline 3,778; no-inline 3,790;
frame-pointer omission and machine outlining remained 3,778. These experiments
are not firmware feature changes.

## Acceptance

Run focused native tests per accepted candidate and the complete local suite for
the final source. Compare observable r3/candidate behavior, including records,
modulation caches/output, probability/RNG, controls and OLED contents. Preserve
all 57 destination recorder-parity cases and unhooked stock playback. Compare
stack usage and keep fixed RAM at twelve bytes. Reject any stack regression.

Build separate placement, passthrough and feature r4 artifacts from official
input. Independently rebuild each and compare full manifests/output. Preserve
r2/r3 images and source checkpoint. Report total savings, remaining usable gaps,
rejected candidates and limits. No publication, flash or device-validation claim
is part of this implementation. The user subsequently requested a separate source
commit of the validated r4 shrink.

## Result

r4 uses 3,662 bytes: 116 saved, 147 remaining, with twelve fixed runtime bytes.
Direct calls save 68; selective scaling extraction saves 48. All 54 local Python
tests pass, including state/message and per-operation stack equivalence across
39 r3/r4 native scenarios. Observed maximum stack falls from 324 to 308 bytes;
a smaller 3,650-byte candidate was rejected for per-operation stack increases.
No feature or guard was removed. Device timing/stack and full hardware gates
remain open; emulator measurements are limited to the exercised fixtures.

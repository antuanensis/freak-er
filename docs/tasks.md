# Ordered development queue

## Current milestone

Only per-step probability and live editing inside stock's A/B, shared 4..64-step
sequencer and four existing modulation tracks. [Spec 004](specs/004-live-editor-operations.md), extending spec 003,
controls behavior. [Spec 005](specs/005-sequencer-size-pass.md) covers the r4
size pass; the broader idea.md remains deferred.

## Completed local implementation

- [x] Pin upstream, validate exact official input, reproduce Release and preserve attribution.
- [x] Replace the separate sequencer prototype with a portable probability/editor model.
- [x] Trace and hook actual stock boundaries and six-argument note dispatch.
- [x] Preserve stock Start/Continue/Stop and exclude arp from probability draws.
- [x] Match the real recorder’s eligibility, four-track assignment, signed/raw conversion and full-track behavior.
- [x] Support future/current edits and initialize stock interpolation caches correctly.
- [x] Capture real pot/encoder dispatch; supply selected snapshot reads and retain fine relative increments.
- [x] Implement Shift+Record, physical Rate/alternate, Shift+Rate and editor closure.
- [x] Add stock-owned OLED page and versioned existing-record metadata.
- [x] Test raw serialization/load, single-pattern reload, A/B copy, legacy/clear defaults and built-in reset.
- [x] Validate twelve-byte runtime allocation, retired-region references, ABI/prologues and inline register/flag preservation.
- [x] Add placement/passthrough/feature build stages, strict input checking, verified MFF output and manifests.
- [x] Add 39 native emulation tests, in addition to reference/tooling/upstream checks.
- [x] Reproduce new-track sparse hold; seed baseline cells for new destinations,
  preserve existing tracks, and omit the non-live P display in revision r2.

- [x] Record user’s positive r2 device report, without assuming full hardware gates.
- [x] r3: all 57 stock destinations, proportional global/Shift-local parameter edits.
- [x] r3: Oct tap/600-ms single-lock delete, Shift+Hold step cleanup and Record-held copy.
- [x] r3: Preset first-note pitch editing; preserve rests, flags and other chord tones.
- [x] Remove old position/output hooks; match untouched stock playback and actual recorder.
- [x] Fit 3,778/3,809 audited bytes with actual ELF alignment, unchanged twelve-byte runtime.
- [x] Pass 53 local Python tests; build/rebuild all three r3 stages, preserve r2.
- [x] Synchronize spec, architecture, controls, capacity, installation and handoff.

Evidence and exact limits: [native integration](native-integration.md).
These checkboxes mean local implementation/emulation, never device acceptance.

## Git checkpoint and next development

The initial checkpoint contains r3 source, r2 history and verified fingerprints
for all six local stage artifacts; see [revision records](revisions.md). Local
manual/editor files and generated/private artifacts remain ignored. No remote or
push is part of this checkpoint.

The initial checkpoint contains no size changes. The separate r4 source checkpoint
saves 116 code bytes, preserving all r3 behavior and the
twelve-byte runtime. No new feature is included. [Measured results](size-pass.md):

- [x] Replace indirect fixed-address calls/returns with direct stock branches.
- [x] Extract only the scaling loop; reject candidates with stack regressions.
- [x] Pass all 54 local Python tests, including 39 scenarios compared on r3/r4.
- [x] Record compiler flags/stack frames and per-region occupancy in manifests.
- [x] Build and independently reproduce all three r4 stages and full manifests;
  preserve all six r2/r3 image fingerprints and the source checkpoint.

Next acceptance work is staged r4 device validation; future features need new
feasibility work. The r4 shrink is checkpointed separately; no r4 flash is recorded.

After measured shrinking, research priorities are: per-key AFX-style recall,
Brownian through the existing LFO, two-state modulation-matrix morphing,
Euclidean/generative-harmony arp, independent main-envelope Decay/Release, then
expanded per-voice digital modulation. These are not implementation commitments
or a guarantee of fitting one image. Broader idea.md work remains speculative.

## Remaining release gates — target hardware required

1. Demonstrate official recovery and verified preset/sample backup/restore.
2. Measure stock audio/MIDI timing and representative four-voice workload.
3. Validate placement-only image, then passthrough hooks, before feature behavior.
4. Exercise real controls, oscillator/sample destinations, signed matrix edits,
   ties/sustained notes, four-track rejection, all clocks and Stop/Continue.
5. Validate device save/reboot, A/B copy/reload/clear, MCC import/export and
   downgrade/resave compatibility of metadata.
6. Run extended stability and compare stack/timing/audio behavior with stock.

Record actual results in [hardware validation](hardware-validation.md). User-reported probability and positive r2 operation are recorded there; r3/r4 and
detailed gates remain open.
Build artifacts alone do not close any gate. See
[recovery/install procedure](recovery.md).

## Deferred

Conditional triggers, extra tracks, another sequencer, ratchets, microtiming,
new directions, drones, morph/mutate, scenes and external companions are outside
this milestone. Formatting every destination's OLED value in physical units is
also deferred; current display reports its stored snapshot value. Editing chord
voices beyond the first note, creating notes on rests and a copy indicator are
not implemented. Further features need measured code savings or newly proven
space; r4 has 147 remaining bytes, with a largest current region tail of 133.
This does not establish that any additional requested feature fits.

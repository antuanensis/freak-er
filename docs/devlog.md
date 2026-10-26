# Development log

## 2026-10-23 — Baseline and first FreakLocks reference slice

- Initialized the nearly empty project around the supplied idea.md. Preserved
  that document and the supplied firmware; all proprietary/generated binaries
  stay ignored.
- Copied the exact 70-file upstream snapshot at
  `083b15cabde98fc31eb89b40562aeeea38224968`, with its MIT license, tests, and
  research evidence. The source checkout was not modified.
- Added identity inspection and exclusive atomic baseline generation. The local
  official image matched the required SHA-256; generated upstream Release matched
  `282ec291a73e89800c52872e4446664e350818978824e1e89003bdadda7d4834`.
- Implemented allocation-free 16-step reference locks with deterministic
  probability/conditions and live edits. Pattern is 256 bytes; host player is
  24 bytes. Native integration is intentionally gated, not claimed complete.
- Added AGENTS.md, ordered roadmap, specs, architecture decision, testing,
  recovery guidance, and session handoff.
- Validation: five C behavior groups/100,000 steps; seven Python tests; sanitizers;
  demo; Thumb compilation; lint; 303 upstream regression/emulation tests, no skips.
  Upstream suite required execution outside the sandbox after Unicorn's native
  startup crashed inside it. No dependency or firmware changes were needed.
- ARM object inspection found 634 executable bytes and an unresolved
  `__aeabi_memcpy` helper, which must be addressed in native linkage/budgeting.
- Remaining: prove sequencer hooks and native memory, establish actual timing and
  recovery evidence, then continue the FreakLocks integration slices. No hardware
  flash or listening test was performed.

## 2026-10-23 — Scope changed to stock probability and live editing

- User required the stock sequencer as the only playback engine, then narrowed
  additions to probability and live modulation-track editing. Replaced the
  separate 16-step/conditional prototype with a 64-step A/B extension model.
  Stock retains four assignable targets, notes, transport, gates and modulation.
- Added spec 003 and ADR 0002; marked the earlier contract superseded. Read the
  supplied 5.0.1 manual and proposed an editor using Shift+Record, Rate,
  Shift+Rate, and stock parameter controls while preserving existing shortcuts.
- Added one-draw-per-boundary probability caching and raw-value edit requests.
  No fixed destination list or new parameter restoration policy remains. The
  full native control/write adapter is not implemented.
- Probed official stock functions under Unicorn. Confirmed that `0x080281F8`
  advances the cursor and `0x0802821C` reads it. The trigger predicate alone is
  insufficient to distinguish new notes from tie-like states.
- Identified existing track target, modulation-byte and presence accessors.
  Four stock integration tests verify A/B shared length and step 64, cached
  probability over real stock cursor callbacks, and real modulation writes
  without cursor or note/velocity changes. Value conversion and recorder/UI
  dispatch remain separate outstanding proof.
- Validation: six C groups/100,000 boundaries; seven firmware-tool tests; four
  stock emulation tests outside sandbox; ASan/UBSan; demo; Cortex-M4 compilation.
  Reference state is 144 bytes; ARM object has 674 executable bytes and no
  undefined helper symbols. None of this reserves native memory or measures
  device timing.
- Native merged firmware remains unavailable. No patch was generated for these
  features and no device was flashed. The old Release artifact is baseline only.
- Final checks: lint/format, local documentation links, vendored-source identity,
  binary ignore rules, and whitespace passed. The user's PDF and editor files
  were preserved; upstream source remains unchanged.

## 2026-10-25 — Native stock-sequencer experimental images

- Implemented the exact-version native adapter for probability and live editing
  inside the stock sequencer. Reused stock boundary, transport, note-controller,
  recorder, four-track allocation, parameter conversion and smoothing paths.
  Added Shift+Record/Rate controls and a stock-owned OLED editor page.
- Proved twelve runtime bytes in unused CC-table slots and existing step-record
  metadata for probability. Added constructor, signed getter, six-argument note
  ABI, trampoline and inline encoder register/APSR checks. Kept stock cursor
  advancement in arp mode while excluding arp from probability draws.
- Fixed first-write recorder arming, new/current interpolation caches, repeated
  fine relative increments and discrete Type scaling. Selected-value overlays
  are panel-scoped; future edits preserve global output and active-model context.
- Added deterministic placement into audited regions, reference scans, strict
  official-input checks, placement/passthrough/feature stages, verified containers
  and exclusive atomic image/manifest publication. No Release feature patches,
  bootloader/calibration edits or flash calls were added. Four unused factory
  console commands become no-ops to provide code space.
- Generated all three local MFF images and independently rebuilt each
  byte-identically, comparing every builder report field and output hash with its
  manifest. Feature and placement code occupy 2,904 bytes; passthrough occupies
  1,524 bytes. Current hashes and paths are recorded in session.md. Intermediate
  artifacts were preserved in an explicitly superseded ignored directory.
- Validation: six C groups/100,000 boundaries, ASan/UBSan, demo, Cortex-M4 reference
  compile, Ruff lint/format, all 36 local Python tests (24 native, four stock-model,
  eight tooling), and 303 unchanged upstream tests passed. Python emulation suites
  ran with normal host access because sandboxed Unicorn initialization crashes.
  No skips in the full local or upstream suites.
- Updated architecture, ABI/storage evidence, ADR, spec, tasks, installation and
  recovery procedure, hardware checklist, testing guide, AGENTS and handoff.
  Retained the portable reference model separately from native device state.
- No hardware has been flashed or tested. MCC update acceptance, boot/recovery,
  physical controls, full oscillator/sample UI, audio/MIDI/interrupt timing,
  stack margins, device persistence, MCC/downgrade round trips and endurance are
  still release gates. Generated MFFs are experiments, not validated releases.

## 2026-10-25 — First user-reported probability result

- The user reports per-step probability working on the experimental MFF and the
  editor OLED showing A/E/P/%/T fields. Recorded this as preliminary device
  evidence, with exact artifact hash and test conditions still unknown.
- Updated current status documents; detailed probability cases, live editing,
  persistence, MCC compatibility and hardware regression gates remain open.
  No firmware code or generated image was changed for this documentation update.

## 2026-10-25 — r2 isolates new live-edit tracks and removes stale P

- User reported Cutoff T1 and Resonance T2 affecting the whole sequence when no
  other step values existed. Real stock playback reproduced the cause: a lone
  modulation snapshot holds through following empty steps. Prior tests verified
  isolated writes but missed the audible full-loop consequence.
- New destinations now receive the original value on their other 63 steps before
  normal stock playback. Existing destinations and sparse cells remain intact,
  including when the playback cache is uninitialized after loading. Signed
  matrix baselines use their correct raw >> 8 conversion. Notes, metadata,
  other tracks/patterns and stock smoothing are preserved.
- Removed P because it refreshed only on editor events. Reduced the decimal
  formatter to its actual 0..255 field range, with exhaustive value coverage,
  keeping the fix within existing audited code regions and twelve runtime bytes.
- Validation: reproduced the failing regression before the fix; all 39 local
  Python tests passed afterward (27 native, eight tooling, four stock/model).
  Added full-loop Cutoff/Resonance playback for A/B and existing-track protection.
  Ruff lint/format passed. No upstream or core source changed.
- Built separately named placement/passthrough/features r2 images without
  replacing prior files. Feature/placement native code is 2,922 bytes;
  passthrough is 1,542 bytes. Current hashes are recorded in session.md.
- Existing tracks are not migrated. Retest on an untouched preset or clear and
  recreate affected tracks with desired baseline values set outside the editor.
  Adjacent-step blending remains normal stock smoothing. No r2 device test or
  assistant-operated flash occurred; hardware confirmation remains pending.

## 2026-10-25 — r3 bounded live editor operations

- User reported r2 working, then requested stock-wide destination coverage,
  per-step deletion/cleanup/copy, proportional global vs Shift-local edits and
  live note changes. Spec 004 records exact controls and deliberate limits.
- Implemented all 57 stock-recordable IDs through metadata, proportional scaling
  of existing values with bounded zero/sign fallback, Oct tap/600-ms lock delete,
  Shift+Hold cleanup and Record+Rate+release lock copy. Preset turns change the
  first existing note only, preserving other chord tones, flags, rests and velocity.
  OLED adds first-note N and absent-lock dash; no copy indicator/storage is added.
- Replaced cloned recorder and scoped position/output hooks with a narrow adapter
  using stock target assignment/record fields. Actual stock recorder parity covers
  every eligible ID, baseline conversion and LEDs. Removing the old position hook
  also restores untouched-stock playback interpolation across the full loop.
- Added only independently checked retired factory sync/oled/boot/cvout commands
  and the oled-only helper. Normal boot initialization/bootloader remain intact.
  Whole-function exact packing respects actual ELF alignment; per-region Parts
  meet upstream word alignment. r3 fits 3,778/3,809 bytes, leaving 31; runtime 12.
  Future features need measured savings or new proven space, not arbitrary gaps.
- All 53 local Python tests passed without skips: 39 native, 10 tooling, 4 stock/model.
  Includes actual LFO/matrix dispatch, global/local curves, release/cancel edge
  cases, timer wrap, pitch limits, untouched-stock playback and packing rejection.
  C groups, ASan/UBSan, demo, ARM reference compilation and Ruff lint/format
  also passed. Unchanged upstream previously passed 303 tests; not rerun for r3.
- Built separate placement/passthrough/features r3 MFFs; independent rebuilds and
  complete JSON manifests match. Feature/placement 3,778 bytes; passthrough 1,358.
  Existing r2 image hashes remain unchanged. Updated spec, controls, architecture,
  ADR 0004, AGENTS, tests, install/recovery, hardware checklist and session handoff.
- No r3 device testing, flash, commit or publication. r2’s positive user report
  does not establish r3 placement acceptance, full control coverage, timing,
  persistence, MCC compatibility, recovery or endurance.

## 2026-10-26 — r2/r3 source checkpoint before shrinking

- Prepared one initial Git checkpoint containing current r3 source and documented
  r2 history, without fabricating a historical r2 commit from partial snapshots.
- Added revision records for behavior, controls, test evidence, all six local
  artifact sizes/hashes, source/builder hashes and historical build commands.
  Current checkout builds r3; r2 filenames do not select historical source.
- Rechecked every r2/r3 MFF against its local manifest and confirmed current
  native source/builder match r3 hashes. r2's positive user report and r3's
  pending hardware status remain distinct.
- Kept official inputs, generated builds/private analysis, the supplied manual
  and local editor settings out of Git, preserving the local files. Documented
  how to supply the optional manual and exact official firmware.
- Updated the handoff and queue: no shrinking or future feature implementation
  is included. Previous read-only/compiler-only planning did not change source.
  The next code change is a separate behavior-preserving optimization.
- Checkpoint validation reran all 53 Python tests without skips, six C behavior
  groups, ASan/UBSan, the demo, Cortex-M4 reference compilation and Ruff
  lint/format successfully. Documentation links and whitespace passed. All
  seventy vendor files still match the pinned source. The commit candidate
  contains only text files; firmware/manual/editor/build inputs stay ignored.
- No remote configuration, push, publication or assistant-operated flash is
  included. The user will create the remote repository separately.

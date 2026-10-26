# Spec 003: stock sequencer probability and live modulation editing

Status: Implemented; r2 received a positive user device report. Controls and
implementation now extended by [spec 004](004-live-editor-operations.md).
Probability/storage contracts remain active. Complete hardware/MCC gates remain
open; see [native contracts](../native-integration.md) and
[device validation](../hardware-validation.md).

This supersedes spec 002's separate 16-step reference transport. The user's
clarification limits this milestone to per-step probability and live editing of
existing modulation tracks. Conditional triggers and additional sequencers are
outside this milestone.

## Preserve stock behavior

There is one playback system: the stock sequencer, with A/B patterns, one shared
length of 4..64 steps, stock clock/transport, notes/chords, velocities, ties/rests,
gate scheduling, keyboard priority, modulation recording, and smoothing.

Keep the existing four modulation tracks per pattern. Each can use any destination
the stock recorder already supports, including oscillator/sample selection and
signed matrix amounts. Do not limit destinations to Wave/Timbre/Shape/cutoff; do
not reinterpret signed values as unsigned percentages. Do not promise unlimited
targets or add support for stock-ineligible buttons, Utility settings, or
Shift-only parameters. Preserve stock's full-track behavior and Memory full
result when a fifth target is attempted.

The extension owns no note pattern, clock, next-step counter, gate queue, or
modulation value bank. It receives the stock pattern, position, and length at a
real step boundary and issues edits back to stock-owned storage.

## Probability

- A/B each have 64 probability values, default 100%. Old presets must behave as
  100% until compatible extension metadata is actually present.
- Consume one deterministic random draw per actual stock step boundary, including
  rests. Cache that visit's result; repeated trigger queries and UI redraws must
  not reroll. A new visit to the same step, including a one-step-position reset,
  is a new draw. No guessed wrap counter replaces the stock boundary notification.
  Intermediate percentages use a 65,536-value random grid; 0% and 100% are exact.
- Combine the cached result with stock's decision only when starting a new note
  or chord. 0% suppresses it; 100% preserves stock. Chord voices share one result.
- Never filter note-offs, panic/Stop, tie continuation/release, keyboard/MIDI input,
  arp events, or modulation-track playback. Skipping a note must not skip its
  modulation events or change stock parameter restoration/smoothing behavior.
- Editing the currently playing step's probability affects its next visit; it
  does not reroll, retrigger, or cut off the current note.
- Mirror stock Start/Continue/Stop. Start resets the configured PRNG seed;
  Continue retains PRNG progression; Stop invalidates the cached trigger and
  closes the editor. Stock remains responsible for releasing notes.

## Historical r2 controls

This section records the original r2 controls. Spec 004 supersedes the parameter
scope, Oct/Mod, Hold, Record-copy and Preset gestures. Use its control table for
r3. Dispatch/release ordering has emulator coverage; the user reports r2 working
without detailed physical-control coverage.

| Context / gesture | Behavior |
| --- | --- |
| Sequencer playing, recording off: Shift + Record | Toggle the live step editor without changing Play or Record. Consume the Record gesture before stock starts recording. |
| Editor: turn Rate/Swing | Move edit cursor through steps 1..length; playback cursor stays independent and stock-driven. |
| Editor: Shift + turn Rate/Swing | Set selected step's probability, 0..100%, clamped at endpoints. |
| Editor: turn a stock-recordable parameter knob | Edit only the selected step through the stock modulation-track writer; retain four-track allocation and signed/raw value formats. |
| Editor: Oct / Mod | Keep stock modulation-track selection. |
| Editor: Play/Stop | Keep stock transport; stopping also closes editor. |
| Editor: A/B | Perform stock pattern change and close editor; never silently keep editing the other pattern. |
| Editor: Shift + Record | Exit; restore Rate/Swing's normal role. |
| Recording active or arpeggiator selected | Do not enter editor; preserve that stock workflow. |
| Outside editor | Every existing shortcut keeps its stock meaning. |

Rate push continues to be stock's Sync control; no new meaning is assigned.
Shift + Rate's editor role is context-specific. Outside the editor its existing
swing/sequence-length behavior remains intact. Do not steal Shift+A/B reload,
A/B+Hold clear, A+B copy, Oct/Mod+Hold clear-track, Hold/Tie/Rest, or keyboard
transpose gestures.

OLED shows active pattern, selected edit step/length, selected
modulation track/destination/value, and probability. The edit cursor must not be
confused with the playback cursor. Playback position is omitted in r2 because
it was not continuously refreshed. Use existing screen ownership/lifecycle rather
than drawing a permanent overlay from a knob handler.
Current numeric values report the stock snapshot byte, signed for matrix amounts;
physical-unit/name formatting for each destination is deferred.

## Original single-step edit semantics

The following single-step behavior is retained under Shift in r3; spec 004 also
defines global edits and other operations.

Capture a stock parameter ID and its raw 16-bit value after stock eligibility and
range checks. Route a bounded edit request to the stock writer in a serialized
control context. Do not copy or allocate a parallel modulation sequence. A fifth
track target fails visibly without changing existing assignments.

Editing a future step changes that stored snapshot without changing today's
global/base parameter. Editing the active step updates its existing modulation
output immediately through the normal stock parameter path and smoothing. It
must not restart the sequencer, emit a new note, or change probability's cached
decision. Incoming MIDI controls and keyboard performance retain stock behavior;
the new selected-step capture applies only in the explicit panel editor context.
After a current edit, subsequent ticks may quantize to stock snapshot resolution.
Both active interpolation endpoints receive the new value; the following stock
boundary resumes smoothing from it. Relative editing retains fine increments
between turns and invalidates that cache when the edit cursor moves.

When a live edit first assigns a destination, initialize every other step of
that new stock modulation track to its original value. This prevents a single
snapshot from holding across empty steps and sounding global. Use stock numeric
resolution and preserve its smoothing, including neighbouring-step blends.
Do not rewrite other cells of an existing track: its recorded values and sparse
behaviour remain stock-owned. Existing tracks from earlier experiments are not
automatically migrated; clear/recreate them or use an untouched preset to test r2.

## Acceptance and release gates

- Reference implementation has no independent playback or fixed destination list.
- Test both patterns at step 64, all stock lengths, shared length changes, repeated
  trigger queries, 0/100/intermediate probability, and Start/Stop/Continue.
- Test live edit requests for arbitrary eligible IDs and negative matrix values,
  future/current steps, full-track rejection, and no transport/RNG mutation.
- Run the real stock position/advance/length and trigger functions in emulation
  to demonstrate one unchanged stock cursor and note data.
- Identify actual boundary, note-on-only, panel, modulation-write, and screen
  hooks with displaced-instruction/register contracts. A plausible trigger
  predicate alone is not sufficient because ties and note-offs must survive.
- Prove native RAM/code ownership. The reference probability table's 128 bytes
  are a budget request, not available RAM. Apparent padding is not free until
  all readers/writers and the persistence parser/saver have been audited.
- Prove metadata save/load/defaults, A/B copy/reload/clear, preset changes and MCC
  compatibility. Do not hide probabilities in unproven stock record bytes.
- Require staged device placement/pass-through and behavior tests, clock/audio
  comparison, no stuck notes, and recovery before suggesting a feature flash.

Manual source: the user-supplied [5.0.1 manual](../microfreak_Manual_5_0_1_EN.pdf),
printed pages 81..90 and Appendix C page 140. It confirms existing four-track
recording, destination coverage, transport, and shortcut collisions. It does not
prove any new gesture is free in the actual button dispatcher.

# Spec 002: FreakLocks reference core, slice 1

Status: Superseded by [spec 003](003-stock-sequencer-extension.md). The original
16-step reference implementation was replaced after the user requested only
probability and live modulation editing in the existing stock sequencer. The
contract below describes that earlier slice and is not the current API.

## Purpose and scope

Prove a bounded, deterministic contract for the first idea.md feature before
choosing native storage or hook addresses. Provide 16 forward-playing steps with
note, velocity, gate percentage, probability percentage, conditions, and locks for
Wave, Timbre, Shape, and shared filter cutoff. Values use 0..32767; the four logical
parameter IDs do not yet map to stock IDs.

## Contract

- Pattern storage is at most 256 bytes; player state at most 32 bytes. No heap,
  peripheral access, flash writes, clock source, or audio processing.
- A caller supplies each musical step boundary, base values, and an output event.
  Start resets to step 0, cycle 0 and the given 32-bit seed; Stop prevents events.
- Each boundary advances once, including silent steps. A completed 16-step pass
  increments the cycle. First-cycle means cycle 0; every-N fires on cycles 0, N,
  2N. Previous conditions use the immediately previous actual trigger, including
  across a pattern boundary; a fresh Start has no previous trigger.
- Probability is 0..100%; 0 never fires and 100 always passes probability. One
  LCG draw is consumed per boundary regardless of conditions/rests. Intermediate
  percentages are quantized to the 65,536-value draw grid. Identical seeds and
  edits yield identical events.
- Velocity 0 or gate 0 denotes a rest. A step triggers only if it is not a rest
  and both probability and its condition pass.
- Every event resolves from the current caller-provided base values. Only
  triggered steps apply their locks. Silent or unlocked steps restore base values;
  locks never overwrite the base state or bleed into following steps.
- A single lock can be replaced or removed without affecting others. Accepted
  live edits do not reset the playhead, cycle, seed, or previous-trigger state.
  `fl_resolve` can re-evaluate an active step after editing without advancing time.
- Invalid edits are rejected without changing pattern state. Invalid base values
  reject the tick without advancing transport or modifying the output event.
- Calls are serialized; the API does not promise interrupt-safe concurrent access.

## Non-goals and next slices

This slice emits step-boundary events on desktop. It schedules no gate-off events
and sends no MIDI or native notes. Firmware MIDI-clock integration, OLED controls,
save/load/rollback, copy/paste/undo, more than 16 steps, ratchets, microtiming,
directions, smoothing, and engine switching require subsequent ordered slices.
Do not describe this slice as a playable firmware or a completed FREAKOS 0.1.

## Acceptance and proof

`make test` exercises playback, live editing, removal/restoration, conditions,
deterministic probability, validation, and sustained cycling. `make test-sanitize`
checks memory/undefined behavior; `make check-arm` proves freestanding compilation
only. `make demo` demonstrates changing an upcoming lock during playback and
resolving a current lock without restarting. Target code/RAM placement and cycle
budgets remain unproven until integration and hardware measurement.

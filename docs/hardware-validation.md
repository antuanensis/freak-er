# Target-device validation record

Status: **User reports r2 works. r3 device validation pending.**

On 2026-10-25, the user reported that per-step probability works on the
experimental MFF and that the OLED shows the editor's A/E/P/%/T fields.
This establishes an initial reported feature result, not completion of the
probability matrix or other hardware gates. Exact artifact hash, device setup,
clock, sequence length, duration and save/reboot behavior were not supplied.

The user subsequently reported that first assigning Cutoff (T1), then Resonance
(T2), affected every step when no other snapshots were recorded. Local stock
playback reproduced sparse-value hold beyond the edited step. Revision r2 seeds
new tracks' other steps with baseline values and removes the non-live P display.
At r2, all 39 local Python tests passed, including full-loop baseline restoration in A/B.
The user subsequently reported “It works well” before requesting the r3
operations. Record that as positive r2 feedback, without inventing an artifact
hash or coverage conditions. Existing sparse tracks are not automatically migrated.

r3 adds proportional global/Shift-local edits, all stock-recordable destinations,
Oct hold deletion, Shift+Hold cleanup, Record+Rate+release copying and Preset
first-note editing. It also retires more factory diagnostics and removes the old
position hook. **No r3 device result exists.** Its 53 passing local Python tests
are emulation/tooling evidence only.

Record a dated result per stage, artifact SHA-256, conditions, clock source/BPM,
sequence length, workload and duration. Keep serial/calibration data private.
Use [recovery.md](recovery.md) for preparation and installation order.

| Stage | Required observations | Result |
| --- | --- | --- |
| Official stock | Verified preset/sample backup and restore; recovery demonstrated; audio/MIDI baseline under four voices. | Pending |
| Placement | MCC acceptance, boot, ordinary playing, preset access, return to official stock. | Pending |
| Passthrough | Stock A/B, 4/16/64 steps, notes/chords/ties, Record/Play, all controls, clocks and save/load match baseline. | Pending |
| Probability | 0/100/intermediate values, A/B step 64, one chord decision, rests, repeated loops, edits taking effect next visit. | User reports per-step probability works; detailed cases pending |
| Transport | Start reseeds, Continue retains progression, Stop releases notes/closes editor, rapid Stop/Start, internal/MIDI/USB/analog clocks. | Pending |
| Live controls | Both Shift/Record release orders, Rate selection without moving playback, Shift+Rate clamping, Rate push Sync, Oct/Mod, A/B/preset closure. | Pending |
| Modulation | Existing/new targets, four-track rejection, positive/negative matrix, all active oscillator/sample destinations, repeated relative turns, future/current edits and smoothing. | User reports r2 works; detailed destination/smoothing coverage pending; r3 untested |
| r3 operations | Global curves retain relative differences, saturation/zero/sign behavior, Shift edits one step; all stock destinations including matrix/sample. Oct tap vs 600-ms hold; Shift+Hold only clears locks/probability. Copy across steps 1/64 in A/B, cancellation/release ordering. Preset edits first note only, preserves chord tones/rests. | Pending |
| Preservation | Keyboard/MIDI/arp unaffected; silent steps retain modulation; no stuck notes, parameter jumps or unwanted recording. | Pending |
| Persistence | Save/reboot/load, A/B copy/reload/clear, legacy presets, MCC import/export and stock downgrade/resave/reinstall. | Pending |
| Load/endurance | Extended playback/editing; audio continuity, MIDI timing, stack/interrupt behavior compared with stock. | Pending |

The emulator stubs final voices, queues and some clock interfaces. Its passing
results do not fill any row above. Investigate a failure before proceeding to
another stage; preserve the exact manifest and reproduction conditions.

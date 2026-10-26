# Spec 004: live editor operations

Status: Implemented in experimental r3; local validation passed. Device testing
pending. Extends spec 003.

The user reports r2 working and requests stock destination coverage, per-step
lock removal/cleanup/copy, Shift-scoped edits, and live note changes. Stock still
owns A/B, notes, four modulation tracks, timing and persistence. No additional
sequencer, tracks, conditions or private note/modulation bank is introduced.

## Controls and observable behaviour

- Shift+Record enters/exits while playback is running and recording is off.
- Rate selects the edit step. Shift+Rate changes its probability.
- Hold Shift while turning a parameter to edit only that step. Without Shift,
  scale that parameter's existing locked values across the active pattern
  proportionally to the selected step's old/new values. Preserve absent locks
  and the other pattern. If the reference is zero, or a signed reference crosses
  zero, use a bounded offset instead of division or reversing value ordering.
  Stock byte quantization and saturation apply. A new destination initializes
  all steps together. Sub-byte relative turns retain their selected-value cache.
- Tap Oct/Mod to select an assigned modulation track. Hold it for 600 ms to
  remove that track's lock at the selected step, once per press. Shift does not
  change the long-hold action. Show a dash for an absent lock.
- Shift+Hold removes all four modulation locks from the selected step and resets
  its probability to 100%. Notes, velocity, ties and other steps remain intact.
- Hold Record without Shift, turn Rate to choose a destination, then release
  Record to copy the source step's four lock values/presence flags there. Copy
  does not copy notes or probability, and does not start stock recording. Only
  the active pattern is addressed. A/B, Stop, exit or another edit cancels it.
- Turn Preset in the editor to change the selected step’s first note in semitones.
  Other chord tones, velocities and note flags remain unchanged. Clamp to MIDI
  0..127 (126 when the high-bit flag would otherwise create the 0xFF rest
  sentinel). A rest stays a rest; this gesture cannot create a note.
  Preset press closes the editor and forwards the stock action. Outside the
  editor preset browsing remains stock.
- Matrix selection/amount gestures stay inside the editor. Other stock workflow
  buttons close it. Outside the editor no new gesture is intercepted.

The OLED shows pattern, edit position/length, first note (MIDI number or dash),
probability, selected track and destination/value. Copy has no extra indicator.
There is no non-live playback-position display.

## Parameter contract

Use every destination stock marks recordable: the exact input exposes 57 IDs,
including oscillator/sample controls and all 35 matrix amounts. Do not substitute
a short whitelist. Keep the four-destination limit and full-track rejection.
Stock-ineligible Utility/button/Shift-only destinations remain ineligible.
Verify physical dispatcher paths as well as direct capture. Signed matrix
amounts retain raw >> 8 conversion; other snapshots retain raw >> 7.

## Step operations

Deleting a lock clears its presence bit, preserving other track bits and note
data. Copy replaces destination lock presence/values with the source's; it does
not allocate new targets. Cleanup resets probability without changing the cached
decision for the current visit. These operations mark the stock pattern dirty.
Preserve stock sparse-value hold and smoothing; clearing a lock does not add a
hidden restoring lock. Step pitch changes take effect on the next stock visit,
without moving playback or interrupting a currently sounding note.

## Acceptance

Test all 57 eligible IDs against actual stock recorder allocation/conversion and
ineligible passthrough. Exercise global/Shift scopes, signed amounts, existing
tracks and full capacity. Test short/long Oct gestures at threshold and timer
wrap, release ordering, invalid/empty selection, and context cancellation. Check
cleanup and copy at step 64 in both A/B with notes/metadata/other steps preserved.
Check pitch bounds, untouched additional chord tones, flags, rests, velocities and cursor/RNG
invariance. Run native tests, nearest tooling/integration gates, lint, staged
MFF verification and independent artifact rebuilds. Hardware results for r2 do
not validate the new revision; record new user results separately.

## Capacity decision

The r3 native image occupies 3,778 of 3,809 audited bytes, with twelve runtime
bytes. It reuses stock sequence records and target assignment, and replaces the
older cloned recorder/position hook with a narrow recorder-parity-tested adapter.
Eight unused factory diagnostic commands are retired; boot audio/conf/filter/ioc
and the bootloader remain untouched. Whole-function packing uses actual ELF
alignment. No additional bank, heap, clipboard storage, chord transposition mode
or copy indicator is added. Further features require measured code savings or
new independently proven space; 31 bytes is not a useful feature budget.

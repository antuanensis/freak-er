# Stock sequencer findings

Date: 2026-10-23. Derived from the exact official 5.0.0.2084 update under Unicorn.
These are single-function/synthetic-RAM probes, not a booted full-system test or
device measurements. No proprietary instructions or data dumps are reproduced.

## Reproduced functions and fields

| Function | Observed behavior |
| --- | --- |
| `0x08028014(object, length)` | Writes the shared length to A and B. Tested with 4, 16 and 64. UI validation is separate; do not assume this low-level setter rejects invalid lengths. |
| `0x080281F8(object)` | Advances the shared step cursor and wraps at selected pattern's length. Returns new position. It is not a read-only getter. |
| `0x0802821C(object)` | Reads shared step position without advancing it. |
| `0x08028244(object, position)` | Sets the shared cursor. |
| `0x0802906C(engine)` | Existing trigger predicate; behavior depends on mode and current step flags. A rest flag returns false; flags 1 and 3 both pass in mode 3. It does not alone identify a new note-on dispatch. |
| `0x08027FB4(object, track)` / `0x08027FCC(object, track, id)` | Read/write the selected pattern's existing modulation target ID. Tested all four tracks independently in A/B. These low-level accessors do not prove a target is eligible. |
| `0x08028074(object, step, track)` / `0x08028104(object, step, track, byte)` | Read/write the stock modulation byte. Setter also changes pattern metadata; the higher-level native recorder is documented separately below. Tested at step 64 without advancing the cursor or altering notes/velocities. |
| `0x08028090(object, step, track)` / `0x08028128(object, step, track, enabled)` | Read/write per-step modulation presence. Verified that enabling one lane exposes its recorded value without changing the cursor. |

Observed sequence-object offsets: `+0x02` selects A/B, length bytes are `+0x40D`
and `+0x81F`, and shared cursor is `+0x828`. Pattern stride is `0x412`. In the
synthetic engine used for probes, `engine+0x08` points to the sequence object and
mode byte `engine+0x1C = 3` takes a sequencer path without Spice processing.

These offsets are evidence about the exact official version, not permission to
write arbitrary native memory. Emulation objects at `0x20008000`/`0x20009000` are
test allocations only; those addresses are not free native RAM.

## Executable proof

`make stock-test` runs four checks against the official image:

1. Both patterns share length and traverse complete stock cycles at 4, 16, and 64
   steps; repeated reads do not advance position.
2. The stock trigger predicate accepts both ordinary and tie-like nonzero flags;
   this prevents treating the predicate alone as a safe new-note hook.
3. The compiled C probability extension follows real stock cursor callbacks for
   A/B at 64 steps. A/64 at 0% is suppressed while B/64 at default 100% passes;
   rests remain rests. Repeated queries do not advance playback or change note
   records. This is a host-mediated integration model, not a native binary hook.
4. Existing target/value/presence accessors edit all four lanes at step 64 for A/B
   independently while retaining a different playback position. This verifies
   stock storage access, not native UI event capture, full-track allocation, or
   the conversion from signed/unsigned parameter values to recorded bytes.

## Subsequent native implementation

The user-supplied manual confirms four pattern-wide modulation targets and both
step snapshots and one-loop real-time modulation recording. The required new
behavior is editing a selected step while stock playback continues. Reusing stock
step-record mode indiscriminately would change Record/transport state and is not
an acceptable implementation.

The 2026-10-27 native adapter now connects the boundary, note-controller,
recorder, raw-value reads, controls, OLED and persistence paths. Its separate
27-test suite exercises those native hooks and real stock routines. See
[native integration](native-integration.md) for addresses, memory/ABI contracts,
corrections to early assumptions and exact coverage.

The table/probes above describe the original investigation, not the complete
current test suite. They remain useful low-level contracts. Hardware, MCC round
trips, audio/MIDI timing, complete oscillator/sample UI and interrupt behavior
remain untested; see [device validation](hardware-validation.md). The historical
upstream Release baseline still contains neither sequencer addition.

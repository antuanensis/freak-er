# Session memory

## Checkpoint status

The initial Git checkpoint contains r3 source and documented r2 history; see
[revision records](revisions.md) for all six artifact fingerprints, sizes and
build commands. It does not reconstruct a historical r2 source commit.
Shrinking and future feature implementation have not started. Only read-only
inspection, unchanged-source compiler experiments and baseline tests preceded
this checkpoint; native source and builder still match the r3 manifest hashes.
The next development change must be a separate behavior-preserving size pass.
No remote setup, push, publication or device operation is included.

## Current objective and result

Extend the stock-only MicroFreak sequencer: probability, stock modulation locks,
proportional global/Shift-local editing, lock deletion/cleanup/copy and live
first-note editing. A/B, shared 4..64-step length, four tracks, transport, smoothing
and persistence stay stock-owned. Active contract: [spec 004](specs/004-live-editor-operations.md),
extending spec 003. The broader idea.md remains deferred.

**Experimental r3 is implemented, locally tested and built. No r3 device result.**
The user reported probability working, then r2 “works well,” before requesting
these additions. Exact device hashes/conditions were not supplied. Do not invent
coverage or close the full hardware/MCC/timing gates from that report.

The latest concern was code capacity. r3 fits **3,778 / 3,809 audited bytes**, with
**31 bytes remaining** and unchanged **twelve-byte runtime state**. Eight unused
factory diagnostics plus an oled-only helper provide space. Diagnostic boot is
not the bootloader; normal boot audio/conf/filter/ioc remain intact. No extra
bank, heap or flash writer. More features require measured savings or newly
proven placement; do not promise the original idea.md will fit.

## Implemented controls

During stock sequencer playback, recording off:

- Shift+Record enters/exits; Rate selects E; Shift+Rate sets probability 0..100.
- Unshifted parameter turns scale present values across active pattern
  proportionally. Missing locks/other pattern stay unchanged. Zero/sign-changing
  references use bounded additive fallback; byte clipping/quantization apply.
- Shift+parameter changes E only. A new local target seeds other cells with the
  original value; a new global target initializes all cells to the new value.
- Tap Oct/Mod cycles assigned tracks; hold 600 ms clears selected track at E,
  Shift optional. Release after a long hold does not cycle.
- Shift+Hold clears four locks and resets probability at E, keeping notes.
- Hold Record without Shift, turn Rate from source to destination, release Record
  copies four values/presence bits, not notes/probability. Exit/context/another
  edit cancels; Record never starts recording through this editor gesture.
- Preset turns edit the first existing note by semitones. Other chord tones,
  velocities and flags stay intact. Rests stay rests; flagged notes cap at 126 to
  avoid 0xFF. No chord transposition, octave mode or note creation.
- Matrix selection stays in editor; other workflow buttons close/forward stock.
  Preset push closes; Rate push remains Sync. Outside editing controls stay stock.

OLED: `A E12/64 N60`, `%75 T1`, destination/value. N-/T-/value dash mean rest,
no track, absent lock respectively. TFULL means all four targets assigned.
Values are stock snapshot bytes (signed matrix); no P or copy indicator. Delete
retains stock sparse hold, so a preceding lock can carry through a cleared step.
Only new eligible note-ons are probabilistic; ties/releases/modulation/arp and
keyboard/MIDI retain stock behavior. Start seeds 42; Continue retains progression.

## Native contracts and changed architecture

See [native integration](native-integration.md), [ADR 0003](adr/0003-native-sequence-metadata.md)
and [ADR 0004](adr/0004-bounded-live-editor.md).

- State at 0x2001C9D8 uses twelve unused CC-pointer-table bytes; stock group count 20.
  PRNG/allowed/close_pending are volatile interrupt-owned; UI fields main-loop
  serialized. Packed scope/value also hold Oct timestamp/copy source when idle.
- Probability uses record bytes 14/15, 0..100/tag 0xD3. Validate all 64 and stock
  nonempty marker; legacy/partial invalid defaults to 100%. Stock serializer owns it.
- r3 replaces the temporary 148-byte cloned recorder with a narrow native adapter
  reusing target setter 0x08027FCC and proven record/cache/LED fields. All 57
  eligible IDs compare against actual stock recorder 0x08026DB8. Stock metadata
  sets eligibility; four-target rejection retained. Ordinary raw>>7, matrix>>8;
  stock baseline cache is byte(raw>>7) even for matrix.
- Position 0x0802821C and output 0x0802682C are now **unhooked**. The old position
  shim affected preceding-step interpolation; playback now matches untouched stock
  with identical RAM/records, A/B/all 64 steps/three phases.
- Raw/scaled getters remain panel-scoped; fine raw cache supports relative edits.
  Inline encoder hook 0x0802C480 preserves registers/LR/APSR except intended r6.
  Type editable scaling uses a local read-only view; model context stays global.
  Never swap global values/table pointers to fake a future edit.
- Pot Shift is consumed only inside editing, making Shift a local-edit modifier.
  Outside editing stock Shift alternate destinations remain intact.
- Ten proven regions: append, retired codec/synth/gpio/flag/sync/oled/boot/cvout,
  and oled-only helper. Every build checks static references. Actual 2/4-byte ELF
  alignment, bounded deterministic whole-function packing and word-aligned Parts.
  No function splitting, arbitrary space or checksum/bootloader/calibration edits.

## Artifacts (local and ignored)

Built from exact official input; all three independently rebuilt byte-identically,
with every JSON manifest field compared. Stock version display remains unchanged.

| Stage | File under build/ | SHA-256 |
| --- | --- | --- |
| Placement, no hooks | freak-er-placement-r3.mff | 7d164208abb9987dfac71d55cf1b1f4182c29a6bec601b67eaa684d418bac8a1 |
| Passthrough | freak-er-passthrough-r3.mff | f05ab47156636e9b84243733b8dd8bec44ff3809046f674e22fec63c70156157 |
| Features | freak-er-stock-sequencer-experimental-r3.mff | 313d7a485b2753bdde07be12aef7f34f34962643443cf82c48162b89853a0dbb |

Feature/placement code 3,778; passthrough 1,358; runtime 12 in every stage.
Working r2 images/manifests preserved; their previous SHA-256 values rechecked:
placement ca9b80d06912fa3ddc317cb6ff3043cfb715b34ef9952365204185aebd89063b,
passthrough fe9c7a81ad4a1b6d9ecff1fcd4790147be84b1f9db5b6ad916016698881e0d33,
features d7cfe1fdb83f6dc7b57b8e6c79add83bb187e8f1b80b2754f762cc44325a5abb.
The older upstream-release.mff contains neither requested sequencer addition.

## Validation

- 53 local Python tests passed, no skips: 39 native, 10 tooling, 4 stock/model.
- Includes all 57 recorder parity, actual pot/Type/LFO/matrix paths, global/local
  curves, timer threshold/wrap, cleanup/copy/release cancellation, first-note
  bounds/rest/flag/velocity preservation, untouched-stock playback, metadata,
  ABI/register/APSR and staged code placement/alignment/overflow verification.
- Three r3 artifact rebuilds and full manifests matched; r2 hashes unchanged.
- Six C groups, ASan/UBSan, demo, ARM reference compilation and Ruff lint/format
  were rerun successfully. Reference/core and vendored sources are unchanged. Current command results
  and practical limits: [testing](testing.md).
- Unchanged upstream previously passed 303 tests; not rerun for r3.

Synthetic timers and hardware queues/final voices are stubbed. No full boot,
audio rendering, USB interrupts, complete oscillator/sample initialization, MCC
round trips, stack/timing or endurance proof. No assistant flash occurred.

## Next action

Finish at a clean r2/r3 Git checkpoint. Begin size optimization separately,
preserving every r3 feature and existing storage/ABI contracts. Current planning
leads are direct branches to known stock functions and measured helper reuse;
compiler-only flags yielded no savings. Do not add features during the shrink.

Later priorities are AFX-style key recall (four shared continuous targets in an
optional preset mode reusing sequence storage), Brownian as an existing-LFO mode,
two-state matrix-depth morphing with manual/automatic position control, Euclidean
arp rhythm then root/scale-based harmony, independent Decay/Release through reused
upstream work, and expanded per-voice digital modulation. Separate feature builds
are acceptable if measured budgets require them; these are research priorities,
not implemented or guaranteed to fit together. Full AFX engine/sample switching
and broad patch morphing remain deferred.

Device gates remain independent. Follow [recovery](recovery.md) and record new r3
placement, passthrough then feature evidence in [hardware validation](hardware-validation.md).
r2 success cannot validate r3's additional placements/hooks. Keep official recovery
and all verified local r2/r3 artifacts. Do not flash, publish or push as part of
this checkpoint.

## Environment and preservation

Official input: original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff,
SHA-256 c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c.
Pinned vendor revision 083b15cabde98fc31eb89b40562aeeea38224968; seventy source files
match the untouched sibling ThisFirmwareDoesNotExist checkout.
Use vendor/ThisFirmwareDoesNotExist/.venv/bin/python for integration. Sandboxed
Unicorn crashes because hw.cachelinesize is denied; tests need normal host access.
Private Ghidra/decompilation/probes and r2 source snapshot stay ignored under
build/. Never print/distribute proprietary firmware, fragments or dumps. The
manual and .vscode settings remain local and ignored; see [input setup](local-inputs.md).
idea.md and the unchanged attributed vendor snapshot are included in the source
checkpoint. The user will create the remote separately. No publication or device
operation is included.

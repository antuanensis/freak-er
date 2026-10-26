# Native integration evidence

Evidence: r3 integration 2026-10-25; r4 size pass 2026-10-26. Input: official MicroFreak 5.0.0.2084, SHA-256
`c2b405e3c8565b7b73b4dd06522559458190082a8ba633cc5f1bcc43dc64332c`.
Implementation evidence here comes from static dataflow analysis and Unicorn
execution. User-reported probability and r2 operation are recorded
separately in hardware-validation.md. Private analysis remains in ignored
`build/`; no stock listings or firmware fragments are distributed.

## Hooks and ABI

| Site | Purpose and contract |
| --- | --- |
| `0x0801103C` | Replace the constructor's final call to `0x0800E730`; forward arguments, then initialize twelve unused runtime bytes. Stock group count stays 20 and constructor output otherwise matches stock in emulation. |
| `0x08029112` | Replace the real cursor-advance call to `0x080281F8`. Advance exactly once, preserve return position, then draw probability in engine modes 2/3. Stock also advances its shared cursor in arp mode; retain that behavior without drawing. |
| `0x08048524` | Note-controller entry, six arguments. Filter only source 5, status 0x90, positive velocity, transport running. Forward other events and all arguments unchanged. Tests check stack arguments and restoration. |
| `0x0802880C` | Transport: 1/4 Start, 3/5 Continue, 0/2 Stop. Preserve original execution. Stop sets pending UI closure, including when Start follows before the next main-loop poll. |
| `0x08023C9C` | Panel-aware setter. Stock flag byte 1 bit 0x40 determines recordability; stock group/index bounds remain enforced. Return stock's consumed result 3 after capture. |
| `0x08023C2C` | Equivalent raw getter, with selected-value reads only during panel scope and stock UI callers. Recorder/MIDI/audio callers retain global values. |
| `0x0802C480` | Generic incrementer's inlined signed read. The shim writes r6 only, preserves every other register and APSR including comparison flags, and rejoins at `0x0802C484`. Tests verify this contract. |
| `0x08040D82`, `0x08040DFC` | Sample/Type editable-value calls to stock scaler `0x0800E644`. Supply the selected raw value through a local read-only 144-byte parameter view, retaining stock metadata and scaling. The active-model context read at `0x08040B9E` remains global. |
| `0x08027F48`, `0x080284F0`, `0x08028264` | Pattern clear, sequence load and built-in installation. Invalidate metadata appropriately while preserving stock behavior. Invalid built-in indexes remain no-ops. |
| `0x08074C44`, `0x08074C48` | Button press/release vtable words. Consume Shift+Record only during playback with recording off. Remember consumed Record until release, even if Shift releases first. |
| `0x08074C54`, `0x08074C70` | Pot/encoder vtable words. Scope real stock dispatch, including helpers and tail calls. Physical Rate is 0x403; 0x402 is its alternate. Preset encoder 0x800 edits the first note inside the editor. Outside it, browsing remains stock. |
| `0x0803A824` | Main-loop poll call to `0x08039DA4`. Preserve its result; close/repost editor according to transport, recording, pattern and length; poll the 600-ms Oct hold using stock HAL tick at 0x2001E1D8. |
| `0x08052F1C` | Request-0x700 drawing case. Preserve live callee-saved registers, use stock's four-byte text messages and rejoin `0x08052C2E`. |

Entry trampolines replay the audited first four bytes and branch to entry + 4.
The builder accepts only the identified PUSH/MOVW/PUSH+ADD forms. Position getter
`0x0802821C` and set-and-send `0x0802682C` are unhooked in r3. Input identity, call/vtable targets and the
inline encoder load's register contract are checked before building.

r4 declares typed stock functions against undefined `.abs` symbols, backed by
absolute `.equ` addresses. The pinned linker resolves direct Thumb calls and
inline return branches after placement, using its existing relocation support.
Targets and calling conventions are the same as r3; literal-loaded function
pointers are removed. No new stock hook is added. The scaling loop is kept
out of the capture caller to reduce spills and total code. All 39 native
scenarios compare identically against committed r3 state/messages, with no
per-operation observed stack increase; see [size evidence](size-pass.md).

## Stock ownership and live writing

Sequence object: `0x20000EEC`; modulation manager: `0x20000E30`.
UI state: `0x20003704`; engine: `0x20003AA8`; transport: `0x20003A64`.
UI transport state 2 is playback; 3/4 are recording paths. Entry/capture requires
both transport running and that playback state.

Stock recorder `0x08026DB8` is the parity oracle, not called through a cloned
object in r3. Stock setter metadata determines eligibility (57 IDs), group/index
bounds stay enforced, and `0x08027FCC` assigns the selected existing/free target.
The narrow adapter writes the same stock record fields and recorder caches.
Tests compare target assignment, selected value, baseline structure and LED state
against the actual recorder for every eligible ID, including negative matrix
amounts. Full four-track capacity rejects a fifth destination.

Step records use notes 0..3, velocities 4..7, modulation values 8..11 and presence
bits 0..3 in byte 13. Target IDs are at pattern +0x400..0x407; +0x410 is the dirty
marker. Ordinary snapshots use raw >> 7; matrix IDs use raw >> 8. Stock's baseline
cache is the byte `(uint8_t)(raw >> 7)`, including matrix amounts; the actual
matrix baseline snapshot separately uses raw >> 8. Assignment, baseline/current
values, interpolation endpoints and track LED state remain stock-compatible.

A Shift/local edit changes only E. New targets seed all other 63 cells with the
original parameter value, preventing stock sparse hold from spreading the edit.
An unshifted/global edit scales existing present cells using selected old/new
values, preserving gaps and the other pattern; a new target initializes all 64
cells to the new value. Zero-reference or signed sign changes use a bounded
additive offset. Native integer division and byte saturation apply. Current-step
local edits and global edits update normal output and active endpoints; a future
local edit leaves current output untouched. The next boundary resumes stock
smoothing. Existing sparse tracks are not automatically repaired.

The previous r2 position-getter replacement clobbered r1/r2, which the stock
getter preserves, changing the stock caller’s preceding-step interpolation. r3 removes
that replacement and output suppression entirely. Playback is compared with
untouched stock using identical RAM/records over both patterns, all 64 positions
and three interpolation phases. The signed -1 position sentinel remains stock.

Oct tap selects a track; a 600-ms hold clears its presence bit at E. Shift+Hold
clears all four bits and sets probability 100. Record+Rate+release copies the
four values and presence bits within the same pattern, without notes/probability
or target allocation. Preset edits only the first note, preserving its flag,
additional chord tones and velocities. A rest stays a rest. Pitch is clamped to
avoid turning a flagged note into the 0xFF rest sentinel. These record edits mark
the pattern dirty and apply on its next stock visit. Deletion keeps sparse hold;
it never adds a restoring lock.

OLED shows pattern, E/length, N first note, probability, selected track and
stored destination/value. Absent notes/locks use a dash. P remains removed;
copy has no extra indicator. All 57 parameter names were checked to terminate inside their twelve-byte
stock table slots, bounding the 64-byte display buffer.
Pot Shift is consumed as the single-step modifier inside the editor; outside
editing the stock alternate destination remains intact. Matrix selection stays
inside editing; other workflow buttons close it and forward stock action.

Relative controls need scoped reads too; setter capture alone stalls increments
against an unchanged global value. One cached raw value retains precision while
turning the same control. Moving edit cursor invalidates that cache. No global
value/pointer is temporarily swapped, and no interrupts are disabled around
stock queue calls.

Discrete Type/sample controls use stock's metadata-based scaler rather than the
raw getter. Only their editable-value calls receive the selected snapshot;
active-model context continues to use the global value so future Type edits do
not switch the current model's UI context or imply that its assets were loaded.
The real Type encoder is exercised repeatedly in emulation. Complete sample and
oscillator initialization still requires device testing.

## Persistent metadata

Each A/B pattern is 0x412 bytes, including 64 sixteen-byte step records. Stock
note/velocity/modulation/presence fields occupy bytes 0..13. Reviewed accessors
and the note-copy writer leave bytes 14/15 untouched; tests exercise both
patterns and every step. Full sequence serialization, load and A/B copy transfer
these bytes along with the rest of the pattern.

The experiment uses byte 14 for probability 0..100 and byte 15 for tag 0xD3.
Recognize a pattern only when all 64 tags/values validate and stock's marker is
nonempty. Invalid/legacy metadata means 100% everywhere. First edit initializes
all records together and marks the pattern dirty. Clear/load/built-in hooks
prevent stale metadata after resets; inlined clears are also invalidated by
stock's empty marker.

Serializer `0x080284BC` copies both patterns (0x824 bytes) into the existing
preset component. Loader `0x080284F0` accepts both/single-pattern reloads. Copy
`0x0802824C` transfers a full pattern. These real paths are tested without
growing the preset stream or adding flash calls. MCC import/export may transform
padding; application round-trip preservation remains untested. See
[ADR 0003](adr/0003-native-sequence-metadata.md).

## RAM and code ownership

Runtime state uses `0x2001C9D8..0x2001C9E3`: three unused CC-table pointer slots
for groups 21..23. Stock registers twenty groups; this patch adds none. The
host reference's 144-byte state is not allocated on device. Twelve bytes hold
PRNG, UI flags/track, packed step/pattern/scope, separate decision/close-pending bytes,
last parameter and raw encoder value. Only random/decision/close-pending are
interrupt-owned volatile members; the UI fields are main-loop serialized. The
scope/value fields also encode a pending Oct timestamp (low 15-bit HAL tick) or
copy source (bit 15 plus six-bit source index) when panel dispatch is inactive.
Another edit/exit cancels gestures and invalidates the raw cache. No clipboard
bank is allocated.

Whole functions are packed deterministically into proven regions:

| Region | Ownership |
| --- | --- |
| `0x0807FA60..0x0807FFFE` | Appended main-image window; checksum byte excluded. |
| `0x0802BE90..0x0802C131` | Retired factory `codec`; slot `0x08074094`. |
| `0x0802CA94..0x0802CC03` | Retired factory `synth`; slot `0x080740D4`. |
| `0x0802C2F4..0x0802C3E1` | Retired factory `gpio` prefix; slot `0x08073FF4`. |
| `0x0802D44C..0x0802D52F` | Retired factory `flag`; slot `0x080740B4`. |
| `0x0802BB60..0x0802BBFF` | Retired factory `sync`; slot `0x08074054`. |
| `0x0802BC00..0x0802BC83` | Retired factory `oled`; slot `0x08074034`. |
| `0x0802BC84..0x0802BD0F` | Retired factory diagnostic `boot`; slot `0x08073FD4`, not the bootloader. |
| `0x0802BD94..0x0802BE8F` | Retired factory `cvout`; slot `0x08074134`. |
| `0x0802EE74..0x0802EF25` | Helper called only by retired `oled`. |

Those eight factory commands become stock no-ops. Normal boot's
audio/conf/filter/ioc commands remain present. Every build reruns raw reference
scans. Known scanner noise at `0x0802BE40`, `0x0802C154` and `0x0802B7B2` comes
from instruction decoding, not live references. The helper has two live callers,
`0x0802BC42`/`0x0802BC6C`, both inside retired oled. Private Ghidra inspection
confirms its apparent branch reference at `0x0802E92C` is data and its apparent
literal reference at `0x0802EB16` is a Thumb-32 second halfword. The preceding
function terminates at `0x0802EE37`, with no fall-through. Ownership also follows
pinned upstream's [free-space evidence](../vendor/ThisFirmwareDoesNotExist/docs/free-space-and-dead-code.md).

Total capacity is **3,809 bytes**; r4 feature/placement code uses **3,662**, leaving
**147 bytes** (r3 used 3,778, leaving 31). Runtime remains twelve bytes. A deterministic bounded exact packer
uses each executable ELF section's actual 2/4-byte alignment, placing word-aligned
sections first. Whole functions are never split; literal pools stay aligned.
Sections are merged into word-aligned per-region Parts for upstream verification.
A second compiler pass must emit identical bytes. Overflow, search exhaustion,
misalignment, unaudited references and unsupported relocations fail the build.
Manifests record capacity, section alignment, compiler arguments, compiler stack
frames, per-region used/free bytes and hashes. Naked assembly pushes and stock
callees are excluded from compiler frame figures; emulator instrumentation checks
actual exercised stack paths separately. MFF checksums and bounds
use upstream verification. Bootloader, calibration and separate OLED images are
not patched. See [ADR 0004](adr/0004-bounded-live-editor.md).

## Limits

Unicorn uses isolated stock contexts, synthetic timers and stubs for queues,
downstream voices and selected timing interfaces. Internal flash/controller
writes are trapped. Tests do not reproduce USB interrupts, physical OLED,
complete oscillator/sample UI initialization, audio rendering, MCC round trips
or endurance. Hardware stack/timing margins and every external clock mode still
need staged measurements on the target unit.

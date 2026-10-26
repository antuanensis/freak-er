# Architecture

Stock owns the only sequencer: A/B, shared 4..64-step length, notes/chords,
clock, gate scheduling, ties/rests and four assignable modulation tracks. This
milestone adds per-step probability and live editing of those existing tracks.
Conditional triggers, extra tracks and another playback engine are excluded.

## Native implementation

`native/stock_sequencer.c` is a freestanding Cortex-M4 adapter for exactly
5.0.0.2084. Its twelve runtime bytes occupy unused parameter-table slots. The
probabilities live in versioned metadata in stock's existing sequence records;
there is no second note/modulation bank or independent playhead.

The stock boundary call advances once, then the adapter draws once and caches
its decision. Only positive-velocity sequencer note-ons are filtered. Stock
continues to process modulation, note-offs, keyboard/MIDI and arp normally.
Start resets seed 42; Continue retains progression; Stop invalidates the decision
and schedules editor closure in the main loop.

Panel dispatch scopes the editor. Stock handles parameter eligibility and knob
behavior. Relative controls read the selected snapshot through scoped getters;
a raw-value cache retains increments below the snapshot's eight-bit resolution.
Recorder base reads, incoming MIDI and unrelated queries see stock values.
Discrete editable values retain stock metadata-based scaling through a local
read-only parameter view; active oscillator-model context stays global.

A narrow adapter reuses stock target assignment and record fields, with parity
against all 57 stock-recordable IDs. It leaves the stock position getter and
set-and-send unhooked. There is no cloned recorder, temporary cursor change or
second parameter bank. Shift changes one step; unshifted edits scale the active
pattern’s existing values proportionally, with bounded zero/sign-change fallback.
New local tracks seed other steps with baseline values; new global tracks use the
new value throughout. Existing gaps stay absent. Stock smoothing is retained.

Deletion, cleanup and copy change existing presence/value/metadata fields.
Record-held copy stores only a source index, reusing twelve-byte runtime state.
Preset changes only the first note, leaving rests and other chord tones intact.
See [spec 004](specs/004-live-editor-operations.md) for precise controls and limits.

The OLED editor uses stock request 0x700 and its text widget. All new screen
messages run in control/main-loop context. No interrupt masking, flash writer,
heap allocation, bootloader change or calibration change is added.

## Build and reference model

`tools/native.py` reuses the pinned upstream ELF assembler/linker, reference
scanner and patch verifier. It checks the official input, hook targets, displaced
instruction forms and retired-region references. Trampoline fragments come from
the user's official file during building. Generated firmware stays ignored. r3 packs whole functions by actual ELF alignment
into 3,809 proven bytes: append space, eight retired factory diagnostic commands
and an oled-only helper. r4 code uses 3,662 bytes, 116 fewer than r3, by direct stock calls and selective
scaling-loop extraction. All behavior is preserved; further features still need
measured savings or new placement evidence. Normal boot initialization stays intact.

`tools/firmware.py build` creates placement, passthrough or feature experiments
and a manifest recording hashes, compiler, region placement and stage. Existing
outputs are never replaced. Manifests also record executable compiler arguments,
compiler stack frames and per-region occupancy. The Python-only `source` option
can rebuild the committed r3 reference for equivalence tests. The separate `baseline` command still reproduces
upstream Release only; that patch is not included in these sequencer builds.

`core/freaklocks.c` remains the portable behavioral model, with a 144-byte host
state and raw edit requests. It is not linked into the native image. Its table
is a reference representation, not an additional device allocation.

## Evidence and limits

[Native integration](native-integration.md) records addresses, storage and ABI
contracts. `make native-test` runs the actual adapter and stock routines under
Unicorn, including native boundary, transport, recorder, relative editing,
smoothing and persistence paths. Peripheral queues and the final voice engine
are stubbed; this is not a full-system boot or hardware validation.

Device boot acceptance, real audio/MIDI timing, interrupt behavior, physical
controls, oscillator/sample-specific UI and MIDI Control Center round trips
remain release gates. Follow [recovery.md](recovery.md) in stage order. Presence
of a generated MFF never proves those gates passed.

# Testing

## Commands

```sh
make test
make test-sanitize
make check-arm
make setup
make native-test
make stock-test
make lint
FREAKPATCH_STOCK_MFF="$PWD/original_firmware/MicroFreak_Firmware_Update_5_0_0_2084.mff" make upstream-test
```

The default `make test` runs six C behavior groups and ten firmware-tool tests.
Native/stock emulation tests skip under Python without Unicorn; those skips are
not integration proof. `make setup` installs pinned development dependencies
using the unchanged vendored lockfile with `--frozen`.

## Coverage

The reference C suite covers 100,000 seeded boundaries, externally supplied
4..64-step A/B positions, cached probability, transport, editor selection and raw
signed edit requests. Sanitizers cover this host model. Cortex-M4 compilation of
the model is separate from native firmware linkage.

Ten firmware-tool tests cover strict official identity, deterministic upstream
baseline reproduction, exclusive atomic publication/symlink protection and native
CLI manifest hashes/overwrite refusal, exact section packing and overflow rejection. Existing wrong firmware fails rather
than silently skipping. Local suites default to `original_firmware/`; set
`FREAKPATCH_STOCK_MFF` for another local path and explicitly for upstream tests.

Four original stock tests combine stock functions with the host C model. The
39 tests in `test_native.py` additionally build/install the actual native adapter
into an emulated main image and cover:

- Constructor equivalence apart from twelve reserved bytes; stock group count 20.
- Actual stock boundary hook, one draw per visit, A/B grid and arp exclusion.
- Six-argument note ABI, note-off/velocity-zero/other-source passthrough, real
  stock chord/tie dispatch and actual Start/Continue/Stop paths.
- Recorder conversion, four-track allocation/rejection, independent edit cursor,
  current/future output and real stock interpolation across controlled phases.
- Real pot/vtable dispatch, repeated relative encoder increments, scoped selected
  reads, incoming control passthrough and raw cache invalidation.
- Repeated discrete Type encoder changes through stock scaling, while active
  model context and the global Type value remain unchanged for future edits.
- New Cutoff/Resonance tracks: baseline cells on all 64 steps in both A/B, real
  pot dispatch and a full playback loop returning to baseline after the edit.
  Notes, probability metadata and the other pattern remain unchanged. Existing
  sparse tracks retain their other cells even with an uninitialized playback cache.
- All 57 eligible IDs compared with the actual stock recorder for assignment,
  snapshot conversion, baseline structure and LEDs; no short destination whitelist.
- Actual LFO and matrix amount encoder dispatch, plus Shift-pot scope with stock
  alternate behavior preserved outside the editor.
- Proportional global scaling, signed values, zero fallback, byte limits and
  missing-lock/other-pattern preservation.
- Oct tap vs long hold at 599/600 ms and timer wrap; cleanup and Record-held copy
  at step 64 in both A/B, with notes/probability preservation and cancellation.
- First-note pitch bounds, flags/rests, untouched chord tones/velocities and
  cursor/RNG invariance.
- Playback compared with untouched stock using identical RAM and sequence records
  over A/B, every step and three interpolation phases. The old r2 position shim
  is removed; smoothing stays stock-owned.
- OLED E/length/N/probability/track/absent-lock display, no stale P; decimal
  formatting covers every value 0..255.
- Inline encoder hook preserving all other registers, stack, APSR flags and
  signedness; stock position getter remains unhooked, including the -1 sentinel.
- Button edge ordering, physical Rate ID, recording exclusion and OLED chunks.
- Full serialization/load, A/B copy, single-pattern reload, legacy/empty/partial
  metadata defaults, built-in resets and note/modulation metadata preservation.
- Placement/passthrough stages, reference scans, ELF alignment/nonoverlap/capacity,
  word-aligned region Parts and traps on emulated internal flash/controller writes.

Current local result: **54 Python tests passed, no skips**: 39 native adapter
tests, one r3/r4 equivalence test, ten tooling and four stock/model tests. The
comparison executes all 39 native scenarios on both versions, checking sequence,
modulation/runtime state, all parameter values, captured OLED/page/close messages
and per-operation observed stack bounds. It rebuilds the pinned original source
from Git commit 6a5c412; keep that commit available in development clones. Missing
Git history, official input or Unicorn causes an explicit skip, not a pass.
`make native-test` includes both native test modules. Derived metrics stay in
ignored `build/r4-equivalence.json`; no RAM/firmware dumps are committed.

r4 feature/placement code is 3,662 of 3,809 bytes, 116 fewer than r3; passthrough
is 1,288. Runtime remains twelve bytes. Maximum observed scenario stack is 308
versus r3's 324, with no individual operation increase. Compiler frame figures
exclude stock callees and naked-function pushes; they are not stack-depth proof.
Construction and hardware interrupts are outside these scenario measurements.
See [size evidence](size-pass.md) for exact limits and rejected candidates.

All three r4 artifacts independently rebuilt byte-for-byte, with every manifest
field matching. All six r2/r3 artifact fingerprints were rechecked unchanged.
Six reference C groups, ASan/UBSan, demo, Cortex-M4 reference compilation and
Ruff lint/format passed at the checkpoint; core/reference source is unchanged.
Ruff lint/format passed again for r4. The unchanged upstream previously passed
303 tests and was not rerun for the size pass.

The build also rejects unresolved/unsupported ELF relocations and unaudited
prologue forms. Upstream's MFF verifier checks image edits, bounds, alignment and
checksums. Upstream source and its own 303-test suite remain unchanged.

## Limits

Native tests use synthetic timer/control contexts and stub hardware queues,
selected clock getters and final voice notifications. They do not emulate a
complete device boot, audio output, USB interrupts, physical display/buttons,
every oscillator/sample UI initialization, MCC transformations or extended load.
Recorded values use stock’s eight-bit resolution; immediate local edits may
retain finer raw output until the next stock event. Passing tests does not establish device timing or safety.

On this Apple Silicon host, sandboxed Unicorn initialization crashes in
`init_cache_info` because access to `hw.cachelinesize` is denied. Identical tests
pass outside the sandbox. Use normal host test access rather than weakening
validation or patch code. Follow [hardware validation](hardware-validation.md)
and [recovery](recovery.md) before release claims.

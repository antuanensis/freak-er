# r4 sequencer size pass

Status: locally implemented and validated; no r4 device result. Date: 2026-10-26.
Behavior contract remains [spec 004](specs/004-live-editor-operations.md); size
acceptance is [spec 005](specs/005-sequencer-size-pass.md).

## Result

| Measurement | r3 | r4 |
| --- | ---: | ---: |
| Feature/placement code, including literals | 3,778 bytes | 3,662 bytes |
| Proven region capacity | 3,809 bytes | 3,809 bytes |
| Remaining bytes | 31 | 147 |
| Fixed runtime state | 12 bytes | 12 bytes |
| Maximum observed scenario stack | 324 bytes | 308 bytes |

**116 bytes saved (3.1%) without feature removal.** All controls, probability
metadata/seed, 57 destination eligibility, A/B persistence, stock playback and
OLED contents remain unchanged. No new memory region, stock-code retirement,
heap, clock, parameter bank or feature is introduced. Source declarations grew;
compiled code shrank. Capacity refers to the linked image, not C line count.

The 147 bytes include small fragments; the largest currently unused contiguous
range is 133 bytes at the appended tail. Repacking can move functions, but this
result does not establish that AFX or the remaining feature wishlist will fit.

## Accepted changes

1. Typed calls to fixed stock entries use relocatable direct Thumb branches
   instead of constant function pointers and address literals. The pinned
   linker's existing `.abs` relocation support resolves those targets after
   placement. Inline encoder and OLED return branches use the same mechanism.
   This saves **68 bytes** (3,778 to 3,710); all 39 native tests passed at this step.
2. Keep the proportional-scaling loop out of the capture caller. Selective
   `noinline` reduces caller spills and total code by another **48 bytes**
   (3,710 to 3,662). No algorithm, scope or guard order changes.

Trampolines, six-argument forwarding and inline register/APSR contracts are
preserved. Position and set-and-send stay unhooked. There is no copied third-party
mod code and no change to the pinned vendor snapshot.

Manifests now include exact executable compiler arguments, per-function compiler
stack frames and per-region used/free bytes. Stack frame metadata excludes stock
call chains and handwritten naked-function pushes; the emulator comparison
measures the actual exercised instruction paths separately. The builder's
optional Python-only `source` argument allows rebuilding the committed r3 source
for regression comparison. The command-line interface is unchanged.

## Rejected candidates

- Frame-pointer omission and machine outlining saved zero bytes; broad inlining
  suppression increased r3 to 3,790 bytes.
- Separately extracting capture or track selection, or allowing raw getter
  inlining, increased the final candidate size; no such change was kept.
- Extracting the pattern-address helper alongside scaling reached 3,650 bytes
  and matched state/messages, but added eight bytes of stack on pitch, Oct-hold
  polling, OLED drawing and copy-release paths. It was rejected despite saving
  another twelve code bytes. A lower overall maximum would have hidden these
  per-operation regressions, so the test checks every observed operation.

## Regression evidence

All **54 local Python tests passed without skips**: the original 53 plus a
comparison test rebuilding native source from checkpoint
`6a5c4128c31012464abfb66754a596490e285cfd`. That test executes the existing 39 native
scenarios on both r3 and r4, in addition to their normal candidate run. It checks
complete synthetic sequence/modulation/runtime state, every parameter group's
values, captured OLED/page/close messages and observed stack per operation.
All compared outputs match; no operation's observed stack increases.

The comparison also enforces strictly smaller code and equal runtime allocation.
It writes only derived measurements to ignored `build/r4-equivalence.json`, not
RAM/firmware dumps. `make native-test` includes this comparison. It explicitly
skips if Unicorn, official input or the baseline Git commit is unavailable;
skips are not equivalence proof. Keep that commit in development clones.

Constructor ABI, actual playback, all 57 recorder cases, relative/Type/LFO/matrix
controls, gesture release/cancellation, serialization and full-track behavior
retain their existing native coverage. Firmware-tool tests also check region
accounting and metadata. Ruff lint/format pass. Core/reference and upstream
sources are unchanged; their prior checkpoint results remain recorded in
[testing](testing.md).

These fixtures stub peripheral queues, final voices and selected timing paths;
construction is not included in the observed stack comparison. This is no full
boot, USB/interrupt timing, audio rendering, real stack margin or device proof.
Follow [staged recovery/install](recovery.md) for actual hardware evaluation.

## Per-region accounting

Used bytes include executable section data and literal pools. Functions retain
actual ELF alignment and remain whole; no alignment safety check is weakened.

| Region start | Capacity | Used | Free |
| --- | ---: | ---: | ---: |
| `0x0807fa60` | 1439 | 1306 | 133 |
| `0x0802be90` | 674 | 672 | 2 |
| `0x0802ca94` | 368 | 364 | 4 |
| `0x0802c2f4` | 238 | 238 | 0 |
| `0x0802d44c` | 228 | 224 | 4 |
| `0x0802bb60` | 160 | 160 | 0 |
| `0x0802bc00` | 132 | 128 | 4 |
| `0x0802bc84` | 140 | 140 | 0 |
| `0x0802bd94` | 252 | 252 | 0 |
| `0x0802ee74` | 178 | 178 | 0 |

## Local r4 artifacts

All stages start from the exact official 5.0.0.2084 input. These are private,
ignored experimental files; r2/r3 images and manifests remain unchanged.

| Stage | Local file under build/ | Native bytes | SHA-256 |
| --- | --- | ---: | --- |
| placement | `freak-er-placement-r4.mff` | 3662 | `c8f4bfdd93532f84ae286f8c028c56e2249d4a6fe76a4517984f3f8461535505` |
| passthrough | `freak-er-passthrough-r4.mff` | 1288 | `80026bb29405c36bc2d744a616fd6b1da0ee5062b1b0d8524919796c943bca42` |
| features | `freak-er-stock-sequencer-experimental-r4.mff` | 3662 | `7c07453672fa907ecf64d40edd63943088d9ea67e62e46db7b6929eeeed906c9` |

Compiler: `Apple clang version 21.0.0 (clang-2100.1.1.101)`.

Source SHA-256: `0472a587c474008483b09136df56da719b8071bccc1a572874e17f31fbaac335`.

Builder SHA-256: `9e3d7850ab7c86d122ab0d90ec32c24f340c9167cde800bb7d3345c50f9f2fb7`.

All three artifacts were independently rebuilt with matching bytes and every
manifest field. All six r2/r3 artifact fingerprints were rechecked unchanged. Filenames, not the stock
version display, distinguish revisions/stages. The user requested a separate
r4 source checkpoint after validation. No assistant-operated flash, publication
or remote change is included.

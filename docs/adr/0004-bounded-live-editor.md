# ADR 0004: bounded stock live editor

Status: Accepted for experimental r3; device acceptance pending.

## Context

The user requests global proportional/Shift-local edits, all stock destinations,
step lock deletion/cleanup/copy and live note changes. The previous five regions
provided only 2,947 bytes. r2 used 2,922 bytes and a cloned recorder with scoped
position/output hooks. The position replacement also changed stock playback
interpolation behavior, discovered by comparison with untouched stock.

## Decision

Use stock eligibility metadata, target assignment and existing record fields
through a narrow adapter. Require parity against the actual recorder for all 57
eligible IDs, baseline conversion and LEDs. Remove position and output hooks.
Keep all twelve runtime bytes; encode pending gestures in the existing scope/value
fields. No heap, extra sequence bank, clipboard bank or flash writer is added.

Add only upstream-proven retired factory sync/oled/boot/cvout commands and the
helper called exclusively by oled, after reference/fall-through analysis. Together
with existing regions this gives 3,809 bytes. The diagnostic boot command is not
the bootloader; normal boot audio/conf/filter/ioc remain intact. Pack whole ELF
sections by actual alignment, deterministically with a bounded exact search,
then merge per region for upstream verification. Fail rather than overflow.

## Consequences

All requested operation categories fit in 3,778 bytes, leaving 31. First-note
editing is deliberately limited to an existing first note; rests cannot be filled
and other chord tones stay unchanged. Copy has no extra screen indicator and
stores only the source index while Record is held. Global scaling clips/quantizes
at stock byte limits, with additive fallback at zero/sign changes. These limits
are explicit in spec 004. Further scope requires measured savings or independently
proven space. Local tests and verified MFFs do not prove device timing, stack,
MCC compatibility or physical-control coverage; evaluate all r3 stages again.

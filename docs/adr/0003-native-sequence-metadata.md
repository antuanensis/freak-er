# ADR 0003: versioned metadata inside existing sequence records

Status: Accepted for experiments; hardware/MCC release gates open.
Date: 2026-10-24

## Context

Probability needs 128 persistent values. Adding tracks, consuming a destination
or allocating another sequence bank conflicts with the stock-only design.
Native RAM is constrained; growing presets or adding flash writes would create
another compatibility risk.

## Decision

Use two trailing bytes of each stock step record, following the accessor /
dataflow and persistence evidence in [native integration](../native-integration.md).
Store probability 0..100 and tag 0xD3. Recognize only complete, valid 64-record
metadata; otherwise default to 100%. Reuse stock serialization and pattern copy.
Invalidate clear/load/built-in resets and honor the empty-pattern marker.

Keep twelve runtime bytes in unused group-21..23 CC-pointer slots. Pack selection
and track flags to retain a raw encoder value without another table. Separate
boundary/Stop bytes from main-loop UI flags.

## Consequences

All four modulation destinations remain available. Native serialization/load,
A/B copy, clear and built-in reset are tested in emulation. Older code ignores
the metadata; original presets default to 100% unless valid extension metadata
is present. No flash writer or extra preset component is added.

This does not promise compatibility with every preset tool. MCC round trips,
downgrade/resave behavior and device persistence must be measured before release.
Another firmware version needs another layout/access audit; every other input
hash is rejected. If those gates fail, revise storage rather than claiming
compatibility from raw serializer tests alone.

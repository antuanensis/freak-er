# ADR 0002: extend the stock sequencer without another transport

Status: Accepted
Date: 2026-10-23

## Context

The first reference implemented its own 16-step transport and four fixed lock
targets. The user requires the normal stock sequencer as the only sequencer and
then narrowed additions to per-step probability and live editing. The supplied
manual establishes A/B patterns with shared 4..64-step length and four freely
assignable stock modulation tracks.

## Decision

Replace the separate reference transport with a probability/editor extension.
Stock retains notes, clock, position, ties, gate scheduling, modulation values,
assignment eligibility and four-track capacity. The extension consumes real
stock boundary notifications, caches one probability decision per visit, and
issues raw parameter edit requests back to stock-owned data.

Retain stock automation/restoration/smoothing behavior even when a note is
suppressed. Do not carry forward the earlier prototype's forced restoration or
its fixed destination list. Conditional triggers and expanded storage capacity
are outside the current milestone.

## Consequences

Reference state shrinks to 144 bytes, including its A/B table. The subsequent
native adapter uses twelve runtime bytes and stock-record metadata instead;
see [ADR 0003](0003-native-sequence-metadata.md). Native hooks/controls now have
emulation evidence. Device timing, physical controls and MCC compatibility remain
separate release gates in [spec 003](../specs/003-stock-sequencer-extension.md).

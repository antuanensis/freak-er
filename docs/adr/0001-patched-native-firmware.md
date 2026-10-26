# ADR 0001: incremental native patching with a portable C core

Status: Accepted
Date: 2026-10-23

## Context

The supplied project contains a patcher and reverse-engineering evidence rather
than a complete firmware source tree. Its main image has little spare flash and
no proven general-purpose free RAM. The requested roadmap depends on real-time
sequencing, controls, and persistence that are not mapped sufficiently yet.

## Decision

Vendor the supplied MIT framework at an exact revision, preserve it, and reuse its
checks for baseline reproduction. Write new algorithms in allocation-free C11,
test them on desktop, and keep device integration separate. Implement roadmap
slices in order and require firmware evidence and hardware gates before claiming
native availability. No unproven code or RAM address will be selected for a build.

## Alternatives and consequences

A complete replacement firmware would require reproducing unknown boot, audio,
control, storage, and peripheral behavior. An external MIDI companion would be a
separate architecture and does not meet the requested native goal. Neither is
selected. Vendoring adds a small source snapshot, avoids a mutable sibling-path
dependency, retains tests and documentation, and permits offline baseline builds.
C creates a path to embedded reuse but does not prove the core will fit or meet
timing. That remains a measured go/no-go decision.

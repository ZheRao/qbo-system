# Failure Logs — [from detected risks]

This document captures potential system failures detected from early stage and the invariants extracted from them.

Each entry follows:

Risk → Root Cause → System Insight → Invariant → Change

## [2026-04-03] — Silent Misclassification Risk in Nested JSON Traversal

### Context
- Source: QBO API (nested JSON)
- Layer: Bronze → Silver
- Component: Node classification

### Risk

Unseen QBO JSON structures could be misclassified or skipped without error.

### Root Cause

Classification relied on implicit structural assumptions and tolerated unknown patterns.

### System Insight

Silent misinterpretation is more dangerous than failure.  
Unknown structure must be treated as invalid.

### New / Updated Invariant
- All nodes must pass strict structural validation before classification
- Every node must map to exactly one known type (no fallback)
- Missing / invalid structure must raise immediately (fail-loud)

### Implementation Change
- Added validation gates:
    - key → KeyError
    - type → TypeError
    - content → ValueError
- Enforced exhaustive classification (no default path)

### Notes

Prevents silent data corruption under schema drift.

## [2026-04-12] — Concurrent Auth Mutation in Distributed Ingestion

### Context
- Source: QBO API
- Layer: Ingestion (Auth + Extraction)
- Component: Auth handling under Spark execution

### Risk

Multiple Spark partitions could concurrently refresh and write auth state for the same company, leading to race conditions and inconsistent auth files.

### Root Cause

Auth refresh and persistence were embedded inside extraction logic, which is executed in a distributed, unordered, and retryable environment.

### System Insight

Control-plane state mutation is not compatible with distributed execution.  
Auth refresh is inherently single-writer and order-sensitive, while Spark execution is parallel and non-deterministic.

### New / Updated Invariant
- Auth refresh must not occur inside distributed workers
- Shared auth state must not be mutated concurrently
- Distributed tasks may only consume auth state, never modify it

### Implementation Change
- Moved auth refresh into a preflight sequential step (driver-only)
- Constructed a per-run auth snapshot for all companies
- Broadcast auth snapshot to workers as read-only input
- Removed all auth write logic from partition-level execution

### Notes

Prevents race conditions, inconsistent auth state, and non-deterministic pipeline behavior under Spark execution.
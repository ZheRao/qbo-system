# Failure Logs — [future scale risks]

This document captures potential system failures that are not yet active but are expected to emerge under scale.

Each entry follows:

Risk → Root Cause → System Insight → Invariant → Potential Solutions



## [2026-04-26] — Auth Expiry vs Long-Running Distributed Ingestion

### Context

* Source: QBO API
* Layer: Bronze Ingestion (Auth + Extraction)
* Execution: Spark (distributed)
* Current Design (Spark):

  * Auth refresh occurs in a preflight driver-only step
  * A per-run auth snapshot is broadcast to workers (read-only)
  * Workers do not mutate auth state (enforced invariant)

### Risk

If ingestion duration exceeds auth token lifetime (~60 minutes), workers will begin using expired tokens mid-execution, leading to partial failures, retries, or inconsistent ingestion states.

This risk increases with:

* growing data volume (longer extraction time)
* multi-tenant scaling (more entities per run)
* API latency variability



### Root Cause

Auth tokens are:

* time-bound (expire after fixed duration)
* captured as a **static snapshot at job start**

Distributed ingestion is:

* long-running
* non-deterministic in execution time

→ A **time-variant dependency (auth)** is treated as a **time-invariant input (snapshot)**.



### System Insight

Time-sensitive control-plane state (e.g., auth tokens) cannot be safely modeled as a global constant in long-running distributed jobs.

Auth should be treated as a:

* **renewable, per-request or per-stream lease**
  rather than
* **job-global immutable snapshot**



### Invariant (future)

* Long-running distributed ingestion must not rely on globally static, time-expiring credentials
* Auth validity must be guaranteed at the point of API interaction, not assumed from job start
* Systems must either:

  * bound execution within credential lifetime, or
  * support safe credential renewal without violating control-plane invariants



### Potential Solutions

#### 1. Time-Bounded Ingestion (Batching) — *Preferred initial strategy*

* Split ingestion into smaller runs such that each completes within token lifetime
* Example:

  * partition by entity and/or time window (periods)
* Properties:

  * minimal architectural change
  * preserves current invariants
  * deterministic and replayable



#### 2. Driver-Orchestrated Mid-Run Token Refresh

* Driver monitors token expiry and refreshes tokens during execution
* Requires:

  * versioned auth state
  * safe propagation to workers (e.g., broadcast refresh or lookup layer)
* Tradeoffs:

  * increased system complexity
  * potential consistency issues if not carefully designed



#### 3. External Auth Service (Token-on-Demand Model)

* Workers request valid tokens from a centralized auth service:

  * `get_token(entity_id)`
* Service ensures:

  * single-writer refresh
  * always-valid token issuance
* Properties:

  * decouples auth lifecycle from ingestion job
  * supports arbitrarily long execution
* Tradeoffs:

  * introduces network dependency and service layer
  * requires concurrency control and caching strategy



#### 4. Per-Entity Job Isolation (Alternative Considered)

* Run one Spark job per entity to align token lifetime with job duration
* Tradeoffs:

  * increased scheduling overhead
  * fragmented execution and observability
  * reduced parallel efficiency
* Status:

  * not preferred unless driven by additional constraints



### Notes

* Current system completes ingestion within ~10 minutes → risk is not active
* This is a **scale-triggered failure**, not a present issue
* Decision should be revisited when:

  * ingestion duration approaches 30–40 minutes, or
  * API rate limits / latency materially increase



### Meta

This entry exists to prevent premature over-engineering while preserving awareness of a known scaling boundary.

Re-evaluate under real pressure rather than theoretical maximums.

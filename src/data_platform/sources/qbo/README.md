# data-platform

## Overview

`data-platform` is a **configurable data ingestion and transformation framework** designed to convert semi-structured external data (e.g. APIs like QuickBooks Online) into structured, analysis-ready datasets.

The system is built around a strict separation of concerns:

- **Platform mechanics** → how data pipelines execute
- **Source adapters** → how external systems are ingested and normalized
- **Business contracts** → how structured data is interpreted downstream

This enables the platform to scale across:
- multiple source systems
- multiple companies (multi-tenant)
- multiple execution environments (Pandas / PySpark)

without modifying core logic.

> The goal is not to build pipelines, but to build **durable data infrastructure** that compounds over time.

## Core Principles

### 1. No-Assumption Data Processing (Bronze / Silver)

- **Bronze Layer** → raw extraction from source systems (no transformation assumptions)
- **Silver Layer** → structural normalization (e.g. flattening nested JSON)

Constraints:
- no business logic
- no fixed schema expectations
- no company-specific assumptions

This ensures:
- resilience to schema drift
- portability across sources
- reproducibility of raw truth

### 2. Externalized Business Logic (Gold)

- All business meaning is defined **outside the engine**
- Driven by **contracts and configuration**

Examples:
- entity mappings
- location grouping
- financial classification rules

This allows:
- multi-tenant reuse
- zero code changes for new companies
- controlled evolution of business logic

### 3. Engine Abstraction

Execution engine is configurable:

- `Pandas` → local / lightweight workflows
- `PySpark` → distributed / large-scale processing

The same pipeline logic can run on either engine via configuration.

### 4. Configuration-Driven System

All variability is externalized:

- I/O paths
- runtime behavior (e.g. Spark configs, partitioning)
- structural assumptions
- contracts (business logic)

This eliminates hardcoding and enables:
- reproducible runs
- environment portability
- controlled system behavior


## Architecture

```text
data_platform/
    core/                      # platform mechanics
    sources/                   # source system adapters
        <source_name>/
    gold/                      # business-level transformations
        templates/
```

### 1. Core Layer

`src/data_platform/core`

Responsible for **platform mechanics shared across all sources**

Includes:
- execution engine abstraction (Spark / Pandas)
- configuration loading
- filesystem utilities (safe read/write, atomic operations)
- common data operations

Answers:
> How does the system run?

---
### 2. Source Layer

`src/data_platform/sources/{source_name}`

Each source system is implemented as an isolated adapter.

Structure:
```
sources/{source_name}/
    ingestion/
    transformation/
    json_configs/
    utils/
    docs/
```
---
**Responsibilities:**

#### `/ingestion` (Bronze Layer)
- API extraction
- raw data retrieval
- writes JSON (or raw format) to Bronze

Flow:
```
API → raw data → file write (Bronze)
```
---
#### `/transformation` (Silver Layer)
- load raw data from Bronze
- normalize structure (flattening, expansion)
- output structured tables

Flow:
```
Bronze → transformation → tabular dataset → file write (Silver)
```
---
#### `/json_configs` (External Control Layer)

All system variability is defined here:

- `/io` → path configurations
- `/system` → runtime configs (e.g. Spark write mode, partition sizing)
- `/assumptions` → structural invariants of source data
- `/state` → job metadata (e.g. extracted FX rates, checkpoints)
- `/contracts` → company-specific business mappings

---
#### `/utils`

Source-specific helpers:
- API traversal
- task scheduling (e.g. Spark `mapPartitions`)
- normalization utilities

---
#### `/docs`
- setup guides
- raw data structure references
- operational procedures

---
### 3. Gold Layer

`src/data_platform/gold`

Represents **business-level transformations**

Depends only on:
- Silver datasets
- external contracts

Contains:
- reusable transformation templates
- company-specific modeling logic

Answers:
> How should this data be interpreted?

## End-to-End Flow
```
External API (e.g. QBO)
        ↓
Bronze (raw extraction)
        ↓
Silver (normalized tables)
        ↓
Gold (business models)
```

## Prerequisites

### 1. Authentication
API credentials / refresh tokens must be stored in:
```
sources/{source_name}/json_configs/io/path.json
```
### 2. Contracts (Required for Gold Layer)

Company-specific configurations must be defined in:
```
sources/{source_name}/json_configs/contracts/
```

### 3. Environment
- Python
- Optional:
    - PySpark (for distributed execution)
    - Pandas (for local execution)

## Design Intent

This project is intentionally built to:
- handle schema variability without breaking
- separate data structure from business meaning
- support multi-tenant scaling
- remain engine-agnostic
- evolve incrementally without rewrites

## Future Directions
- stronger schema enforcement at Silver layer
- incremental processing / checkpointing
- observability (logging, metrics, failure tracing)
- adapter expansion beyond QBO
- performance tuning for large-scale Spark jobs

## Final Note

This system reflects a shift from:
>"writing data scripts"

to
> "building data infrastructure"

The difference is durability, composability, and long-term leverage.
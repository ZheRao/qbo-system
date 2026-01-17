# QBO Data System

## Overview

This repository implements a **scalable, production-oriented data extraction and transformation framework** for **QuickBooks Online (QBO)**.

The system is designed to:
- Extract multiple QBO entities and reports (e.g. Profit & Loss, General Ledger, raw tables)
- Persist raw and transformed data using a **Bronze / Silver / Gold** layered architecture
- Flatten semi-structured QBO JSON payloads into **partitioned, analytics-ready tabular datasets**
- Serve as a durable pipeline into **Power BI** via SharePoint file sync (Windows-based), as a pragmatic compromise in the absence of Azure/AWS infrastructure

This repo represents a **personal milestone** toward building **industrialized data systems that are modular, documented, externally configured, and designed to last**.


## Design Principles

- **Framework-first, not task-first**  
  This is not a one-off ETL job. The system is designed to scale across:
  - New QBO entities
  - Additional companies
  - New fiscal periods
  - Additional downstream consumers

- **Strict compartmentalization**  
  I/O, ingestion, transformation, and business logic are separated by responsibility.

- **Externalized configuration**  
  Paths, schemas, contracts, and business mappings live outside code whenever possible.

- **Layered storage, not layered modules**  
  Bronze / Silver / Gold are **storage concepts**, not Python submodules. This allows storage backends to evolve independently of code.

## What This System Does

### 1. Extract (Bronze Layer)

- Extracts data from QBO API:
  - Financial reports (e.g. Profit & Loss, General Ledger)
  - Raw entity tables
- Supports:
  - Multiple sub-companies
  - Configurable fiscal years / periods
- Handles:
  - Authentication and token refresh
  - Distributed / parallel HTTP extraction (Spark-capable)
- Writes **raw API payloads** to the **Bronze** layer with partitioned paths:

```text
QBO/
  data_type=pl/
  company_code=XXX/
  year_month=YYYY-MM/
```

> Bronze is treated as **immutable raw truth** — no schema assumptions, no transformations.

---
### 2. Transform (Silver Layer)

- Flattens nested JSON structures into tabular form

- Applies:
    - Schema normalization
    - Column standardization
    - Type coercion

- Writes clean, structured outputs as:
    - Parquet (primary)
    - CSV (optional / compatibility)

> Silver represents **standardized, reusable data assets** independent of business rules.

--- 
### 3. Curate (Gold Layer)

- Applies final business logic and reporting rules
- Produces analytics-ready tables aligned with reporting needs
- Writes outputs directly to a Windows filesystem directory synced with SharePoint
    - Enables downstream Power BI consumption
    - Chosen intentionally due to lack of current Azure/AWS migration

> Gold is consumer-facing and opinionated by design.

## Downstream Consumers

Gold datasets currently power:
- Executive dashboards
- HR dashboards (*partial*)
- Operational / pillar dashboards

The framework is intentionally generic enough to support:
- Budgeting systems
- Forecasting
- HR analytics
- Additional finance workflows

## Repository Structure

Current `src/qbo_etl` layout:

```text
src/qbo_etl
├── ingestion/              # API extraction orchestration
├── io/                     # File system I/O abstractions
│   ├── file_read.py
│   └── file_write.py
├── json_configs/           # Externalized configs & contracts
│   ├── contracts/          # Schema & business contracts
│   └── io/
│       └── database.path.json
├── silver/                 # JSON → tabular transformations
│   └── flatten.py
├── utils/                  # Shared utilities
│   └── task_schedular.py
└── __init__.py
```

## Configuration & Secrets

- All paths, schemas, and contracts are externally defined
- Secrets and credentials are intentionally excluded from the repository
- Storage locations for Bronze / Silver / Gold are configured outside code

## Current Limitations (Explicit & Intentional)

Given time constraints and an active refactor phase:
- ❌ Unit tests are **temporarily not implemented**
- ❌ Structured logging is **temporarily not implemented**

These are **known and accepted tradeoffs**, not omissions by accident.  
The system architecture is designed to support both once stability is reached.

## Why This Repo Exists

This project marks a **transition from scripting to system-building**.

Key milestones represented here:
- Treating data pipelines as long-lived infrastructure
- Designing for scale before feature completeness
- Making architecture, constraints, and tradeoffs explicit
- Prioritizing clarity, documentation, and external contracts

This repository is a foundation — not an endpoint.

## Future Directions

- Formal unit testing and test data contracts
- Structured logging and observability
- Full cloud migration (Azure / AWS)
- Unified data platform built on the same architectural principles
# data-platform

## Overview

`data-platform` is a **generic data ingestion and transformation framework** designed to convert semi-structured external data sources into structured datasets.

The platform was initially developed for **QuickBooks Online (QBO)** but is intentionally structured so that:
- **platform mechanics remain stable**
- **source-specific ingestion is isolated**
- **business representation is externally defined**

The goal is not to produce one-off ETL pipelines, but to build **durable, reusable data infrastructure**.

## Core Design Principles

The architecture separates three different concerns:
1. **Platform mechanics** — how ingestion pipelines run
2. **Source mechanics** — how external systems are translated into structured data
3. **Business meaning** — how companies interpret the structured data

Keeping these concerns isolated allows the platform to support **multiple source systems and organizations without rewriting core logic**.

## Architecture
```text
data_platform/
    core/              # platform mechanics
    sources/           # source system adapters
        qbo/
        qbo_time/
        ...
    gold/              # company-specific transformations
        templates/         # optional reusable modeling patterns
```
### 1. Core Layer

`data_platform/core`

The **core layer** contains platform mechanics shared across all source systems.

Examples include:
- configuration loading
- filesystem utilities
- execution environments (Spark / Pandas)

Its responsibility is to answer:  
*How should the platform run?*

### 2. Source Layer

`data_platform/sources/<source_system>`

Each external system is implemented as a **source adapter**.

Examples:
```text
sources/
    qbo/
    qbo_time/
```
Source adapters handle:
- authentication
- API extraction
- hierarchical traversal
- normalization of nested structures
- construction of **Silver-layer datasets**

Source code answers:  
*How do we translate this external system into structured internal data?*

### 3. Gold Layer

Gold-layer transformations represent **business-specific data models**.

It depends only on:
1. **Silver-layer datasets**
2. **external configuration** (mappings, categories, naming rules)

This keeps business meaning separate from ingestion mechanics.

Gold answers:  
*How should this company interpret the structured data?*

## Example pipeline:
```text
QBO API
  ↓
Bronze extraction
  ↓
Silver normalization
  ↓
Gold business modeling
```

## Project Philosophy

This project represents a shift from **data scripting** toward **data systems engineering**.

The platform is designed to be:
- structurally robust
- externally configurable
- portable across organizations
- resilient to schema variation
- capable of long-term evolution

The objective is to build **data infrastructure that compounds over time**.
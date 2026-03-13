# Generic Data Platform (Initial Implementation)

### Overview

This repository implements the **initial version of a generic data ingestion platform** for transforming semi-structured API data into structured datasets.

The system was first developed for **QuickBooks Online (QBO)** but is designed so that:
- **framework mechanics remain stable**
- **source-specific semantics are externalized**

The goal is to build **durable data infrastructure**, not one-off ETL pipelines.

## Core Architecture

The platform separates **data mechanics** from **data meaning**.

Framework responsibilities:
- hierarchical JSON traversal
- schema discovery
- structural normalization
- distributed processing (Spark)

External configuration defines:
- column mappings
- schema contracts
- company-specific logic

This allows the same framework to ingest **multiple sources and organizations** without rewriting core logic.

## Data Layers

The system follows a **Bronze / Silver / Gold** architecture.

**Bronze — Raw Source Data**
- Raw API responses stored unchanged
- Immutable source of truth

**Silver — Structural Data**
- Nested JSON flattened into structured datasets
- Source-faithful normalization

**Gold — Business Data**
- Column mappings
- reporting logic
- analytics-ready datasets

## Structural Invariants

The system is built around a few strict invariants.

### 1. Preserve Raw Truth
```text
Raw API → Bronze → Silver → Gold
```
- No transformation occurs before Bronze.

### 2. Mechanics Before Semantics

- Framework code handles **structure**.  
- Business meaning is defined through **external contracts**.

### 3. Structure-Driven Traversal
- Semi-structured APIs are treated as **hierarchical object systems**.
- Nodes are processed by **structural signatures**, not ad-hoc case logic.
- Data extraction occurs only at **terminal data nodes**.

### 4. Unknown Structures Must Fail

The system fails loudly when encountering unrecognized structures.

Errors reveal:
- schema variation
- missing invariants
- API evolution

## Current Source

QuickBooks Online serves as the **first production test case** for the platform, particularly its deeply nested financial report structures.

## Repository Purpose

This project represents a shift from data scripting to data systems engineering.

The objective is a platform that is:
- structurally robust
- externally configurable
- resilient to schema variation
- designed to evolve
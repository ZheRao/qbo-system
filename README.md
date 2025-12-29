# QBO Data System

## Overview

Extracts QuickBooks Online (QBO) reports and entities via QBO API, stores raw responses in **Bronze** layer, and transforms into standardized **Silver/Gold** tables for analytics

## What this system does

### **Extract**
- Pulls QBO data (PL, GL, raw tables)
    - Across all configured subcompanies
    - For selected fiscal years
- Handles authentication, token refresh, and distributed HTTP extraction
- Writes raw API payloads to ***Bronze*** with partitioned paths:
```text
QBO/data_type=.../company_code=.../year_month=...
```

### **Transform**
- Flattens raw JSON into tabular form
- Applies schema standardization and column mappings
- Writes cleaned outputs as Parquet files in the ***silver*** layer
- Applies final business rules for analytics consumption (***Gold*** layer)

### **Downstream consumers**
The transformed datasets power multiple business dashboards, including:
- *Executive Dashboard*
- *HR Dashboard*
- *Pillar Dashboards*

## Repo layout

```text
├── src/  
│   └── qbo_etl/  
│       ├── __init__.py  
│       ├── pl/        
│       │   ├── __init__.py  
│       │   ├── extract.py  
│       │   ├── flatten.py  
│       │   └── business_rules.py  
│       ├── gl/  
│       │   ├── __init__.py  
│       │   └── ...  
│       └── hr/  
│           ├── __init__.py  
│           └── ...  
├── tests/  
└── config/  
└── docs/  
```

# Databricks Delta Pipeline — Customer Support Analytics

An end-to-end ETL pipeline for Customer Support performance reporting using **FastAPI, PySpark, Databricks, AWS S3, Delta Lake, Unity Catalog, and Power BI**.

The project follows a **Medallion Architecture (Bronze → Silver → Gold)**, separating raw ingestion, data transformation and quality validation, and business-ready analytics.

---

## 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │   Customer Support   │
                         │       CSV / API      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │    REST Endpoint     │
                         │       /upload        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Databricks      │
                         │       PySpark        │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │     BRONZE LAYER     │
                         │   Raw Delta Data     │
                         │        AWS S3        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    SILVER LAYER      │
                         │ Cleaned & Structured │
                         │   Data + DQ Checks   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      GOLD LAYER      │
                         │ Business Metrics     │
                         │        AWS S3        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Power BI        │
                         │ Customer Operations  │
                         │      Dashboard       │
                         └──────────────────────┘
```

The project stores Delta data externally in AWS S3 while Databricks provides the PySpark processing layer and Unity Catalog table registration.

---

## 🎯 Business Problem

The Customer Operations team needed visibility into:

* Agent performance
* Average Handle Time (AHT)
* Daily ticket volumes
* Ticket status distribution
* Resolution rates by issue type

The pipeline converts raw customer-support data into business-ready datasets that can be consumed by Power BI.

---

## 🛠️ Technology Stack

| Technology        | Purpose                                        |
| ----------------- | ---------------------------------------------- |
| **FastAPI**       | REST API endpoint for file ingestion           |
| **Python**        | API handling and ingestion logic               |
| **PySpark**       | Distributed data processing and transformation |
| **Databricks**    | Spark processing environment                   |
| **AWS S3**        | Persistent data storage                        |
| **Delta Lake**    | Transactional storage format                   |
| **Unity Catalog** | Table and schema registration                  |
| **Power BI**      | Business reporting and visualization           |

---

# 📥 1. Data Ingestion — FastAPI

The project starts with a FastAPI application exposing a `/upload` endpoint.

```text
POST /upload
```

The endpoint:

1. Accepts a CSV file.
2. Reads the uploaded file.
3. Converts the CSV into a Pandas DataFrame.
4. Converts the records into JSON.
5. Returns the uploaded records and record count.

## The API application is named **Agent Support API**.

# 🥉 2. Bronze Layer — Raw Ingestion

**Notebook:** `01_Bronze_API_Ingestion`

The Bronze layer preserves the incoming data before business transformations.

### Responsibilities

* Extract data from the REST API.
* Process records in batches using pagination.
* Handle timeouts and connection errors.
* Retry selected HTTP failures.
* Use exponential backoff.
* Preserve the incoming values as strings.
* Add ingestion metadata.
* Store the raw data as Delta in S3.

The implemented API extraction uses a **100-record page size**, up to **3 retries**, and a **30-second timeout**.

### Error Handling

The extraction logic handles:

* Timeouts
* Connection errors
* HTTP `429`
* HTTP `500`
* HTTP `502`
* HTTP `503`
* HTTP `504`

Retry waits use exponential backoff.

### Bronze Metadata

Each batch includes:

```text
_ingested_at
_source_url
_batch_id
_page
```

This provides basic ingestion traceability and batch-level lineage.

### S3 Location

```text
s3://sales-pipeline-data-lake-ratnajit/bronze/customer_support_tickets/
```

The Bronze data is written in **Delta format using append mode**.

---

# 🥈 3. Silver Layer — Transformation & Data Quality

**Notebook:** `02_Silver_Transformation`

The Silver layer converts raw Bronze data into clean, structured analytical data.

### Transformations

* Convert `aht_minutes` from STRING → INT.
* Convert `created_date` from STRING → DATE.
* Trim whitespace from text fields.
* Remove duplicate tickets.
* Keep the latest record for each `ticket_id`.

The deduplication uses a Spark window ordered by ingestion timestamp.

### Data Quality Checks

The pipeline checks:

```text
Null ticket_id
Null aht_minutes
Null created_date
Duplicate records
```

The current run produced:

```text
Bronze records: 1000
Silver records: 1000
Duplicates removed: 0
```

The resulting Silver schema contains proper `INT` and `DATE` types.

### S3 Location

```text
s3://sales-pipeline-data-lake-ratnajit/silver/customer_support_tickets/
```

The cleaned dataset is stored as a Delta table and registered in Unity Catalog.

---

# 🥇 4. Gold Layer — Business Metrics

**Notebook:** `03_Gold_Business_Metrics`

The Gold layer transforms the cleaned Silver data into business-ready datasets for reporting.

Three analytical datasets are created.

---

## 👤 Agent Performance

```text
gold/agent_performance/
```

Metrics include:

* Agent name
* Tickets handled
* Average AHT
* Total AHT

Example output contains performance metrics for four agents.

---

## 📈 Daily Ticket Volume

```text
gold/daily_ticket_volume/
```

Metrics include:

* Created date
* Total tickets
* Resolved tickets
* Open tickets
* Pending tickets
* Average AHT

The current dataset contains daily metrics across **91 days**.

---

## 🎯 Resolution Rates

```text
gold/resolution_rates/
```

Metrics include:

* Issue type
* Status
* Ticket count
* Average AHT
* Total tickets per issue type
* Percentage

Resolution metrics are calculated across issue types and ticket statuses.

---

# ☁️ S3 Data Lake Structure

```text
sales-pipeline-data-lake-ratnajit/
│
├── bronze/
│   └── customer_support_tickets/
│
├── silver/
│   └── customer_support_tickets/
│
└── gold/
    ├── agent_performance/
    ├── daily_ticket_volume/
    └── resolution_rates/
```

All three layers use **Delta Lake on AWS S3**.

---

# 🗂️ Unity Catalog Structure

The project registers the S3-backed Delta datasets in Unity Catalog:

```text
workspace
│
├── bronze
│   └── customer_support_tickets
│
├── silver
│   └── customer_support_tickets
│
└── gold
    ├── agent_performance
    ├── daily_ticket_volume
    └── resolution_rates
```

Unity Catalog is used for schema and table organization while the underlying Delta data remains in S3.

---

# 📊 Power BI

The Gold datasets are designed for consumption by Power BI.

The reporting layer focuses on:

* Agent performance
* AHT analysis
* Daily ticket trends
* Ticket status
* Resolution rates
* Issue-type analysis

The Gold layer is specifically designed to provide aggregated business metrics for Customer Operations reporting.

---

# 📁 Project Structure

```text
databricks-delta-pipeline/
│
├── app.py
│
├── notebooks/
│   ├── 01_Bronze_API_Ingestion.ipynb
│   ├── 02_Silver_Transformation.ipynb
│   └── 03_Gold_Business_Metrics.ipynb
│
├── data/
│   └── customer_support_tickets.csv
│
├── README.md
└── .gitignore
```

### Notebook Responsibilities

```text
01_Bronze_API_Ingestion
        ↓
API extraction + pagination + retries
        ↓
S3 Bronze Delta

02_Silver_Transformation
        ↓
Type casting + cleaning + deduplication + DQ
        ↓
S3 Silver Delta

03_Gold_Business_Metrics
        ↓
Business aggregations
        ↓
S3 Gold Delta
        ↓
Power BI
```

---

# 🔄 End-to-End Flow

```text
Customer Support Data
        │
        ▼
     FastAPI
        │
        ▼
   REST /upload
        │
        ▼
     PySpark
        │
        ▼
┌───────────────────┐
│ Bronze - S3 Delta │
│ Raw + Metadata    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Silver - S3 Delta │
│ Clean + Validate  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Gold - S3 Delta   │
│ Business Metrics  │
└─────────┬─────────┘
          │
          ▼
      Power BI
```

---

# 📌 Project Highlights

* REST API-based ingestion with FastAPI.
* Batch extraction using pagination.
* Retry handling with exponential backoff.
* Raw data preservation in Bronze.
* Delta Lake storage on AWS S3.
* PySpark-based transformations.
* Data-type standardization.
* Duplicate detection and removal.
* Null-value validation.
* Batch and ingestion metadata for traceability.
* Business-focused Gold datasets.
* Power BI reporting layer.
* Unity Catalog registration for S3-backed Delta tables.

---

## 👨‍💻 Project Role
**Role:** Senior Data Analyst

The project demonstrates the ability to work across the analytics pipeline—from consuming REST API data and processing it with PySpark to preparing business-ready datasets and building reporting outputs in Power BI.

**Author** Ratnajit Chakraborty
https://www.linkedin.com/in/ratnajit-chakraborty-076ab520a

The focus is on **data analysis and analytics engineering**, while using data-engineering concepts such as API ingestion, Delta Lake, S3 storage, data quality, and medallion architecture.

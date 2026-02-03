# Technical Architecture
## Credit Scoring for Unbanked Retailers

---

## Overview

This document provides detailed technical architecture for the credit scoring ML pipeline, covering data flows, processing layers, model architecture, and deployment considerations.

---

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES LAYER                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  CSV Files (Synthetic Data Generation)                               │
│  ├─ retailers.csv          (10,000 retailer profiles)               │
│  ├─ transactions.csv       (75,347 purchase orders)                 │
│  ├─ repayments.csv         (payment history)                        │
│  └─ macro_indicators.csv   (economic context)                       │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                       BRONZE LAYER (Raw Ingestion)                    │
│                      Notebook: 00_Ingestion.ipynb                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Purpose: Ingest raw data with minimal processing                    │
│                                                                       │
│  Processing:                                                          │
│  • CSV to Delta Lake conversion                                      │
│  • Add ingestion metadata (timestamp, source_file)                   │
│  • Schema inference and type casting                                 │
│  • No data quality checks (preserve original)                        │
│                                                                       │
│  Output Tables:                                                       │
│  ├─ bronze_retailers         (10,000 rows)                          │
│  ├─ bronze_transactions      (75,347 rows)                          │
│  ├─ bronze_repayments        (payment records)                       │
│  └─ bronze_macro_indicators  (economic data)                         │
│                                                                       │
│  Storage: Delta Lake (ACID-compliant, versioned)                     │
│  Format: Partitioned by ingestion_date                               │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    SILVER LAYER (Cleaned & Validated)                 │
│                   Notebook: 01_transformation.ipynb                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Purpose: Clean, validate, and enrich data for analytics             │
│                                                                       │
│  Data Quality Checks:                                                 │
│  ✓ Deduplication (remove duplicate retailer_id, transaction_id)     │
│  ✓ Null handling (impute or drop based on criticality)              │
│  ✓ Type validation (dates, numbers, enums)                          │
│  ✓ Business rule validation (age > 0, amount > 0, etc.)             │
│  ✓ Referential integrity (transaction → retailer FK exists)         │
│                                                                       │
│  Enrichment:                                                          │
│  • Join transactions with repayment data                             │
│  • Calculate days_late (payment_date - due_date)                     │
│  • Flag on_time payments (days_late <= 0)                            │
│  • Add order sequence numbers                                        │
│  • Parse dates and extract temporal features (year, month, quarter) │
│                                                                       │
│  Output Tables:                                                       │
│  ├─ silver_retailers                  (cleaned retailer master)     │
│  ├─ silver_retailer_transactions      (enriched transactions)       │
│  └─ silver_repayments                 (validated payments)           │
│                                                                       │
│  Data Quality Metrics:                                                │
│  • Completeness: 99.8% (minimal nulls)                               │
│  • Uniqueness: 100% (no duplicates)                                  │
│  • Validity: 99.95% (business rules passed)                          │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                   GOLD LAYER (ML Feature Engineering)                 │
│                  Notebook: 02_Gold_ML_Features.ipynb                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Purpose: Generate point-in-time ML-ready features                   │
│                                                                       │
│  Point-in-Time Methodology:                                           │
│  • Observation Dates: 8 snapshots (July-Oct 2024)                   │
│    - 2024-07-25, 2024-08-01, 2024-08-10, 2024-08-20                │
│    - 2024-09-01, 2024-09-15, 2024-09-30, 2024-10-15                │
│                                                                       │
│  • Lookback Windows:                                                  │
│    - Recent: Last 30 days                                            │
│    - Medium: Last 60 days                                            │
│    - Lifetime: All historical data                                   │
│                                                                       │
│  • Forward Window (Labels):                                           │
│    - Performance: Next 45 days                                       │
│    - Default threshold: 30+ days late                                │
│                                                                       │
│  Feature Categories (50+ features):                                   │
│                                                                       │
│  1. Payment Behavior (13 features):                                  │
│     • on_time_rate_{recent/medium/lifetime}                          │
│     • avg_days_late_{recent/medium/lifetime}                         │
│     • max_days_late_{recent/lifetime}                                │
│     • late_rate_{recent/medium/lifetime}                             │
│     • payment_consistency                                             │
│     • on_time_improvement                                             │
│                                                                       │
│  2. Transaction Patterns (7 features):                               │
│     • txn_count_{recent/medium/lifetime}                             │
│     • avg_orders_per_month                                            │
│     • days_since_last_order                                           │
│     • txn_velocity_ratio (recent vs medium)                          │
│     • unique_categories (product diversity)                           │
│                                                                       │
│  3. Transaction Values (7 features):                                 │
│     • avg_order_value_{recent/medium/lifetime}                       │
│     • total_value_{recent/medium/lifetime}                           │
│     • credit_utilization (used / limit)                              │
│                                                                       │
│  4. Behavioral Trends (4 features):                                  │
│     • payment_deterioration_ratio                                     │
│     • late_rate_change                                                │
│     • txn_velocity_ratio                                              │
│     • on_time_improvement                                             │
│                                                                       │
│  5. Business Characteristics (8 features):                           │
│     • years_in_business, months_in_business                          │
│     • num_employees                                                   │
│     • has_business_registration (binary)                             │
│     • formality_score (0-1)                                          │
│     • customer_tenure_days                                            │
│     • owner_age                                                       │
│                                                                       │
│  6. Mobile Money (2 features):                                       │
│     • monthly_mobile_money_txns                                       │
│     • mobile_money_score (usage pattern)                             │
│                                                                       │
│  7. Categorical (Encoded):                                           │
│     • shop_type_encoded (Kiosk=0, Store=1, etc.)                    │
│     • urbanization_encoded (Rural=0, Peri=1, Urban=2)               │
│     • gender_encoded (Male=0, Female=1)                              │
│                                                                       │
│  8. Macroeconomic (3 features):                                      │
│     • usd_ngn_rate (exchange rate)                                   │
│     • inflation_rate_pct                                              │
│     • gdp_growth_rate_pct                                             │
│                                                                       │
│  9. Risk Flags (5 features):                                         │
│     • approved_tier_flag                                              │
│     • deteriorating_flag                                              │
│     • inactive_flag                                                   │
│     • excellent_payer_flag                                            │
│     • growth_tier_flag                                                │
│                                                                       │
│  Output Tables:                                                       │
│  ├─ gold_ml_features_july_dec_2024  (8,150 samples, 50+ features)  │
│  └─ Feature statistics and distributions                             │
│                                                                       │
│  Data Leakage Prevention:                                             │
│  ✓ Strict temporal ordering (only past data for features)           │
│  ✓ Labels based on future behavior (45-day window)                  │
│  ✓ No target leakage in feature engineering                         │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                     ML TRAINING & PREDICTION LAYER                    │
│              Notebook: 05_Credit_Risk_Model_Training.ipynb            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ML Framework: Apache Spark MLlib                                     │
│  Orchestration: MLflow (experiment tracking, model registry)         │
│                                                                       │
│  Model Architecture:                                                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Gradient Boosted Trees (GBT) Regressor                          ││
│  │                                                                  ││
│  │ Hyperparameters:                                                 ││
│  │ • maxIter: 100 (number of trees)                                ││
│  │ • maxDepth: 6 (tree depth)                                      ││
│  │ • stepSize: 0.1 (learning rate)                                 ││
│  │ • subsamplingRate: 0.8 (80% data per tree)                     ││
│  │ • featureSubsetStrategy: auto                                    ││
│  │                                                                  ││
│  │ Input:                                                            ││
│  │ • Features: 44 selected features (vector)                       ││
│  │ • Label: Credit score baseline (300-850)                        ││
│  │                                                                  ││
│  │ Output:                                                           ││
│  │ • Predicted credit score (continuous)                           ││
│  │ • Confidence intervals                                           ││
│  │ • Feature importance scores                                      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  Training Pipeline:                                                   │
│  1. Feature Selection (44 most predictive features)                 │
│  2. Vector Assembly (combine features into single column)           │
│  3. Standard Scaling (mean=0, std=1)                                │
│  4. GBT Training (regression)                                        │
│  5. Score to Tier Mapping (scores → Platinum/Gold/Silver/etc.)     │
│  6. Credit Limit Calculation (risk-adjusted limits)                 │
│                                                                       │
│  Train/Test Split:                                                    │
│  • Strategy: Time-based split (respect temporal order)              │
│  • Training: First 6 observation dates (80% samples)                │
│  • Testing: Last 2 observation dates (20% samples)                  │
│  • No random shuffling (preserve time series nature)                │
│                                                                       │
│  Model Evaluation:                                                    │
│  • Regression Metrics: RMSE=2.32, MAE=1.65, R²=0.93                │
│  • Classification Metrics: Tier Accuracy=97.0%                      │
│  • Business Metrics: 0% default in top tiers                        │
│                                                                       │
│  Output Tables:                                                       │
│  ├─ gold_credit_score_predictions  (6,266 scored retailers)        │
│  ├─ gold_credit_limits              (risk-adjusted limits)           │
│  └─ model_registry                  (MLflow tracked)                 │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS & BI LAYER (Star Schema)                 │
│             Notebook: Notebook_Normalized_Table_PowerBI.ipynb         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Purpose: Prepare dimensional model for Power BI                      │
│                                                                       │
│  Star Schema Design:                                                  │
│                                                                       │
│  Fact Table:                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ gold_fact_credit_scoring                                         ││
│  │                                                                  ││
│  │ Keys:                                                             ││
│  │ • fact_key (PK)                                                  ││
│  │ • date_key (FK → dim_date)                                       ││
│  │ • retailer_key (FK → dim_retailer)                               ││
│  │ • risk_tier_key (FK → dim_risk_tier)                             ││
│  │ • credit_product_key (FK → dim_credit_product, optional)        ││
│  │                                                                  ││
│  │ Measures (50+ columns):                                           ││
│  │ • Scores: actual, predicted, error                               ││
│  │ • Credit: base limit, multipliers, final limit                  ││
│  │ • Risk: expected default rate, expected loss                     ││
│  │ • Payment: on-time rates, days late, late rates                 ││
│  │ • Transactions: counts, values (recent/medium/lifetime)         ││
│  │ • Trends: deterioration, velocity, improvement                   ││
│  │ • Flags: tier match, approved, excellent payer, etc.            ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  Dimension Tables:                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ gold_dim_date (170 rows)                                         ││
│  │ • date_key, full_date, year, quarter, month, day                ││
│  │ • fiscal_year, fiscal_quarter, is_weekend, is_month_end        ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ gold_dim_retailer (10,000 rows)                                  ││
│  │ • retailer_key, retailer_id, business_name, owner_name         ││
│  │ • demographics: gender, age                                      ││
│  │ • location: state, urbanization, lat/long, region              ││
│  │ • business: shop_type, years_in_business, employees            ││
│  │ • mobile money: pattern, monthly_txns                           ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ gold_dim_risk_tier (5 rows)                                      ││
│  │ • tier_key, tier_name, tier_rank                                ││
│  │ • score_min, score_max, expected_default_rate                   ││
│  │ • credit_decision (APPROVED/DECLINED)                           ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ gold_dim_credit_product (5 rows)                                 ││
│  │ • product_key, product_name                                      ││
│  │ • limit_min, limit_max, description                             ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  Relationships:                                                       │
│  • 1:* relationships (one-to-many)                                   │
│  • Single cross-filter direction                                     │
│  • 3 active relationships (date, retailer, risk tier)               │
│  • 1 inactive relationship (credit product - reference only)        │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                        VISUALIZATION LAYER                            │
│                         Power BI Dashboard                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  5 Dashboard Pages:                                                   │
│  1. Executive Overview    - High-level KPIs and trends               │
│  2. Portfolio Analysis    - Tier composition and risk breakdown      │
│  3. Credit Performance    - Model accuracy and validation            │
│  4. Retailer Deep Dive    - Individual analysis (drill-through)      │
│  5. Monitoring & Alerts   - Model health and early warnings          │
│                                                                       │
│  100+ DAX Measures:                                                   │
│  • Base metrics (retailers, exposure, defaults)                      │
│  • Time intelligence (MoM growth %, trends)                          │
│  • Risk metrics (default rates, loss rates, tier accuracy)          │
│  • Conditional formatting (colors, icons)                            │
│  • Scenario analysis (what-if calculations)                          │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Details

### 1. Compute & Processing

**Apache Spark (PySpark 3.5)**
- Distributed data processing
- Scales to billions of records
- In-memory computation for speed
- ML library (MLlib) for scalable ML

**Microsoft Fabric**
- Managed Spark compute
- Auto-scaling (10-100 nodes)
- Serverless SQL endpoint
- Integrated ML & BI

### 2. Storage

**Delta Lake**
- ACID transactions
- Time travel (versioning)
- Schema evolution
- Optimized Parquet storage
- Z-order clustering for queries

**Lakehouse Architecture**
- Bronze: Raw data (append-only)
- Silver: Cleaned data (slowly changing)
- Gold: Analytics-ready (star schema)

### 3. ML & MLOps

**Spark MLlib**
- GBT Regressor (main model)
- Vector Assembler (feature prep)
- Standard Scaler (normalization)
- Pipeline API (reproducible workflows)

**MLflow**
- Experiment tracking
- Model versioning
- Model registry
- Metrics logging
- Artifact storage

### 4. Business Intelligence

**Power BI**
- DirectQuery mode (live data)
- Star schema modeling
- DAX calculations
- Interactive dashboards
- Mobile support

---

## Data Flow & Lineage

### End-to-End Data Lineage

```
retailers.csv
     ↓
bronze_retailers (10,000 rows)
     ↓
silver_retailers (10,000 rows, cleaned)
     ↓
     ├─→ gold_ml_features (8,150 samples) ──┐
     └─→ gold_dim_retailer (10,000 rows)    │
                                             ↓
transactions.csv                    GBT Model Training
     ↓                                       ↓
bronze_transactions (75,347 rows)   gold_credit_score_predictions
     ↓                                       ↓
silver_retailer_transactions        gold_credit_limits
     ↓                                       ↓
gold_ml_features (joins) ────────→  gold_fact_credit_scoring
                                             ↓
                                    Power BI Dashboard
```

---

## Performance Optimization

### 1. Data Partitioning

```python
# Bronze layer - partition by ingestion date
.partitionBy("ingestion_date")
.write.format("delta").save()

# Silver layer - partition by year and month
.partitionBy("order_year", "order_month")
.write.format("delta").save()

# Gold layer - partition by observation_date
.partitionBy("observation_date")
.write.format("delta").save()
```

### 2. Z-Order Clustering

```sql
-- Optimize for query patterns
OPTIMIZE gold_fact_credit_scoring
ZORDER BY (date_key, retailer_key, risk_tier_key);
```

### 3. Caching Strategy

```python
# Cache frequently accessed tables
retailers_df.cache()
transactions_df.cache()

# Checkpoint long transformation chains
features_df.checkpoint()
```

### 4. Broadcast Joins

```python
# Broadcast small dimension tables
from pyspark.sql.functions import broadcast

result = fact_df.join(
    broadcast(dim_df),
    fact_df.dim_key == dim_df.dim_key
)
```

---

## Security & Governance

### 1. Data Access Control

```python
# Row-level security
.filter(col("state") == current_user().state)

# Column-level security
.drop("phone_number", "email")  # PII fields
```

### 2. Data Encryption

- At-rest: AES-256 encryption
- In-transit: TLS 1.2+
- Delta Lake encryption

### 3. Audit Logging

```python
# Track all data access
audit_log = {
    "user": current_user(),
    "timestamp": current_timestamp(),
    "action": "READ",
    "table": "gold_fact_credit_scoring",
    "rows_accessed": result.count()
}
```

---

## Scalability Considerations

### Current Scale
- 10,000 retailers
- 75,000 transactions
- 8 observation dates
- Processing time: ~15 minutes

### Future Scale (Target)
- 1,000,000 retailers
- 10,000,000 transactions
- Daily observations
- Processing time: <2 hours

### Scaling Strategy
1. Horizontal scaling (add more nodes)
2. Incremental processing (process only new data)
3. Partition pruning (read only relevant partitions)
4. Aggregation tables (pre-compute summaries)
5. Model serving endpoint (low-latency predictions)

---

## Monitoring & Alerting

### Metrics to Monitor

**Data Quality:**
- Null rate per column
- Duplicate count
- Schema changes
- Row count changes

**Model Performance:**
- Prediction accuracy (MAE, RMSE)
- Tier classification accuracy
- Default detection rate
- Feature drift

**System Performance:**
- Processing time
- Memory usage
- Error rate
- Cost per pipeline run

### Alert Triggers

- Model accuracy < 90%
- Processing time > 30 minutes
- Error rate > 1%
- Feature drift > 20%

---

## Disaster Recovery

### Backup Strategy

**Delta Lake Time Travel:**
```sql
-- Restore to previous version
RESTORE TABLE gold_fact_credit_scoring
TO VERSION AS OF 10;

-- Query historical data
SELECT * FROM gold_fact_credit_scoring
TIMESTAMP AS OF '2024-10-01';
```

**Model Versioning:**
- All models saved to MLflow registry
- Can rollback to any previous version
- A/B testing support

---

## Cost Optimization

### Storage Costs
- Bronze: $0.023/GB (raw data)
- Silver: $0.023/GB (cleaned)
- Gold: $0.023/GB (analytics)
- Total: ~100GB = $2.30/month

### Compute Costs
- Spark cluster: 10 nodes x $0.50/hour
- Pipeline runtime: 15 minutes
- Cost per run: $1.25
- Monthly (30 runs): $37.50

### Total Monthly Cost
- Storage: $2.30
- Compute: $37.50
- Power BI: $10/user
- **Total: ~$50-100/month**

---

*Last Updated: January 2025*

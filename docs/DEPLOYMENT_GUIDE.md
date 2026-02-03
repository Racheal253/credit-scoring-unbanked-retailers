# Deployment Guide
## Credit Scoring Model - Production Deployment

---

## Overview

This guide provides step-by-step instructions for deploying the credit scoring model to production, including infrastructure setup, model deployment, monitoring, and maintenance procedures.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Data Pipeline Deployment](#data-pipeline-deployment)
4. [Model Deployment](#model-deployment)
5. [API Deployment](#api-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Rollback Procedures](#rollback-procedures)
8. [Maintenance & Updates](#maintenance--updates)

---

## 1. Pre-Deployment Checklist

### ✅ Prerequisites

**Infrastructure:**
- [ ] Microsoft Fabric workspace created
- [ ] Lakehouse(s) provisioned (Bronze, Silver, Gold)
- [ ] Spark pool configured (minimum 10 nodes)
- [ ] SQL endpoint enabled
- [ ] Power BI workspace created

**Permissions:**
- [ ] Data contributor access to Fabric workspace
- [ ] SQL read/write permissions on Lakehouse
- [ ] ML experiment tracking enabled
- [ ] Power BI publish permissions

**Code & Data:**
- [ ] All notebooks tested in development
- [ ] Synthetic data generated and uploaded
- [ ] Model training completed successfully
- [ ] Power BI dashboard tested with data

**Testing:**
- [ ] Unit tests pass (pytest)
- [ ] Integration tests pass
- [ ] Model performance validated (>85% accuracy)
- [ ] Dashboard renders correctly

---

## 2. Infrastructure Setup

### Step 1: Create Microsoft Fabric Workspace

```bash
# Azure CLI commands
az login

# Create resource group
az group create \
  --name rg-credit-scoring-prod \
  --location eastus

# Create Fabric capacity
az fabric capacity create \
  --name creditscoring-fabric-prod \
  --resource-group rg-credit-scoring-prod \
  --sku F8 \
  --admin-members user@domain.com
```

### Step 2: Configure Lakehouse

**In Fabric Portal:**

1. Navigate to workspace: "CreditScoringProd"
2. Create Lakehouse:
   - Name: `Bronze`
   - Storage: Standard
   - Click "Create"
3. Repeat for `Silver` and `Gold` lakehouses

**Folder Structure:**
```
Bronze/
├─ Files/
│  └─ synthetic_data/
│     ├─ retailers.csv
│     ├─ transactions.csv
│     ├─ repayments.csv
│     └─ macro_indicators.csv
└─ Tables/
   ├─ bronze_retailers/
   ├─ bronze_transactions/
   └─ bronze_repayments/

Silver/
└─ Tables/
   ├─ silver_retailers/
   ├─ silver_retailer_transactions/
   └─ silver_repayments/

Gold/
└─ Tables/
   ├─ gold_ml_features_july_dec_2024/
   ├─ gold_credit_score_predictions/
   ├─ gold_credit_limits/
   ├─ gold_fact_credit_scoring/
   └─ gold_dim_*/
```

### Step 3: Upload Data

**Using Azure Storage Explorer:**
```bash
# Install azcopy
wget https://aka.ms/downloadazcopy-v10-linux
tar -xvf downloadazcopy-v10-linux

# Upload data
./azcopy copy \
  'data/synthetic_data/*' \
  'https://[storage-account].dfs.core.windows.net/Bronze/Files/synthetic_data/' \
  --recursive
```

**Or via Fabric UI:**
1. Open Bronze Lakehouse
2. Click "Upload" → "Upload files"
3. Select all CSV files
4. Upload to: `Files/synthetic_data/`

---

## 3. Data Pipeline Deployment

### Step 1: Import Notebooks

**Option A: Via Fabric UI**
1. Go to Workspace → New → Import notebook
2. Select each notebook file:
   - `00_Ingestion.ipynb`
   - `01_transformation.ipynb`
   - `02_Gold_ML_Features.ipynb`
   - `05_Credit_Risk_Model_Training.ipynb`
   - `Notebook_Normalized_Table_PowerBI.ipynb`
3. Attach to Spark pool

**Option B: Via REST API**
```python
import requests

workspace_id = "your-workspace-id"
api_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

with open("notebooks/00_Ingestion.ipynb", "r") as f:
    notebook_content = f.read()

payload = {
    "displayName": "00_Ingestion",
    "definition": notebook_content
}

response = requests.post(api_url, headers=headers, json=payload)
```

### Step 2: Create Pipeline

**Create Data Pipeline in Fabric:**

```json
{
  "name": "Credit_Scoring_Daily_Pipeline",
  "activities": [
    {
      "name": "Ingest_Raw_Data",
      "type": "Notebook",
      "notebook": "00_Ingestion",
      "timeout": "00:10:00"
    },
    {
      "name": "Transform_Data",
      "type": "Notebook",
      "notebook": "01_transformation",
      "dependsOn": ["Ingest_Raw_Data"],
      "timeout": "00:15:00"
    },
    {
      "name": "Feature_Engineering",
      "type": "Notebook",
      "notebook": "02_Gold_ML_Features",
      "dependsOn": ["Transform_Data"],
      "timeout": "00:20:00"
    },
    {
      "name": "Model_Training",
      "type": "Notebook",
      "notebook": "05_Credit_Risk_Model_Training",
      "dependsOn": ["Feature_Engineering"],
      "timeout": "00:30:00"
    },
    {
      "name": "Create_BI_Tables",
      "type": "Notebook",
      "notebook": "Notebook_Normalized_Table_PowerBI",
      "dependsOn": ["Model_Training"],
      "timeout": "00:10:00"
    }
  ],
  "triggers": [
    {
      "name": "Daily_2AM_Trigger",
      "type": "Schedule",
      "schedule": {
        "frequency": "Day",
        "interval": 1,
        "startTime": "2024-01-01T02:00:00Z",
        "timeZone": "W. Central Africa Standard Time"
      }
    }
  ]
}
```

**In Fabric UI:**
1. Create Data Pipeline → "Credit_Scoring_Daily_Pipeline"
2. Add activities (drag-drop notebooks)
3. Configure dependencies (arrows)
4. Add schedule trigger (2 AM daily)
5. Save and publish

### Step 3: Test Pipeline

```bash
# Trigger manual run
az pipelines run --name Credit_Scoring_Daily_Pipeline

# Monitor progress
az pipelines runs show --run-id [run-id]
```

---

## 4. Model Deployment

### Option 1: Batch Scoring (Recommended for Daily Pipeline)

**Already Included in Pipeline:**
- Model training notebook automatically scores all retailers
- Predictions saved to `gold_credit_score_predictions`
- No additional deployment needed

### Option 2: Real-Time API Endpoint

**Deploy Model as REST API:**

**A. Using Azure ML (if available):**

```python
from azureml.core import Workspace, Model
from azureml.core.webservice import AciWebservice, Webservice

# Register model
ws = Workspace.from_config()
model = Model.register(
    workspace=ws,
    model_path="models/gbt_credit_scoring_model",
    model_name="credit-scoring-gbt-v1",
    description="Credit scoring for unbanked retailers"
)

# Deploy to Azure Container Instance
deployment_config = AciWebservice.deploy_configuration(
    cpu_cores=2,
    memory_gb=4,
    auth_enabled=True
)

service = Model.deploy(
    workspace=ws,
    name="credit-scoring-api",
    models=[model],
    inference_config=inference_config,
    deployment_config=deployment_config
)

service.wait_for_deployment(show_output=True)
print(f"Scoring URI: {service.scoring_uri}")
```

**B. Using Flask API (Simple Deployment):**

**Create `app.py`:**

```python
from flask import Flask, request, jsonify
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Load model once at startup
spark = SparkSession.builder.appName("CreditScoringAPI").getOrCreate()
model = PipelineModel.load("models/gbt_credit_scoring_model")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model_loaded": True})

@app.route('/api/v1/score', methods=['POST'])
def score_retailer():
    """
    Score a single retailer
    
    Request Body:
    {
        "retailer_id": "RTL_001234",
        "observation_date": "2024-10-15"
    }
    
    Response:
    {
        "retailer_id": "RTL_001234",
        "credit_score": 785,
        "risk_tier": "Platinum",
        "credit_limit": 850000,
        "approval_status": "APPROVED",
        "timestamp": "2024-10-15T10:30:00Z"
    }
    """
    try:
        data = request.json
        retailer_id = data['retailer_id']
        observation_date = data['observation_date']
        
        # Generate features for this retailer
        features_df = generate_features(retailer_id, observation_date)
        
        # Make prediction
        predictions = model.transform(features_df)
        
        # Extract result
        result = predictions.select(
            "retailer_id",
            "predicted_credit_score",
            "predicted_risk_tier",
            "final_credit_limit",
            "approved_flag"
        ).first()
        
        return jsonify({
            "retailer_id": result.retailer_id,
            "credit_score": int(result.predicted_credit_score),
            "risk_tier": result.predicted_risk_tier,
            "credit_limit": int(result.final_credit_limit),
            "approval_status": "APPROVED" if result.approved_flag else "DECLINED",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"Scoring error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/batch-score', methods=['POST'])
def batch_score():
    """
    Score multiple retailers
    
    Request Body:
    {
        "retailer_ids": ["RTL_001", "RTL_002", ...],
        "observation_date": "2024-10-15"
    }
    """
    data = request.json
    retailer_ids = data['retailer_ids']
    observation_date = data['observation_date']
    
    # Generate features for all retailers
    features_df = generate_batch_features(retailer_ids, observation_date)
    
    # Make predictions
    predictions = model.transform(features_df)
    
    # Convert to JSON
    results = predictions.select(
        "retailer_id",
        "predicted_credit_score",
        "predicted_risk_tier",
        "final_credit_limit"
    ).collect()
    
    return jsonify({
        "count": len(results),
        "predictions": [row.asDict() for row in results]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Deploy API:**

```bash
# Build Docker image
docker build -t credit-scoring-api:v1 .

# Push to container registry
docker tag credit-scoring-api:v1 myregistry.azurecr.io/credit-scoring-api:v1
docker push myregistry.azurecr.io/credit-scoring-api:v1

# Deploy to Azure Container Apps
az containerapp create \
  --name credit-scoring-api \
  --resource-group rg-credit-scoring-prod \
  --image myregistry.azurecr.io/credit-scoring-api:v1 \
  --target-port 5000 \
  --ingress external \
  --cpu 2 --memory 4Gi
```

---

## 5. Power BI Dashboard Deployment

### Step 1: Publish Dashboard

**From Power BI Desktop:**
1. Open `Credit_Scoring_Dashboard.pbix`
2. File → Publish → "CreditScoringProd" workspace
3. Configure dataset refresh schedule:
   - Frequency: Daily
   - Time: 3:00 AM (after pipeline completes)
   - Credentials: Service principal or OAuth

### Step 2: Configure Security

**Row-Level Security (RLS):**

**In Power BI Desktop:**
1. Modeling → Manage Roles
2. Create role: "Regional Manager"
   ```dax
   [state] = USERNAME()
   ```
3. Create role: "Executive"
   ```dax
   TRUE()  // See all data
   ```

**In Power BI Service:**
1. Navigate to dataset settings
2. Security → Add members to roles
3. Assign users to appropriate roles

### Step 3: Share Dashboard

**Create App:**
1. Workspace → Create App
2. Name: "Credit Scoring Analytics"
3. Add dashboard pages
4. Set permissions:
   - Viewers: All credit team members
   - Contributors: Credit managers
   - Admins: Data science team
5. Publish

---

## 6. Monitoring Setup

### Application Insights Integration

**Add to Notebooks:**

```python
from applicationinsights import TelemetryClient
import logging

# Initialize App Insights
tc = TelemetryClient('YOUR_INSTRUMENTATION_KEY')

# Track pipeline start
tc.track_event('Pipeline_Started', {
    'pipeline': 'Credit_Scoring_Daily',
    'date': str(datetime.now())
})

# Track model performance
tc.track_metric('Model_Accuracy', tier_accuracy)
tc.track_metric('Model_MAE', mae)
tc.track_metric('Processing_Time_Minutes', processing_time)

# Track errors
try:
    # ... pipeline logic
except Exception as e:
    tc.track_exception()
    logging.error(f"Pipeline failed: {str(e)}")

# Flush telemetry
tc.flush()
```

### Set Up Alerts

**In Azure Portal:**

1. **Model Performance Alert:**
   - Metric: `Model_Accuracy`
   - Condition: Less than 90%
   - Action: Email data science team

2. **Pipeline Failure Alert:**
   - Metric: `Pipeline_Status`
   - Condition: Failed
   - Action: Email ops team + SMS

3. **Processing Time Alert:**
   - Metric: `Processing_Time_Minutes`
   - Condition: Greater than 30
   - Action: Email performance team

### Create Monitoring Dashboard

**In Power BI (separate from main dashboard):**

**Metrics to Track:**
- Pipeline success rate (last 30 days)
- Average processing time
- Model performance trends (MAE, RMSE, Accuracy)
- Data quality metrics (null rates, duplicate counts)
- API response times (if using real-time API)
- Cost tracking

---

## 7. Rollback Procedures

### Rollback Data Pipeline

**If new pipeline version fails:**

```python
# Restore tables to previous version using Delta Lake time travel
spark.sql("""
    RESTORE TABLE gold_fact_credit_scoring
    TO VERSION AS OF 10
""")

# Or restore to specific timestamp
spark.sql("""
    RESTORE TABLE gold_fact_credit_scoring
    TO TIMESTAMP AS OF '2024-10-14 02:00:00'
""")
```

### Rollback Model

**Switch to previous model version:**

```python
# In MLflow registry, promote previous version to Production
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Demote current production model
client.transition_model_version_stage(
    name="credit-scoring-gbt",
    version=5,  # Current version
    stage="Archived"
)

# Promote previous model to production
client.transition_model_version_stage(
    name="credit-scoring-gbt",
    version=4,  # Previous stable version
    stage="Production"
)
```

### Rollback Power BI Dashboard

**Restore previous version:**
1. Go to Power BI workspace
2. Dataset settings → Update history
3. Select previous version
4. Click "Restore"

---

## 8. Maintenance & Updates

### Weekly Tasks

- [ ] Review pipeline execution logs
- [ ] Check model performance metrics
- [ ] Validate data quality reports
- [ ] Review alert notifications

### Monthly Tasks

- [ ] Retrain model with latest data
- [ ] A/B test new model vs. production
- [ ] Update feature engineering if needed
- [ ] Review and optimize query performance
- [ ] Update documentation

### Quarterly Tasks

- [ ] Conduct model audit
- [ ] Review feature importance changes
- [ ] Evaluate new data sources
- [ ] Assess infrastructure costs
- [ ] Plan capacity upgrades

### Model Retraining Schedule

**When to Retrain:**
- Scheduled: Monthly (always)
- Triggered: When accuracy drops below 90%
- Triggered: When feature drift detected (>20%)
- Ad-hoc: When new features added

**Retraining Process:**
1. Generate new features with latest data
2. Train new model version
3. Evaluate on hold-out test set
4. Compare to production model
5. If better: Promote to staging
6. Run A/B test for 1 week
7. If successful: Promote to production
8. Archive old model

---

## 9. Disaster Recovery

### Backup Strategy

**Delta Lake:**
- Automatic versioning (30-day retention)
- Daily snapshots to separate storage account
- Cross-region replication

**Model Registry:**
- All models saved to MLflow
- Artifacts backed up to Azure Blob Storage
- Version control in Git

**Power BI:**
- .pbix files stored in Git repository
- Daily export of dataset definitions

### Recovery Procedures

**Scenario 1: Complete Lakehouse Loss**

```bash
# Restore from Azure Blob Storage backup
azcopy copy \
  'https://backup.blob.core.windows.net/lakehouse-backup/gold/*' \
  'https://prod.dfs.core.windows.net/gold/' \
  --recursive
```

**Scenario 2: Model Corruption**

```python
# Download from MLflow artifact store
import mlflow

model_uri = "models:/credit-scoring-gbt/4"  # Last known good version
local_path = mlflow.artifacts.download_artifacts(model_uri)

# Re-upload to production
mlflow.pyfunc.log_model(...)
```

**Scenario 3: Pipeline Failure**

1. Check logs in Application Insights
2. Identify failed notebook
3. Fix issue in development
4. Test fix
5. Deploy to production
6. Manually trigger pipeline
7. Validate outputs

---

## 10. Production Checklist

### Pre-Launch

- [ ] All notebooks tested and validated
- [ ] Model performance meets targets (>85% accuracy)
- [ ] Dashboard tested with production data
- [ ] Security and RLS configured
- [ ] Monitoring and alerts set up
- [ ] Backup and recovery tested
- [ ] Documentation complete
- [ ] Team trained on operations

### Go-Live

- [ ] Schedule pipeline to run daily at 2 AM
- [ ] Notify stakeholders of launch
- [ ] Monitor first 3 runs closely
- [ ] Conduct user acceptance testing
- [ ] Gather feedback from credit team

### Post-Launch (First 30 Days)

- [ ] Daily monitoring of model performance
- [ ] Weekly review meetings with stakeholders
- [ ] Address user feedback promptly
- [ ] Document lessons learned
- [ ] Plan enhancements based on usage

---

## Support & Escalation

### Contact Information

**Level 1: Dashboard Issues**
- Contact: BI Team
- Email: bi-support@planinvest.ng
- Response Time: 4 hours

**Level 2: Data Pipeline Issues**
- Contact: Data Engineering Team
- Email: data-eng@planinvest.ng
- Response Time: 2 hours

**Level 3: Model Performance Issues**
- Contact: Data Science Team
- Email: data-science@planinvest.ng
- Response Time: 1 hour

**Critical (Production Down):**
- Contact: On-Call Engineer
- Phone: +234-XXX-XXX-XXXX
- Response Time: 15 minutes

---

**Document Version:** 1.0  
**Last Updated:** January 2025  
**Next Review:** April 2025

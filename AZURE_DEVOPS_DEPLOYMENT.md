# Deploy to Snowflake Using Azure DevOps (No Docker Needed Locally)

**Use Azure DevOps to build and push Docker images - no local Docker installation required!**

---

## Prerequisites

- ✅ Azure DevOps project
- ✅ Repository pushed to Azure Repos (or GitHub connected to Azure DevOps)
- ✅ Snowflake infrastructure set up (compute pool, image repository)
- ✅ Snowflake credentials

---

## Step 1: Set Up Azure DevOps Pipeline

### 1.1 Push Code to Azure Repos

```bash
# Initialize git if not done
git init
git add .
git commit -m "Initial commit - LTC Insurance API"

# Add Azure DevOps remote (get this from Azure DevOps)
git remote add origin https://dev.azure.com/<your-org>/<your-project>/_git/<your-repo>

# Push to Azure DevOps
git push -u origin main
```

---

### 1.2 Create Service Connection to Snowflake

**In Azure DevOps:**

1. Go to **Project Settings** (bottom left)
2. Click **Service connections** (under Pipelines)
3. Click **New service connection**
4. Select **Docker Registry**
5. Fill in:
   - **Registry type**: Others
   - **Docker Registry**: `https://bnmbckj-vi07646.registry.snowflakecomputing.com`
   - **Docker ID**: Your Snowflake username (e.g., `VIDYASURESH`)
   - **Password**: Your Snowflake password
   - **Service connection name**: `SnowflakeDockerRegistry`
6. Click **Save**

---

### 1.3 Create Pipeline

**In Azure DevOps:**

1. Go to **Pipelines** → **Pipelines**
2. Click **New Pipeline**
3. Select **Azure Repos Git**
4. Select your repository
5. Select **Existing Azure Pipelines YAML file**
6. Choose `/azure-pipelines.yml`
7. Click **Run**

The pipeline will automatically:
- ✅ Build the Docker image
- ✅ Tag it with timestamp version
- ✅ Push to Snowflake registry
- ✅ Display deployment instructions

---

## Step 2: Monitor Build

The pipeline will run automatically. You'll see:

```
Stage 1: Build and Push Docker Image
  ✓ Set Build Version
  ✓ Build Docker Image
  ✓ Login to Snowflake Registry
  ✓ Tag Image for Snowflake
  ✓ Push to Snowflake Registry
  ✓ Deployment Info

Stage 2: Verification Instructions
  ✓ Show Verification Steps
```

**Time:** ~5-10 minutes

---

## Step 3: Get Image Version

After the pipeline completes, check the build output:

```
============================================
DEPLOYMENT INFORMATION
============================================
Registry: bnmbckj-vi07646.registry.snowflakecomputing.com
Image: ltc_api_repo/images/fastapi_repo/ltc-api:20241018.143022
Full path: bnmbckj-vi07646.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo/ltc-api:20241018.143022
```

**Save the image tag** (e.g., `20241018.143022`)

---

## Step 4: Verify Image in Snowflake

Run in Snowflake:

```sql
USE DATABASE LTC_API_REPO;
USE SCHEMA IMAGES;

SHOW IMAGES IN IMAGE REPOSITORY FASTAPI_REPO;
-- You should see your image with the version tag
```

---

## Step 5: Deploy Service in Snowflake

### 5.1 Generate JWT Secret

```bash
# On your local machine or in Azure DevOps
python -c "import secrets; print(secrets.token_hex(32))"
```

Save the output.

---

### 5.2 Create Service

**In Snowflake, run this (UPDATE THE VALUES):**

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE LTC_INSURANCE;
USE SCHEMA ANALYTICS;

CREATE SERVICE FASTAPI_SERVICE
  IN COMPUTE POOL LTC_API_POOL
  FROM SPECIFICATION $$
    spec:
      containers:
      - name: fastapi
        image: /ltc_api_repo/images/fastapi_repo/ltc-api:latest  # Or use specific version tag
        env:
          # ⚠️ UPDATE THESE:
          SNOWFLAKE_ACCOUNT: BNMBCKJ-VI07646
          SNOWFLAKE_USER: LTC_API_SERVICE
          SNOWFLAKE_PASSWORD: <service_account_password>  # From infrastructure setup
          SNOWFLAKE_ROLE: LTC_API_SERVICE_ROLE
          SNOWFLAKE_WAREHOUSE: COMPUTE_WH
          SNOWFLAKE_DATABASE: LTC_INSURANCE
          SNOWFLAKE_SCHEMA: ANALYTICS
          JWT_SECRET_KEY: <paste_jwt_secret_from_5.1>
          JWT_ALGORITHM: HS256
          JWT_EXPIRATION_HOURS: "1"
          API_VERSION: v1
          ENVIRONMENT: production
          LOG_LEVEL: INFO
        resources:
          requests:
            memory: 2Gi
            cpu: "1"
          limits:
            memory: 4Gi
            cpu: "2"
      endpoints:
      - name: api
        port: 8080
        public: true
  $$
  MIN_INSTANCES = 1
  MAX_INSTANCES = 3;
```

**This will take 2-5 minutes.**

---

## Step 6: Monitor Service Deployment

```sql
-- Check service status
SHOW SERVICES IN SCHEMA LTC_INSURANCE.ANALYTICS;

-- Get detailed status (wait for READY)
CALL SYSTEM$GET_SERVICE_STATUS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE');

-- View logs
CALL SYSTEM$GET_SERVICE_LOGS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE', '0', 'fastapi', 100);
```

**Wait for status = READY** (2-5 minutes)

---

## Step 7: Get API Endpoint

```sql
SHOW ENDPOINTS IN SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE;
```

**Copy the `ingress_url`:**
```
https://<unique-id>.snowflakecomputing.app
```

---

## Step 8: Test Deployment

```powershell
# Set endpoint
$ENDPOINT = "https://<your-ingress-url>"

# Test health
curl.exe "$ENDPOINT/health"

# Test ready
curl.exe "$ENDPOINT/ready"

# Test login
curl.exe -X POST "$ENDPOINT/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"LTCInsurance2024!"}'

# Test API (with token from above)
$TOKEN = "<your_token>"
curl.exe -H "Authorization: Bearer $TOKEN" `
  "$ENDPOINT/api/v1/policies?limit=5"
```

---

## 🎉 Deployment Complete!

Your API is now running in Snowflake without ever installing Docker locally!

---

## Future Updates

### Deploy New Version

Just push to main branch:

```bash
# Make changes
git add .
git commit -m "Update API"
git push origin main
```

Azure DevOps will automatically:
1. Build new image
2. Push to Snowflake with new version tag
3. Display the tag in build output

Then update the service in Snowflake:

```sql
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
FROM SPECIFICATION $$
  spec:
    containers:
    - name: fastapi
      image: /ltc_api_repo/images/fastapi_repo/ltc-api:<new-version-tag>
      -- rest stays the same
$$;
```

---

## Alternative: Manual Trigger

You can also trigger builds manually:

1. Go to **Pipelines** in Azure DevOps
2. Select your pipeline
3. Click **Run pipeline**
4. Select branch and click **Run**

---

## Troubleshooting

### Issue: Docker login fails

**Fix in Azure DevOps:**
1. Go to Service connections
2. Edit `SnowflakeDockerRegistry`
3. Verify username/password are correct
4. Test connection

---

### Issue: Build fails with "unauthorized"

**Fix:**
Verify the service connection has access to Snowflake registry:
- Username: Your Snowflake user
- Password: Your Snowflake password
- Registry URL must include `https://`

---

### Issue: Image not found in Snowflake

**Check:**
```sql
SHOW IMAGES IN IMAGE REPOSITORY LTC_API_REPO.IMAGES.FASTAPI_REPO;
```

If empty, check Azure DevOps build logs for push errors.

---

## Benefits of Azure DevOps Approach

✅ **No local Docker** - Builds in cloud  
✅ **Automated** - Push code = build + deploy  
✅ **Versioned** - Automatic timestamp-based tags  
✅ **Auditable** - All builds logged  
✅ **Fast** - Azure build agents are powerful  
✅ **Team-friendly** - Anyone can deploy by pushing code  

---

## Next Steps

1. ✅ Set up service connection
2. ✅ Create pipeline from `azure-pipelines.yml`
3. ✅ Run pipeline (builds image)
4. ✅ Create service in Snowflake
5. ✅ Test API endpoint

**Total time: ~15 minutes** (no Docker Desktop needed!)


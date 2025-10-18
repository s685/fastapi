# Deployment Guide - Snowpark Container Services (SPCS)

Deploy the LTC Insurance Data API to Snowflake using **Azure DevOps** (no local Docker needed).

## 📋 Prerequisites

### Snowflake Requirements
- Snowflake Enterprise Edition or higher
- ACCOUNTADMIN privileges (for initial setup)
- Snowpark Container Services enabled for your account
- A running warehouse (e.g., COMPUTE_WH)

### Azure DevOps Requirements
- Azure DevOps project
- Repository access (Azure Repos or connected GitHub)
- Permissions to create pipelines and service connections

### Local Requirements (Minimal)
- Git (for pushing code)
- SnowSQL or Snowflake UI access (for SQL execution)
- Python (for generating JWT secret)

## 🚀 Deployment Overview

**Deployment Method:** Azure DevOps CI/CD Pipeline

**Flow:**
1. Push code to Azure Repos
2. Azure DevOps builds Docker image
3. Pipeline pushes image to Snowflake registry
4. Create service in Snowflake
5. API is live!

**Benefits:**
- ✅ No local Docker installation needed
- ✅ Automated builds on every push
- ✅ Versioned deployments
- ✅ Team-friendly

---

## 🚀 Deployment Steps

### Step 1: Set Up Azure DevOps

#### 1.1 Push Code to Azure Repos

```bash
# Initialize git
git init
git add .
git commit -m "Initial commit - LTC Insurance API"

# Add Azure DevOps remote (get URL from your Azure DevOps project)
git remote add origin https://dev.azure.com/<org>/<project>/_git/<repo>

# Push to Azure DevOps
git push -u origin main
```

#### 1.2 Create Service Connection

**In Azure DevOps:**
1. **Project Settings** → **Service connections**
2. **New service connection** → **Docker Registry**
3. Fill in:
   - Registry type: **Others**
   - Docker Registry: `https://bnmbckj-vi07646.registry.snowflakecomputing.com`
   - Docker ID: Your Snowflake username
   - Password: Your Snowflake password
   - Service connection name: `SnowflakeDockerRegistry`
4. **Save**

#### 1.3 Create Pipeline

1. **Pipelines** → **New Pipeline**
2. Select **Azure Repos Git** (or your source)
3. Select your repository
4. Choose **Existing Azure Pipelines YAML file**
5. Path: `/azure-pipelines.yml`
6. Click **Run**

**The pipeline will automatically build and push the Docker image!**

### Step 2: Execute Snowflake Setup Scripts

Run these scripts in order using SnowSQL or Snowflake UI:

#### 2.1 Database and Schema Setup

```bash
snowsql -a <account> -u <username> -f snowflake/01_setup_database.sql
```

Or in Snowflake UI:
```sql
-- Copy and execute contents of snowflake/01_setup_database.sql
```

This creates:
- `LTC_INSURANCE` database with `ANALYTICS` schema
- `LTC_API_REPO` database with `IMAGES` schema

#### 2.2 Verify Data Tables

```bash
snowsql -a <account> -u <username> -f snowflake/02_create_tables.sql
```

This verifies your existing data tables are accessible.

#### 2.3 Create API Users Table

```bash
snowsql -a <account> -u <username> -f snowflake/03_create_users.sql
```

This creates:
- `API_USERS` table for authentication
- Sample users (admin, analyst, viewer)

**Important**: Update user carrier access based on your actual carriers:

```sql
-- Get available carriers
SELECT DISTINCT CARRIER_NAME 
FROM LTC_INSURANCE.ANALYTICS.POLICY_MONTHLY_SNAPSHOT_FACT 
ORDER BY CARRIER_NAME;

-- Update analyst user with specific carriers
UPDATE LTC_INSURANCE.ANALYTICS.API_USERS
SET CARRIER_ACCESS = 'YourCarrier1,YourCarrier2'
WHERE USERNAME = 'analyst';

-- Update viewer user
UPDATE LTC_INSURANCE.ANALYTICS.API_USERS
SET CARRIER_ACCESS = 'YourCarrier1'
WHERE USERNAME = 'viewer';
```

#### 2.4 Optional: Secure Views

```bash
snowsql -a <account> -u <username> -f snowflake/04_create_secure_views.sql
```

Secure views provide database-level RBAC. This is optional as RBAC is primarily implemented in the application layer.

#### 2.5 SPCS Infrastructure Setup

```bash
snowsql -a <account> -u <username> -f snowflake/05_spcs_setup.sql
```

This creates:
- Image repository for Docker images
- Compute pool for running containers
- Service account (`LTC_API_SERVICE`)
- Necessary roles and grants

**Save the repository URL** shown in the output. Format:
```
<org>-<account>.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo
```

#### 2.6 RBAC Configuration

```bash
snowsql -a <account> -u <username> -f snowflake/06_rbac_grants.sql
```

This sets up role-based permissions for API users.

#### 2.7 Verification

```bash
snowsql -a <account> -u <username> -f snowflake/07_verification.sql
```

Verify all components are set up correctly.

### Step 3: Build and Push Docker Image

#### 3.1 Build Docker Image

```bash
# Build the image
docker build -t ltc-fastapi:v1 .

# Verify image was created
docker images | grep ltc-fastapi
```

#### 3.2 Authenticate to Snowflake Registry

```bash
# Replace <org>-<account> with your Snowflake account identifier
# Use your Snowflake username and password
docker login <org>-<account>.registry.snowflakecomputing.com -u <username>

# Enter password when prompted
```

Example:
```bash
docker login myorg-myaccount.registry.snowflakecomputing.com -u john_doe
```

#### 3.3 Tag Image for Snowflake

```bash
# Tag the image with full Snowflake registry path
docker tag ltc-fastapi:v1 \
  <org>-<account>.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo/ltc-fastapi:v1
```

Example:
```bash
docker tag ltc-fastapi:v1 \
  myorg-myaccount.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo/ltc-fastapi:v1
```

#### 3.4 Push Image to Snowflake

```bash
# Push the image
docker push <org>-<account>.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo/ltc-fastapi:v1
```

This may take several minutes depending on your internet speed.

#### 3.5 Verify Image in Snowflake

```sql
USE DATABASE LTC_API_REPO;
USE SCHEMA IMAGES;

SHOW IMAGES IN IMAGE REPOSITORY FASTAPI_REPO;
```

You should see your `ltc-fastapi:v1` image listed.

### Step 4: Create SPCS Service

#### 4.1 Prepare Service Specification

Create a file `service_spec.sql` with the following content:

```sql
USE ROLE ACCOUNTADMIN;

CREATE SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
  IN COMPUTE POOL LTC_API_POOL
  FROM SPECIFICATION $$
    spec:
      containers:
      - name: fastapi
        image: /ltc_api_repo/images/fastapi_repo/ltc-fastapi:v1
        env:
          SNOWFLAKE_ACCOUNT: <your_account>
          SNOWFLAKE_USER: LTC_API_SERVICE
          SNOWFLAKE_PASSWORD: <service_password_from_step_2.5>
          SNOWFLAKE_ROLE: LTC_API_SERVICE_ROLE
          SNOWFLAKE_WAREHOUSE: COMPUTE_WH
          SNOWFLAKE_DATABASE: LTC_INSURANCE
          SNOWFLAKE_SCHEMA: ANALYTICS
          JWT_SECRET_KEY: <your_jwt_secret_from_step_1>
          JWT_ALGORITHM: HS256
          JWT_EXPIRE_MINUTES: "60"
          API_VERSION: v1
          API_TITLE: LTC Insurance Data API
          ENVIRONMENT: production
          LOG_LEVEL: INFO
          MAX_PAGE_SIZE: "1000"
          DEFAULT_PAGE_SIZE: "100"
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
  MAX_INSTANCES = 3
  COMMENT = 'LTC Insurance FastAPI service';
```

#### 4.2 Update Configuration

Replace placeholders in the specification:
- `<your_account>`: Your Snowflake account identifier
- `<service_password_from_step_2.5>`: Password for LTC_API_SERVICE user
- `<your_jwt_secret_from_step_1>`: JWT secret key generated in Step 1

#### 4.3 Execute Service Creation

```bash
snowsql -a <account> -u <username> -f service_spec.sql
```

Or execute in Snowflake UI.

### Step 5: Verify Deployment

#### 5.1 Check Service Status

```sql
-- Show all services
SHOW SERVICES IN SCHEMA LTC_INSURANCE.ANALYTICS;

-- Get detailed status
CALL SYSTEM$GET_SERVICE_STATUS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE');
```

Wait until status shows `READY`. This may take 2-5 minutes.

#### 5.2 Get API Endpoint

```sql
SHOW ENDPOINTS IN SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE;
```

Copy the `ingress_url` - this is your public API endpoint.

Example output:
```
ingress_url: https://abc123-analytics.snowflakecomputing.app
```

#### 5.3 View Service Logs

```sql
-- Get latest logs
CALL SYSTEM$GET_SERVICE_LOGS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE', '0', 'fastapi', 100);
```

### Step 6: Test the API

#### 6.1 Test Health Endpoint

```bash
# Replace with your actual endpoint URL
export API_URL="https://abc123-analytics.snowflakecomputing.app"

# Test health
curl $API_URL/health

# Expected response:
# {"status":"healthy","timestamp":"2024-..."}
```

#### 6.2 Test Readiness

```bash
curl $API_URL/ready

# Expected response:
# {"status":"ready","snowflake":"connected","timestamp":"2024-..."}
```

#### 6.3 Test Authentication

```bash
# Login
curl -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "LTCInsurance2024!"
  }'

# Save the access_token from response
export TOKEN="<access_token_here>"
```

#### 6.4 Test Data Endpoints

```bash
# Get policies
curl "$API_URL/api/v1/policies?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Get specific policy
curl "$API_URL/api/v1/policies/12345" \
  -H "Authorization: Bearer $TOKEN"

# Get policy summary
curl "$API_URL/api/v1/policies/analytics/summary" \
  -H "Authorization: Bearer $TOKEN"

# Get claims
curl "$API_URL/api/v1/claims?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 7: Access Documentation

```bash
# Open interactive API documentation
open $API_URL/api/v1/docs

# Or ReDoc
open $API_URL/api/v1/redoc
```

## 🔧 Post-Deployment Configuration

### Update Service Configuration

If you need to update environment variables or resources:

```sql
-- Suspend service
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE SUSPEND;

-- Update service specification
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
  FROM SPECIFICATION $$
    -- Updated spec here
  $$;

-- Resume service
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE RESUME;
```

### Scale Service

```sql
-- Adjust instance count
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
  SET MIN_INSTANCES = 2, MAX_INSTANCES = 5;
```

### Update Docker Image

```bash
# Build new version
docker build -t ltc-fastapi:v2 .

# Tag and push
docker tag ltc-fastapi:v2 \
  <registry_url>/ltc_api_repo/images/fastapi_repo/ltc-fastapi:v2
docker push <registry_url>/ltc_api_repo/images/fastapi_repo/ltc-fastapi:v2

# Update service
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
  FROM SPECIFICATION $$
    spec:
      containers:
      - name: fastapi
        image: /ltc_api_repo/images/fastapi_repo/ltc-fastapi:v2
        # ... rest of spec
  $$;
```

## 📊 Monitoring and Maintenance

### View Logs

```sql
-- Get latest 500 lines
CALL SYSTEM$GET_SERVICE_LOGS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE', '0', 'fastapi', 500);

-- Stream logs in real-time (in SnowSQL)
!set output_format=plain
CALL SYSTEM$GET_SERVICE_LOGS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE', '0', 'fastapi', 100);
```

### Monitor Resource Usage

```sql
-- Service details
DESC SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE;

-- Compute pool utilization
SHOW COMPUTE POOLS;
DESC COMPUTE POOL LTC_API_POOL;
```

### Suspend/Resume Service

```sql
-- Suspend (stops billing, but preserves service)
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE SUSPEND;

-- Resume
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE RESUME;
```

## 🚨 Troubleshooting

### Service Won't Start

```sql
-- Check status
CALL SYSTEM$GET_SERVICE_STATUS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE');

-- Check logs for errors
CALL SYSTEM$GET_SERVICE_LOGS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE', '0', 'fastapi', 500);
```

Common issues:
- Invalid environment variables (check JWT_SECRET_KEY, passwords)
- Insufficient compute pool resources
- Network connectivity issues

### "Image not found" Error

```sql
-- Verify image exists
SHOW IMAGES IN IMAGE REPOSITORY LTC_API_REPO.IMAGES.FASTAPI_REPO;

-- Check image path in service spec
SHOW SERVICES;
```

### Authentication Failures

```sql
-- Verify API_USERS table
SELECT * FROM LTC_INSURANCE.ANALYTICS.API_USERS;

-- Check service account permissions
SHOW GRANTS TO USER LTC_API_SERVICE;
SHOW GRANTS TO ROLE LTC_API_SERVICE_ROLE;
```

### Performance Issues

```sql
-- Increase resources
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
  FROM SPECIFICATION $$
    spec:
      containers:
      - name: fastapi
        resources:
          requests:
            memory: 4Gi
            cpu: "2"
          limits:
            memory: 8Gi
            cpu: "4"
        # ... rest of spec
  $$;

-- Scale instances
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
  SET MIN_INSTANCES = 2, MAX_INSTANCES = 5;
```

## 🔐 Security Best Practices

1. **Change Default Passwords**
   ```sql
   UPDATE LTC_INSURANCE.ANALYTICS.API_USERS
   SET PASSWORD_HASH = '<new_bcrypt_hash>'
   WHERE USERNAME IN ('admin', 'analyst', 'viewer');
   ```

2. **Rotate JWT Secret**
   - Generate new secret: `openssl rand -hex 32`
   - Update service specification
   - Restart service

3. **Limit Endpoint Access**
   ```sql
   -- Make endpoint private (access via Snowflake only)
   ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE
     SET endpoints[0].public = false;
   ```

4. **Enable Audit Logging**
   - All API access is logged in structured JSON format
   - Access logs via `SYSTEM$GET_SERVICE_LOGS`
   - Consider exporting logs to external SIEM

## 💰 Cost Optimization

- **Auto-suspend**: Compute pool automatically suspends after 1 hour of inactivity
- **Right-sizing**: Start with small instances, scale as needed
- **Instance limits**: Set MAX_INSTANCES to control costs
- **Monitoring**: Track usage with Snowflake's query history

```sql
-- Monitor service costs
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
WHERE SERVICE_TYPE = 'CONTAINER_SERVICES'
  AND START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY START_TIME DESC;
```

## 📚 Additional Resources

- [Snowpark Container Services Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)

## 🆘 Support

For issues or questions:
1. Check troubleshooting section above
2. Review service logs
3. Consult Snowflake support
4. [Your support contact/process]

---

## Quick Reference Commands

```bash
# Check service status
CALL SYSTEM$GET_SERVICE_STATUS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE');

# Get endpoint
SHOW ENDPOINTS IN SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE;

# View logs
CALL SYSTEM$GET_SERVICE_LOGS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE', '0', 'fastapi', 100);

# Suspend service
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE SUSPEND;

# Resume service
ALTER SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE RESUME;

# Drop service (careful!)
DROP SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE;
```


-- ============================================================================
-- Step 5: Snowpark Container Services (SPCS) Setup
-- ============================================================================
-- Description: Set up SPCS infrastructure for deploying the FastAPI container
-- Prerequisites: Snowflake Enterprise Edition or higher, SPCS enabled

-- Switch to ACCOUNTADMIN role (required for SPCS setup)
USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- Create Image Repository
-- ============================================================================
USE DATABASE LTC_API_REPO;
USE SCHEMA IMAGES;

-- Create image repository for storing Docker images
CREATE IMAGE REPOSITORY IF NOT EXISTS FASTAPI_REPO
    COMMENT = 'Repository for LTC Insurance FastAPI container images';

-- Show repository details and get the registry URL
SHOW IMAGE REPOSITORIES;

-- Get the repository URL for docker push
-- Format: <org>-<account>.registry.snowflakecomputing.com/ltc_api_repo/images/fastapi_repo

-- ============================================================================
-- Create Compute Pool
-- ============================================================================
-- Create compute pool for running the API service

CREATE COMPUTE POOL IF NOT EXISTS LTC_API_POOL
    MIN_NODES = 1
    MAX_NODES = 3
    INSTANCE_FAMILY = CPU_X64_S
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 3600
    COMMENT = 'Compute pool for LTC Insurance FastAPI service';

-- Check compute pool status
SHOW COMPUTE POOLS;
DESC COMPUTE POOL LTC_API_POOL;

-- ============================================================================
-- Create Service Role and Grants
-- ============================================================================

-- Create role for the API service
CREATE ROLE IF NOT EXISTS LTC_API_SERVICE_ROLE
    COMMENT = 'Role for LTC Insurance FastAPI service';

-- Grant necessary privileges to service role
GRANT USAGE ON DATABASE LTC_INSURANCE TO ROLE LTC_API_SERVICE_ROLE;
GRANT USAGE ON SCHEMA LTC_INSURANCE.ANALYTICS TO ROLE LTC_API_SERVICE_ROLE;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE LTC_API_SERVICE_ROLE;

-- Grant access to data tables
GRANT SELECT ON TABLE LTC_INSURANCE.ANALYTICS.POLICY_MONTHLY_SNAPSHOT_FACT 
    TO ROLE LTC_API_SERVICE_ROLE;
GRANT SELECT ON TABLE LTC_INSURANCE.ANALYTICS.CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT 
    TO ROLE LTC_API_SERVICE_ROLE;

-- Grant access to API_USERS table
GRANT SELECT ON TABLE LTC_INSURANCE.ANALYTICS.API_USERS TO ROLE LTC_API_SERVICE_ROLE;
GRANT UPDATE ON TABLE LTC_INSURANCE.ANALYTICS.API_USERS TO ROLE LTC_API_SERVICE_ROLE;

-- Grant compute pool usage
GRANT USAGE ON COMPUTE POOL LTC_API_POOL TO ROLE LTC_API_SERVICE_ROLE;

-- Grant image repository access
GRANT READ ON IMAGE REPOSITORY LTC_API_REPO.IMAGES.FASTAPI_REPO 
    TO ROLE LTC_API_SERVICE_ROLE;

-- Create service account user
CREATE USER IF NOT EXISTS LTC_API_SERVICE
    PASSWORD = 'ChangeThisPassword123!'
    DEFAULT_ROLE = LTC_API_SERVICE_ROLE
    DEFAULT_WAREHOUSE = COMPUTE_WH
    COMMENT = 'Service account for LTC Insurance FastAPI';

-- Grant role to service user
GRANT ROLE LTC_API_SERVICE_ROLE TO USER LTC_API_SERVICE;

-- ============================================================================
-- Service Specification
-- ============================================================================
-- After pushing Docker image, create the service with this spec:

/*
-- Replace <REGISTRY_URL> with your registry URL from SHOW IMAGE REPOSITORIES
-- Replace <SNOWFLAKE_PASSWORD> with the LTC_API_SERVICE password

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
          SNOWFLAKE_PASSWORD: <service_password>
          SNOWFLAKE_ROLE: LTC_API_SERVICE_ROLE
          SNOWFLAKE_WAREHOUSE: COMPUTE_WH
          SNOWFLAKE_DATABASE: LTC_INSURANCE
          SNOWFLAKE_SCHEMA: ANALYTICS
          JWT_SECRET_KEY: <generate_with_openssl_rand_hex_32>
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
  MAX_INSTANCES = 3
  COMMENT = 'LTC Insurance FastAPI service';
*/

-- ============================================================================
-- Deployment Instructions
-- ============================================================================

SELECT 'SPCS infrastructure setup completed!' AS STATUS;

SELECT '
=============================================================================
NEXT STEPS FOR DEPLOYMENT:
=============================================================================

1. Build and tag Docker image locally:
   docker build -t ltc-fastapi:v1 .

2. Get registry URL (from SHOW IMAGE REPOSITORIES output above)

3. Authenticate to Snowflake Docker registry:
   docker login <org>-<account>.registry.snowflakecomputing.com -u <your_username>

4. Tag image for Snowflake registry:
   docker tag ltc-fastapi:v1 <registry_url>/ltc_api_repo/images/fastapi_repo/ltc-fastapi:v1

5. Push image to Snowflake:
   docker push <registry_url>/ltc_api_repo/images/fastapi_repo/ltc-fastapi:v1

6. Verify image in Snowflake:
   SHOW IMAGES IN IMAGE REPOSITORY LTC_API_REPO.IMAGES.FASTAPI_REPO;

7. Create the service (uncomment and run the CREATE SERVICE statement above)

8. Check service status:
   SHOW SERVICES;
   CALL SYSTEM$GET_SERVICE_STATUS(''LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE'');

9. Get API endpoint:
   SHOW ENDPOINTS IN SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE;

10. Test the API:
    curl https://<endpoint_url>/health

=============================================================================
' AS DEPLOYMENT_GUIDE;


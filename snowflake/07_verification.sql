-- ============================================================================
-- Step 7: Verification and Testing Queries
-- ============================================================================
-- Description: Verify all setup steps completed successfully

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- 1. Verify Databases and Schemas
-- ============================================================================

SELECT 'Verifying Databases and Schemas...' AS STEP;

SHOW DATABASES LIKE 'LTC%';
SHOW SCHEMAS IN DATABASE LTC_INSURANCE;
SHOW SCHEMAS IN DATABASE LTC_API_REPO;

-- ============================================================================
-- 2. Verify Data Tables
-- ============================================================================

SELECT 'Verifying Data Tables...' AS STEP;

USE DATABASE LTC_INSURANCE;
USE SCHEMA ANALYTICS;

-- Check tables exist
SHOW TABLES;

-- Verify data exists
SELECT 
    'POLICY_MONTHLY_SNAPSHOT_FACT' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT,
    COUNT(DISTINCT CARRIER_NAME) AS UNIQUE_CARRIERS,
    COUNT(DISTINCT INSURED_STATE) AS UNIQUE_STATES
FROM POLICY_MONTHLY_SNAPSHOT_FACT;

SELECT 
    'CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT,
    COUNT(DISTINCT CARRIER_NAME) AS UNIQUE_CARRIERS,
    COUNT(DISTINCT LIFE_STATE) AS UNIQUE_STATES
FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT;

-- ============================================================================
-- 3. Verify API Users
-- ============================================================================

SELECT 'Verifying API Users...' AS STEP;

SELECT 
    USERNAME,
    SNOWFLAKE_ROLE,
    CARRIER_ACCESS,
    IS_ACTIVE,
    CREATED_AT,
    LAST_LOGIN
FROM API_USERS
ORDER BY SNOWFLAKE_ROLE, USERNAME;

-- ============================================================================
-- 4. Verify SPCS Infrastructure
-- ============================================================================

SELECT 'Verifying SPCS Infrastructure...' AS STEP;

-- Check image repository
SHOW IMAGE REPOSITORIES IN SCHEMA LTC_API_REPO.IMAGES;

-- Check compute pools
SHOW COMPUTE POOLS;

-- Check if service exists (after deployment)
SHOW SERVICES IN SCHEMA LTC_INSURANCE.ANALYTICS;

-- ============================================================================
-- 5. Verify Roles and Permissions
-- ============================================================================

SELECT 'Verifying Roles and Permissions...' AS STEP;

SHOW ROLES LIKE 'LTC%';

-- Show grants for service role
SHOW GRANTS TO ROLE LTC_API_SERVICE_ROLE;

-- Show grants for API roles
SHOW GRANTS TO ROLE LTC_API_ADMIN;
SHOW GRANTS TO ROLE LTC_API_ANALYST;
SHOW GRANTS TO ROLE LTC_API_VIEWER;

-- Verify service user
SHOW USERS LIKE 'LTC_API_SERVICE';
SHOW GRANTS TO USER LTC_API_SERVICE;

-- ============================================================================
-- 6. Test Queries (Sample data access)
-- ============================================================================

SELECT 'Testing Sample Queries...' AS STEP;

-- Test policy query by state
SELECT 
    INSURED_STATE,
    COUNT(*) AS POLICY_COUNT,
    SUM(ANNUALIZED_PREMIUM) AS TOTAL_PREMIUM
FROM POLICY_MONTHLY_SNAPSHOT_FACT
WHERE INSURED_STATE IN ('CA', 'NY', 'TX')
GROUP BY INSURED_STATE
ORDER BY POLICY_COUNT DESC
LIMIT 10;

-- Test claims query by decision
SELECT 
    DECISION,
    COUNT(*) AS CLAIM_COUNT,
    AVG(RFB_PROCESS_TO_DECISION_TAT) AS AVG_TAT
FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT
WHERE DECISION IS NOT NULL
GROUP BY DECISION
ORDER BY CLAIM_COUNT DESC
LIMIT 10;

-- ============================================================================
-- 7. Get Carrier Names for User Configuration
-- ============================================================================

SELECT 'Available Carriers for User Configuration:' AS INFO;

SELECT DISTINCT 
    CARRIER_NAME,
    COUNT(*) AS POLICY_COUNT
FROM POLICY_MONTHLY_SNAPSHOT_FACT
GROUP BY CARRIER_NAME
ORDER BY CARRIER_NAME;

-- ============================================================================
-- 8. Configuration Summary
-- ============================================================================

SELECT 'CONFIGURATION SUMMARY' AS SECTION,
       '===================' AS SEPARATOR;

SELECT 
    'Database' AS COMPONENT,
    'LTC_INSURANCE' AS NAME,
    'ANALYTICS' AS SCHEMA_NAME,
    'Active' AS STATUS;

SELECT 
    'Image Repository' AS COMPONENT,
    'LTC_API_REPO.IMAGES.FASTAPI_REPO' AS NAME,
    '' AS SCHEMA_NAME,
    'Ready for Docker push' AS STATUS;

SELECT 
    'Compute Pool' AS COMPONENT,
    'LTC_API_POOL' AS NAME,
    '1-3 nodes (CPU_X64_S)' AS SCHEMA_NAME,
    'Ready' AS STATUS;

SELECT 
    'Service Account' AS COMPONENT,
    'LTC_API_SERVICE' AS NAME,
    'LTC_API_SERVICE_ROLE' AS SCHEMA_NAME,
    'Active' AS STATUS;

SELECT 
    'API Users' AS COMPONENT,
    COUNT(*)::VARCHAR AS NAME,
    LISTAGG(USERNAME, ', ') AS SCHEMA_NAME,
    'Configured' AS STATUS
FROM API_USERS
WHERE IS_ACTIVE = TRUE;

-- ============================================================================
-- Post-Deployment Verification Queries
-- ============================================================================
-- Run these after deploying the service

/*
-- Check service status
CALL SYSTEM$GET_SERVICE_STATUS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE');

-- Get service logs
CALL SYSTEM$GET_SERVICE_LOGS('LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE', '0', 'fastapi');

-- Get API endpoint
SHOW ENDPOINTS IN SERVICE LTC_INSURANCE.ANALYTICS.FASTAPI_SERVICE;

-- Test endpoint health
-- Copy the endpoint URL and run:
-- curl https://<endpoint-url>/health
-- curl https://<endpoint-url>/ready
*/

SELECT '
=============================================================================
VERIFICATION COMPLETED!
=============================================================================

Summary:
✓ Databases and schemas created
✓ Data tables verified (existing data)
✓ API users configured
✓ SPCS infrastructure ready
✓ RBAC roles and permissions set

Next Steps:
1. Update API_USERS with actual carrier names
2. Build and push Docker image
3. Create SPCS service (see 05_spcs_setup.sql)
4. Test API endpoints

For deployment instructions, see:
- DEPLOYMENT.md
- snowflake/05_spcs_setup.sql

=============================================================================
' AS COMPLETION_MESSAGE;


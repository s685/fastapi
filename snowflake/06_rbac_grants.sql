-- ============================================================================
-- Step 6: RBAC Grants and Permissions
-- ============================================================================
-- Description: Set up role-based access control for API users

USE ROLE ACCOUNTADMIN;
USE DATABASE LTC_INSURANCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- Create User Roles (matching API roles)
-- ============================================================================

-- Admin role - full access
CREATE ROLE IF NOT EXISTS LTC_API_ADMIN
    COMMENT = 'Admin role for LTC API - full data access';

-- Analyst role - multi-carrier access
CREATE ROLE IF NOT EXISTS LTC_API_ANALYST
    COMMENT = 'Analyst role for LTC API - multi-carrier access';

-- Viewer role - limited access
CREATE ROLE IF NOT EXISTS LTC_API_VIEWER
    COMMENT = 'Viewer role for LTC API - read-only access';

-- ============================================================================
-- Grant Database and Schema Access
-- ============================================================================

-- Admin role grants
GRANT USAGE ON DATABASE LTC_INSURANCE TO ROLE LTC_API_ADMIN;
GRANT USAGE ON SCHEMA LTC_INSURANCE.ANALYTICS TO ROLE LTC_API_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE LTC_API_ADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA LTC_INSURANCE.ANALYTICS TO ROLE LTC_API_ADMIN;
GRANT SELECT ON FUTURE TABLES IN SCHEMA LTC_INSURANCE.ANALYTICS TO ROLE LTC_API_ADMIN;

-- Analyst role grants
GRANT USAGE ON DATABASE LTC_INSURANCE TO ROLE LTC_API_ANALYST;
GRANT USAGE ON SCHEMA LTC_INSURANCE.ANALYTICS TO ROLE LTC_API_ANALYST;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE LTC_API_ANALYST;
GRANT SELECT ON TABLE LTC_INSURANCE.ANALYTICS.POLICY_MONTHLY_SNAPSHOT_FACT TO ROLE LTC_API_ANALYST;
GRANT SELECT ON TABLE LTC_INSURANCE.ANALYTICS.CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT TO ROLE LTC_API_ANALYST;

-- Viewer role grants
GRANT USAGE ON DATABASE LTC_INSURANCE TO ROLE LTC_API_VIEWER;
GRANT USAGE ON SCHEMA LTC_INSURANCE.ANALYTICS TO ROLE LTC_API_VIEWER;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE LTC_API_VIEWER;
GRANT SELECT ON TABLE LTC_INSURANCE.ANALYTICS.POLICY_MONTHLY_SNAPSHOT_FACT TO ROLE LTC_API_VIEWER;
GRANT SELECT ON TABLE LTC_INSURANCE.ANALYTICS.CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT TO ROLE LTC_API_VIEWER;

-- ============================================================================
-- Create Example Snowflake Users (Optional)
-- ============================================================================
-- These are example Snowflake users that correspond to API users
-- In production, these might be managed by your identity provider

/*
-- Example: Create Snowflake user for admin API user
CREATE USER IF NOT EXISTS ltc_admin_user
    PASSWORD = 'SecurePassword123!'
    DEFAULT_ROLE = LTC_API_ADMIN
    DEFAULT_WAREHOUSE = COMPUTE_WH;

GRANT ROLE LTC_API_ADMIN TO USER ltc_admin_user;

-- Example: Create Snowflake user for analyst API user
CREATE USER IF NOT EXISTS ltc_analyst_user
    PASSWORD = 'SecurePassword123!'
    DEFAULT_ROLE = LTC_API_ANALYST
    DEFAULT_WAREHOUSE = COMPUTE_WH;

GRANT ROLE LTC_API_ANALYST TO USER ltc_analyst_user;

-- Example: Create Snowflake user for viewer API user
CREATE USER IF NOT EXISTS ltc_viewer_user
    PASSWORD = 'SecurePassword123!'
    DEFAULT_ROLE = LTC_API_VIEWER
    DEFAULT_WAREHOUSE = COMPUTE_WH;

GRANT ROLE LTC_API_VIEWER TO USER ltc_viewer_user;
*/

-- ============================================================================
-- Row-Level Security (Optional - for additional security)
-- ============================================================================
-- If you need row-level security based on carrier, you can:
-- 1. Create mapping tables for user-to-carrier access
-- 2. Use secure views with session parameters (see 04_create_secure_views.sql)
-- 3. Implement in application layer (current approach)

-- Example mapping table:
/*
CREATE TABLE IF NOT EXISTS USER_CARRIER_ACCESS (
    USERNAME VARCHAR(100),
    CARRIER_NAME VARCHAR(150),
    ACCESS_LEVEL VARCHAR(20),  -- READ, WRITE
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Grant access to specific carriers
INSERT INTO USER_CARRIER_ACCESS (USERNAME, CARRIER_NAME, ACCESS_LEVEL)
VALUES
    ('analyst', 'Carrier_A', 'READ'),
    ('analyst', 'Carrier_B', 'READ'),
    ('viewer', 'Carrier_A', 'READ');
*/

-- ============================================================================
-- Verify Grants
-- ============================================================================

-- Show all roles
SHOW ROLES LIKE 'LTC_API%';

-- Show grants for each role
SHOW GRANTS TO ROLE LTC_API_ADMIN;
SHOW GRANTS TO ROLE LTC_API_ANALYST;
SHOW GRANTS TO ROLE LTC_API_VIEWER;

-- Verify service role
SHOW GRANTS TO ROLE LTC_API_SERVICE_ROLE;
SHOW GRANTS TO USER LTC_API_SERVICE;

SELECT 'RBAC grants configured successfully!' AS STATUS;

-- ============================================================================
-- Notes on RBAC Implementation
-- ============================================================================
/*
The API implements RBAC in the application layer:

1. User authenticates via /api/v1/auth/login
2. API validates credentials against API_USERS table
3. JWT token includes user role and carrier_access
4. Each API request:
   - Validates JWT token
   - Extracts user role and carrier access
   - Sets session parameters: USER_ROLE and USER_CARRIER
   - Snowflake RBAC can optionally filter data via secure views

This approach provides:
- Flexible access control at API layer
- Optional additional security via Snowflake secure views
- Audit trail of API access via structured logging
- Easy integration with external identity providers (Azure AD)
*/

SELECT 'RBAC setup completed - review notes above for implementation details' AS STATUS;


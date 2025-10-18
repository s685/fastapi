-- ============================================================================
-- Step 4: Create Secure Views (Optional - for RBAC)
-- ============================================================================
-- Description: Create secure views that filter data based on user role
-- Note: This is optional if you want database-level RBAC enforcement

USE DATABASE LTC_INSURANCE;
USE SCHEMA ANALYTICS;

-- ============================================================================
-- Secure View for Policy Data with RBAC
-- ============================================================================
-- This view filters data based on session parameters set by the API
-- The API sets USER_ROLE and USER_CARRIER session parameters

/*
-- Uncomment to use secure views for additional RBAC layer

CREATE OR REPLACE SECURE VIEW POLICY_MONTHLY_SNAPSHOT_SECURE AS
SELECT * FROM POLICY_MONTHLY_SNAPSHOT_FACT
WHERE 
    CASE CURRENT_SESSION_CONTEXT('USER_ROLE')
        WHEN 'ADMIN' THEN TRUE
        WHEN 'ANALYST' THEN (
            CURRENT_SESSION_CONTEXT('USER_CARRIER') = 'ALL' 
            OR CARRIER_NAME IN (
                SELECT VALUE FROM TABLE(
                    SPLIT_TO_TABLE(CURRENT_SESSION_CONTEXT('USER_CARRIER'), ',')
                )
            )
        )
        WHEN 'VIEWER' THEN (
            CURRENT_SESSION_CONTEXT('USER_CARRIER') = 'ALL'
            OR CARRIER_NAME = CURRENT_SESSION_CONTEXT('USER_CARRIER')
            OR CARRIER_NAME IN (
                SELECT VALUE FROM TABLE(
                    SPLIT_TO_TABLE(CURRENT_SESSION_CONTEXT('USER_CARRIER'), ',')
                )
            )
        )
        ELSE FALSE
    END;

-- ============================================================================
-- Secure View for Claims Data with RBAC
-- ============================================================================

CREATE OR REPLACE SECURE VIEW CLAIMS_TPA_FEE_WORKSHEET_SECURE AS
SELECT * FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT
WHERE 
    CASE CURRENT_SESSION_CONTEXT('USER_ROLE')
        WHEN 'ADMIN' THEN TRUE
        WHEN 'ANALYST' THEN (
            CURRENT_SESSION_CONTEXT('USER_CARRIER') = 'ALL'
            OR CARRIER_NAME IN (
                SELECT VALUE FROM TABLE(
                    SPLIT_TO_TABLE(CURRENT_SESSION_CONTEXT('USER_CARRIER'), ',')
                )
            )
        )
        WHEN 'VIEWER' THEN (
            CURRENT_SESSION_CONTEXT('USER_CARRIER') = 'ALL'
            OR CARRIER_NAME = CURRENT_SESSION_CONTEXT('USER_CARRIER')
            OR CARRIER_NAME IN (
                SELECT VALUE FROM TABLE(
                    SPLIT_TO_TABLE(CURRENT_SESSION_CONTEXT('USER_CARRIER'), ',')
                )
            )
        )
        ELSE FALSE
    END;
*/

-- ============================================================================
-- RBAC Implementation Notes
-- ============================================================================
-- If using secure views:
-- 1. Update query_builder.py to query from secure views instead of base tables
-- 2. API will set session parameters before each query:
--    ALTER SESSION SET USER_ROLE = 'ANALYST', USER_CARRIER = 'Carrier_A';
-- 3. Secure views will automatically filter data based on these parameters
--
-- Current implementation: RBAC is handled in application layer for simplicity
-- Secure views provide an additional layer of security if needed

SELECT 'Secure views script completed (views are optional)' AS STATUS;


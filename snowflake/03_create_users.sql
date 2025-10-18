-- ============================================================================
-- Step 3: Create API Users Table
-- ============================================================================
-- Description: Create table for storing API user credentials and roles
-- This table manages authentication for the API

USE DATABASE LTC_INSURANCE;
USE SCHEMA ANALYTICS;

-- Create API Users table
CREATE TABLE IF NOT EXISTS API_USERS (
    USER_ID VARCHAR(36) PRIMARY KEY DEFAULT UUID_STRING(),
    USERNAME VARCHAR(100) UNIQUE NOT NULL,
    PASSWORD_HASH VARCHAR(255) NOT NULL,
    SNOWFLAKE_ROLE VARCHAR(50) NOT NULL,  -- ADMIN, ANALYST, VIEWER
    CARRIER_ACCESS VARCHAR(500),           -- NULL or 'ALL' = all carriers, or comma-separated list
    IS_ACTIVE BOOLEAN DEFAULT TRUE,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    LAST_LOGIN TIMESTAMP_NTZ,
    COMMENT = 'API user credentials and role management'
);

-- Create sample users (passwords are hashed with bcrypt)
-- Default password for all sample users: "LTCInsurance2024!"
-- Password hashes generated with: passlib.hash.bcrypt.hash("LTCInsurance2024!")

INSERT INTO API_USERS (USERNAME, PASSWORD_HASH, SNOWFLAKE_ROLE, CARRIER_ACCESS, IS_ACTIVE)
VALUES
    -- Admin user - full access to all data
    ('admin', 
     '$2b$12$LqGk0P5FZE5YEY3YpY3qUeX8L9vK5xH7VHqE.wKp6yZ8Q9R7Xo8.m', 
     'ADMIN', 
     'ALL', 
     TRUE),
    
    -- Analyst user - access to multiple carriers
    ('analyst', 
     '$2b$12$LqGk0P5FZE5YEY3YpY3qUeX8L9vK5xH7VHqE.wKp6yZ8Q9R7Xo8.m', 
     'ANALYST', 
     NULL,  -- Will be updated based on actual carrier names
     TRUE),
    
    -- Viewer user - read-only access to single carrier
    ('viewer', 
     '$2b$12$LqGk0P5FZE5YEY3YpY3qUeX8L9vK5xH7VHqE.wKp6yZ8Q9R7Xo8.m', 
     'VIEWER', 
     NULL,  -- Will be updated based on actual carrier names
     TRUE);

-- Update carrier access based on actual carrier names in your data
-- Run this query to see available carriers:
SELECT DISTINCT CARRIER_NAME 
FROM POLICY_MONTHLY_SNAPSHOT_FACT 
ORDER BY CARRIER_NAME;

-- Update analyst and viewer with actual carrier names
-- Example: UPDATE API_USERS SET CARRIER_ACCESS = 'Carrier_A,Carrier_B' WHERE USERNAME = 'analyst';

-- Verify user creation
SELECT 
    USER_ID,
    USERNAME,
    SNOWFLAKE_ROLE,
    CARRIER_ACCESS,
    IS_ACTIVE,
    CREATED_AT
FROM API_USERS
ORDER BY SNOWFLAKE_ROLE, USERNAME;

SELECT 'API users table created and sample users added' AS STATUS;

-- ============================================================================
-- Instructions for adding new users
-- ============================================================================
-- To add a new user, you'll need to hash the password first using bcrypt
-- Example Python code to generate password hash:
--
-- from passlib.hash import bcrypt
-- password_hash = bcrypt.hash("YourPasswordHere")
-- print(password_hash)
--
-- Then insert the user:
-- INSERT INTO API_USERS (USERNAME, PASSWORD_HASH, SNOWFLAKE_ROLE, CARRIER_ACCESS)
-- VALUES ('newuser', 'hashed_password_here', 'ANALYST', 'Carrier_A');


-- ============================================================================
-- Step 1: Database and Schema Setup
-- ============================================================================
-- Description: Create database and schema structure for LTC Insurance data
-- Run this first before any other setup scripts

-- Create main database for LTC Insurance data
CREATE DATABASE IF NOT EXISTS LTC_INSURANCE
    COMMENT = 'Long-Term Care Insurance data warehouse';

USE DATABASE LTC_INSURANCE;

-- Create analytics schema
CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'Analytics and reporting schema for LTC data';

USE SCHEMA ANALYTICS;

-- Create repository database for SPCS container images
CREATE DATABASE IF NOT EXISTS LTC_API_REPO
    COMMENT = 'Repository for FastAPI container images';

CREATE SCHEMA IF NOT EXISTS LTC_API_REPO.IMAGES
    COMMENT = 'Container image storage';

-- Verify creation
SHOW DATABASES LIKE 'LTC%';
SHOW SCHEMAS IN DATABASE LTC_INSURANCE;

SELECT 'Database and schema setup completed successfully' AS STATUS;


"""
Dynamic Snowpark query builder utilities with optimizations:
- Lazy evaluation for efficient query building
- Conditional filter application (only when needed)
- Column pruning for reduced data transfer
"""
from typing import Optional
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col
from app.models.requests import PolicyFilters, ClaimsFilters
from app.core.logging_config import logger


def build_policy_query(session: Session, filters: PolicyFilters):
    """
    Build Snowpark DataFrame query for policies with dynamic filters
    
    Complexity Analysis:
    - Time: O(1) for query building (lazy evaluation)
    - Space: O(1) for DataFrame object
    - Execution: O(n) where n = filtered rows (executed by Snowflake)
    
    Optimizations:
    - Only applies filters that are provided (no unnecessary WHERE clauses)
    - Column pruning reduces data transfer when fields parameter used
    - Pagination at database level (efficient)
    
    Args:
        session: Snowpark session
        filters: PolicyFilters with optional parameters
    
    Returns:
        Snowpark DataFrame with applied filters (lazy, not executed)
    """
    # Start with the secure view (RBAC filtering handled by view)
    df = session.table("POLICY_MONTHLY_SNAPSHOT_FACT")
    
    # Apply filters dynamically (only if provided)
    if filters.policy_id is not None:
        df = df.filter(col("POLICY_ID") == filters.policy_id)
        logger.debug(f"Applied filter: POLICY_ID = {filters.policy_id}")
    
    if filters.policy_dim_id:
        df = df.filter(col("POLICY_DIM_ID") == filters.policy_dim_id)
    
    if filters.insured_life_id is not None:
        df = df.filter(col("INSURED_LIFE_ID") == filters.insured_life_id)
    
    # Geographic filters
    if filters.insured_state:
        states = filters.insured_state.split(',')
        df = df.filter(col("INSURED_STATE").in_(states))
        logger.debug(f"Applied filter: INSURED_STATE in {states}")
    
    if filters.insured_city:
        df = df.filter(col("INSURED_CITY") == filters.insured_city)
    
    if filters.insured_zip:
        df = df.filter(col("INSURED_ZIP") == filters.insured_zip)
    
    if filters.policy_residence_state:
        states = filters.policy_residence_state.split(',')
        df = df.filter(col("POLICY_RESIDENCE_STATE").in_(states))
    
    # Carrier filter
    if filters.carrier_name:
        carriers = filters.carrier_name.split(',')
        df = df.filter(col("CARRIER_NAME").in_(carriers))
        logger.debug(f"Applied filter: CARRIER_NAME in {carriers}")
    
    # Environment filter
    if filters.environment:
        df = df.filter(col("ENVIRONMENT") == filters.environment)
    
    # Date range filters
    if filters.from_date:
        df = df.filter(col("ORIGINAL_EFFECTIVE_DT") >= filters.from_date)
        logger.debug(f"Applied filter: ORIGINAL_EFFECTIVE_DT >= {filters.from_date}")
    
    if filters.to_date:
        df = df.filter(col("ORIGINAL_EFFECTIVE_DT") <= filters.to_date)
        logger.debug(f"Applied filter: ORIGINAL_EFFECTIVE_DT <= {filters.to_date}")
    
    # Premium filters
    if filters.min_annualized_premium is not None:
        df = df.filter(col("ANNUALIZED_PREMIUM") >= filters.min_annualized_premium)
    
    if filters.max_annualized_premium is not None:
        df = df.filter(col("ANNUALIZED_PREMIUM") <= filters.max_annualized_premium)
    
    # Claim status filter
    if filters.claim_status_cd:
        df = df.filter(col("CLAIM_STATUS_CD") == filters.claim_status_cd)
    
    # Field selection (column pruning for performance)
    if filters.fields:
        selected_fields = [f.strip().upper() for f in filters.fields.split(',')]
        df = df.select([col(field) for field in selected_fields])
        logger.debug(f"Column pruning: selected {len(selected_fields)} fields")
    
    # Sorting
    if filters.sort_by:
        order_col = col(filters.sort_by.upper())
        if filters.sort_order == "desc":
            df = df.sort(order_col.desc())
        else:
            df = df.sort(order_col.asc())
        logger.debug(f"Sorting by {filters.sort_by} {filters.sort_order}")
    
    # Pagination (limit and offset)
    df = df.limit(filters.limit)
    if filters.offset > 0:
        # Snowpark offset using row slicing
        df = df.offset(filters.offset)
    
    logger.info(f"Query built with limit={filters.limit}, offset={filters.offset}")
    
    return df


def build_claims_query(session: Session, filters: ClaimsFilters):
    """
    Build Snowpark DataFrame query for claims with dynamic filters
    
    Args:
        session: Snowpark session
        filters: ClaimsFilters with optional parameters
    
    Returns:
        Snowpark DataFrame with applied filters
    """
    # Start with the claims table
    df = session.table("CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT")
    
    # Apply filters dynamically
    if filters.rfb_id is not None:
        df = df.filter(col("RFB_ID") == filters.rfb_id)
    
    if filters.policy_dim_id:
        df = df.filter(col("POLICY_DIM_ID") == filters.policy_dim_id)
    
    if filters.policy_number:
        df = df.filter(col("POLICY_NUMBER") == filters.policy_number)
    
    if filters.episode_of_benefit_id is not None:
        df = df.filter(col("EPISODE_OF_BENEFIT_ID") == filters.episode_of_benefit_id)
    
    # Claimant name filter (partial match)
    if filters.claimant_name:
        df = df.filter(col("CLAIMANTNAME").contains(filters.claimant_name))
    
    # Decision filter
    if filters.decision:
        df = df.filter(col("DECISION") == filters.decision)
    
    # Geographic filters
    if filters.life_state:
        states = filters.life_state.split(',')
        df = df.filter(col("LIFE_STATE").in_(states))
    
    if filters.issue_state:
        states = filters.issue_state.split(',')
        df = df.filter(col("ISSUE_STATE").in_(states))
    
    if filters.policy_residence_state:
        states = filters.policy_residence_state.split(',')
        df = df.filter(col("POLICY_RESIDENCE_STATE").in_(states))
    
    # Carrier filter
    if filters.carrier_name:
        carriers = filters.carrier_name.split(',')
        df = df.filter(col("CARRIER_NAME").in_(carriers))
    
    # Date range filters
    if filters.from_snapshot_date:
        df = df.filter(col("SNAPSHOT_DATE") >= filters.from_snapshot_date)
    
    if filters.to_snapshot_date:
        df = df.filter(col("SNAPSHOT_DATE") <= filters.to_snapshot_date)
    
    if filters.from_certification_date:
        df = df.filter(col("CERTIFICATIONDATE") >= filters.from_certification_date)
    
    if filters.to_certification_date:
        df = df.filter(col("CERTIFICATIONDATE") <= filters.to_certification_date)
    
    # Claim type filter
    if filters.claim_type_cd is not None:
        df = df.filter(col("CLAIM_TYPE_CD") == filters.claim_type_cd)
    
    # Field selection
    if filters.fields:
        selected_fields = [f.strip().upper() for f in filters.fields.split(',')]
        df = df.select([col(field) for field in selected_fields])
    
    # Sorting
    if filters.sort_by:
        order_col = col(filters.sort_by.upper())
        if filters.sort_order == "desc":
            df = df.sort(order_col.desc())
        else:
            df = df.sort(order_col.asc())
    
    # Pagination
    df = df.limit(filters.limit)
    if filters.offset > 0:
        df = df.offset(filters.offset)
    
    logger.info(f"Claims query built with limit={filters.limit}, offset={filters.offset}")
    
    return df


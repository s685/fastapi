"""Policy endpoints"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from snowflake.snowpark import Session
from app.models.requests import PolicyFilters
from app.models.responses import PolicySummaryResponse
from app.services.policy_service import PolicyService
from app.core.security import get_current_user, get_user_context_for_session
from app.core.snowflake import session_manager
from app.core.logging_config import logger


router = APIRouter(prefix="/policies", tags=["Policies"])


async def get_policy_session(current_user: Dict[str, str] = Depends(get_current_user)) -> Session:
    """Get Snowpark session with user context for RBAC"""
    user_context = get_user_context_for_session(current_user)
    return await session_manager.get_session(user_context)


@router.get("", response_model=List[Dict[str, Any]])
async def get_policies(
    # ID filters
    policy_id: int = Query(None, description="Filter by specific policy ID"),
    policy_dim_id: str = Query(None, description="Filter by policy dimension ID"),
    insured_life_id: int = Query(None, description="Filter by insured life ID"),
    
    # Geographic filters
    insured_state: str = Query(None, description="Filter by insured state (comma-separated for multiple)"),
    insured_city: str = Query(None, description="Filter by insured city"),
    insured_zip: str = Query(None, description="Filter by insured ZIP code"),
    policy_residence_state: str = Query(None, description="Filter by policy residence state"),
    
    # Carrier and status
    carrier_name: str = Query(None, description="Filter by carrier name (comma-separated)"),
    environment: str = Query(None, description="Filter by environment"),
    
    # Date filters
    from_date: str = Query(None, description="Start date for original effective date (YYYY-MM-DD)"),
    to_date: str = Query(None, description="End date for original effective date (YYYY-MM-DD)"),
    
    # Premium filters
    min_annualized_premium: float = Query(None, description="Minimum annualized premium"),
    max_annualized_premium: float = Query(None, description="Maximum annualized premium"),
    
    # Claim filters
    claim_status_cd: str = Query(None, description="Filter by claim status code"),
    
    # Pagination
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    
    # Sorting
    sort_by: str = Query("POLICY_ID", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    
    # Field selection
    fields: str = Query(None, description="Comma-separated fields to return"),
    
    # Dependencies
    current_user: Dict[str, str] = Depends(get_current_user),
    session: Session = Depends(get_policy_session)
):
    """
    Get policies with optional filters
    
    All query parameters are optional. Returns paginated results.
    RBAC filtering is applied automatically based on user role.
    
    Example:
        GET /api/v1/policies?policy_id=12345
        GET /api/v1/policies?insured_state=CA,NY&limit=50
        GET /api/v1/policies?carrier_name=Carrier_A&fields=policy_id,carrier_name,annualized_premium
    """
    try:
        # Build filters from query parameters
        filters = PolicyFilters(
            policy_id=policy_id,
            policy_dim_id=policy_dim_id,
            insured_life_id=insured_life_id,
            insured_state=insured_state,
            insured_city=insured_city,
            insured_zip=insured_zip,
            policy_residence_state=policy_residence_state,
            carrier_name=carrier_name,
            environment=environment,
            from_date=from_date,
            to_date=to_date,
            min_annualized_premium=min_annualized_premium,
            max_annualized_premium=max_annualized_premium,
            claim_status_cd=claim_status_cd,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            fields=fields
        )
        
        logger.info(f"User {current_user['username']} requesting policies with filters")
        
        # Get policies using service
        policy_service = PolicyService(session)
        policies = policy_service.get_policies(filters)
        
        return policies
    
    except Exception as e:
        logger.error(f"Error fetching policies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching policies: {str(e)}"
        )


@router.get("/{policy_id}", response_model=Dict[str, Any])
async def get_policy_by_id(
    policy_id: int,
    current_user: Dict[str, str] = Depends(get_current_user),
    session: Session = Depends(get_policy_session)
):
    """
    Get a single policy by ID
    
    Args:
        policy_id: Policy ID
    
    Returns:
        Policy details
    """
    try:
        logger.info(f"User {current_user['username']} requesting policy {policy_id}")
        
        policy_service = PolicyService(session)
        policy = policy_service.get_policy_by_id(policy_id)
        
        return policy
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching policy {policy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching policy: {str(e)}"
        )


@router.get("/analytics/summary", response_model=PolicySummaryResponse)
async def get_policy_summary(
    current_user: Dict[str, str] = Depends(get_current_user),
    session: Session = Depends(get_policy_session)
):
    """
    Get aggregated policy statistics
    
    Returns summary statistics including:
    - Total policies
    - Total and average premiums
    - Breakdown by state
    - Breakdown by carrier
    """
    try:
        logger.info(f"User {current_user['username']} requesting policy summary")
        
        policy_service = PolicyService(session)
        summary = policy_service.get_policy_summary()
        
        return PolicySummaryResponse(**summary)
    
    except Exception as e:
        logger.error(f"Error fetching policy summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching summary: {str(e)}"
        )


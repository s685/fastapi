"""Claims endpoints"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from snowflake.snowpark import Session
from app.models.requests import ClaimsFilters
from app.models.responses import ClaimAnalyticsResponse
from app.services.claims_service import ClaimsService
from app.core.security import get_current_user, get_user_context_for_session
from app.core.snowflake import session_manager
from app.core.logging_config import logger


router = APIRouter(prefix="/claims", tags=["Claims"])


async def get_claims_session(current_user: Dict[str, str] = Depends(get_current_user)) -> Session:
    """Get Snowpark session with user context for RBAC"""
    user_context = get_user_context_for_session(current_user)
    return await session_manager.get_session(user_context)


@router.get("", response_model=List[Dict[str, Any]])
async def get_claims(
    # ID filters
    rfb_id: int = Query(None, description="Filter by RFB ID"),
    policy_dim_id: str = Query(None, description="Filter by policy dimension ID"),
    policy_number: str = Query(None, description="Filter by policy number"),
    episode_of_benefit_id: int = Query(None, description="Filter by episode of benefit ID"),
    
    # Claimant filters
    claimant_name: str = Query(None, description="Filter by claimant name (partial match)"),
    decision: str = Query(None, description="Filter by decision type"),
    
    # Geographic filters
    life_state: str = Query(None, description="Filter by life state (comma-separated)"),
    issue_state: str = Query(None, description="Filter by issue state (comma-separated)"),
    policy_residence_state: str = Query(None, description="Filter by policy residence state"),
    
    # Carrier
    carrier_name: str = Query(None, description="Filter by carrier name"),
    
    # Date filters
    from_snapshot_date: str = Query(None, description="Start date for snapshot (YYYY-MM-DD)"),
    to_snapshot_date: str = Query(None, description="End date for snapshot (YYYY-MM-DD)"),
    from_certification_date: str = Query(None, description="Start date for certification"),
    to_certification_date: str = Query(None, description="End date for certification"),
    
    # Claim type
    claim_type_cd: int = Query(None, description="Filter by claim type code"),
    
    # Pagination
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    
    # Sorting
    sort_by: str = Query("RFB_ID", description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    
    # Field selection
    fields: str = Query(None, description="Comma-separated fields to return"),
    
    # Dependencies
    current_user: Dict[str, str] = Depends(get_current_user),
    session: Session = Depends(get_claims_session)
):
    """
    Get claims with optional filters
    
    All query parameters are optional. Returns paginated results.
    
    Example:
        GET /api/v1/claims?rfb_id=12345
        GET /api/v1/claims?life_state=CA&limit=50
    """
    try:
        # Build filters
        filters = ClaimsFilters(
            rfb_id=rfb_id,
            policy_dim_id=policy_dim_id,
            policy_number=policy_number,
            episode_of_benefit_id=episode_of_benefit_id,
            claimant_name=claimant_name,
            decision=decision,
            life_state=life_state,
            issue_state=issue_state,
            policy_residence_state=policy_residence_state,
            carrier_name=carrier_name,
            from_snapshot_date=from_snapshot_date,
            to_snapshot_date=to_snapshot_date,
            from_certification_date=from_certification_date,
            to_certification_date=to_certification_date,
            claim_type_cd=claim_type_cd,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            fields=fields
        )
        
        logger.info(f"User {current_user['username']} requesting claims with filters")
        
        # Get claims using service
        claims_service = ClaimsService(session)
        claims = claims_service.get_claims(filters)
        
        return claims
    
    except Exception as e:
        logger.error(f"Error fetching claims: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching claims: {str(e)}"
        )


@router.get("/{rfb_id}", response_model=Dict[str, Any])
async def get_claim_by_id(
    rfb_id: int,
    current_user: Dict[str, str] = Depends(get_current_user),
    session: Session = Depends(get_claims_session)
):
    """
    Get a single claim by RFB ID
    
    Args:
        rfb_id: RFB ID
    
    Returns:
        Claim details
    """
    try:
        logger.info(f"User {current_user['username']} requesting claim {rfb_id}")
        
        claims_service = ClaimsService(session)
        claim = claims_service.get_claim_by_id(rfb_id)
        
        return claim
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching claim {rfb_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching claim: {str(e)}"
        )


@router.get("/analytics/summary", response_model=ClaimAnalyticsResponse)
async def get_claims_analytics(
    current_user: Dict[str, str] = Depends(get_current_user),
    session: Session = Depends(get_claims_session)
):
    """
    Get aggregated claims analytics
    
    Returns analytics including:
    - Total claims
    - Average TAT
    - Breakdown by decision type
    - Breakdown by state
    - Breakdown by carrier
    """
    try:
        logger.info(f"User {current_user['username']} requesting claims analytics")
        
        claims_service = ClaimsService(session)
        analytics = claims_service.get_claims_analytics()
        
        return ClaimAnalyticsResponse(**analytics)
    
    except Exception as e:
        logger.error(f"Error fetching claims analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analytics: {str(e)}"
        )


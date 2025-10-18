"""Request models with optional filters"""
from typing import Optional, Literal
from datetime import date
from pydantic import BaseModel, Field


class PolicyFilters(BaseModel):
    """
    Policy query filters - all parameters are optional
    Supports filtering, pagination, sorting, and field selection
    """
    # Filtering by IDs
    policy_id: Optional[int] = Field(None, description="Specific policy ID")
    policy_dim_id: Optional[str] = Field(None, description="Policy dimension ID")
    insured_life_id: Optional[int] = Field(None, description="Insured life ID")
    
    # Geographic filters
    insured_state: Optional[str] = Field(None, description="Insured state (comma-separated for multiple: 'CA,NY,TX')")
    insured_city: Optional[str] = Field(None, description="Insured city")
    insured_zip: Optional[str] = Field(None, description="Insured ZIP code")
    policy_residence_state: Optional[str] = Field(None, description="Policy residence state")
    
    # Carrier and status filters
    carrier_name: Optional[str] = Field(None, description="Carrier name (comma-separated for multiple)")
    environment: Optional[str] = Field(None, description="Environment filter")
    
    # Date range filters
    from_date: Optional[date] = Field(None, description="Start date for original effective date filter")
    to_date: Optional[date] = Field(None, description="End date for original effective date filter")
    
    # Premium filters
    min_annualized_premium: Optional[float] = Field(None, description="Minimum annualized premium")
    max_annualized_premium: Optional[float] = Field(None, description="Maximum annualized premium")
    
    # Claim-related filters
    claim_status_cd: Optional[str] = Field(None, description="Claim status code")
    
    # Pagination
    limit: int = Field(default=100, le=1000, ge=1, description="Maximum number of records to return")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    
    # Sorting
    sort_by: Optional[str] = Field(default="POLICY_ID", description="Field to sort by")
    sort_order: Literal["asc", "desc"] = Field(default="asc", description="Sort order")
    
    # Field selection (column pruning)
    fields: Optional[str] = Field(
        None, 
        description="Comma-separated list of fields to return (e.g., 'policy_id,carrier_name,annualized_premium')"
    )


class ClaimsFilters(BaseModel):
    """
    Claims query filters - all parameters are optional
    Supports filtering, pagination, sorting, and field selection
    """
    # Filtering by IDs
    rfb_id: Optional[int] = Field(None, description="RFB ID")
    policy_dim_id: Optional[str] = Field(None, description="Policy dimension ID")
    policy_number: Optional[str] = Field(None, description="Policy number")
    episode_of_benefit_id: Optional[int] = Field(None, description="Episode of benefit ID")
    
    # Claimant filters
    claimant_name: Optional[str] = Field(None, description="Claimant name (partial match supported)")
    
    # Decision filters
    decision: Optional[str] = Field(None, description="Decision type")
    
    # Geographic filters
    life_state: Optional[str] = Field(None, description="Life state (comma-separated)")
    issue_state: Optional[str] = Field(None, description="Issue state (comma-separated)")
    policy_residence_state: Optional[str] = Field(None, description="Policy residence state (comma-separated)")
    
    # Carrier filter
    carrier_name: Optional[str] = Field(None, description="Carrier name (comma-separated)")
    
    # Date range filters
    from_snapshot_date: Optional[date] = Field(None, description="Start date for snapshot date")
    to_snapshot_date: Optional[date] = Field(None, description="End date for snapshot date")
    from_certification_date: Optional[date] = Field(None, description="Start date for certification")
    to_certification_date: Optional[date] = Field(None, description="End date for certification")
    
    # Claim type
    claim_type_cd: Optional[int] = Field(None, description="Claim type code")
    
    # Pagination
    limit: int = Field(default=100, le=1000, ge=1, description="Maximum number of records to return")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    
    # Sorting
    sort_by: Optional[str] = Field(default="RFB_ID", description="Field to sort by")
    sort_order: Literal["asc", "desc"] = Field(default="asc", description="Sort order")
    
    # Field selection (column pruning)
    fields: Optional[str] = Field(
        None,
        description="Comma-separated list of fields to return"
    )


"""Response models"""
from typing import Optional, List, Any, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field


class PolicyResponse(BaseModel):
    """Policy response model - flexible to accommodate field selection"""
    # Core fields that are always present if not using field selection
    POLICY_ID: Optional[int] = None
    POLICY_DIM_ID: Optional[str] = None
    INSURED_LIFE_ID: Optional[int] = None
    INSURED_CITY: Optional[str] = None
    INSURED_STATE: Optional[str] = None
    INSURED_ZIP: Optional[str] = None
    POLICY_RESIDENCE_STATE: Optional[str] = None
    ANNUALIZED_PREMIUM: Optional[float] = None
    LIFETIME_COLLECTED_PREMIUM: Optional[float] = None
    CARRIER_NAME: Optional[str] = None
    ENVIRONMENT: Optional[str] = None
    ORIGINAL_EFFECTIVE_DT: Optional[datetime] = None
    POLICY_SNAPSHOT_DATE: Optional[str] = None
    
    class Config:
        # Allow extra fields for dynamic field selection
        extra = "allow"
        from_attributes = True


class ClaimResponse(BaseModel):
    """Claim response model - flexible to accommodate field selection"""
    RFB_ID: Optional[int] = None
    POLICY_DIM_ID: Optional[str] = None
    CLAIMANTNAME: Optional[str] = None
    POLICY_NUMBER: Optional[str] = None
    DECISION: Optional[str] = None
    CARRIER_NAME: Optional[str] = None
    SNAPSHOT_DATE: Optional[date] = None
    LIFE_STATE: Optional[str] = None
    ISSUE_STATE: Optional[str] = None
    POLICY_RESIDENCE_STATE: Optional[str] = None
    CLAIM_TYPE_CD: Optional[int] = None
    
    class Config:
        # Allow extra fields for dynamic field selection
        extra = "allow"
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    total: int = Field(..., description="Total number of records (if available)")
    limit: int = Field(..., description="Records per page")
    offset: int = Field(..., description="Starting offset")
    data: List[Dict[str, Any]] = Field(..., description="Response data")


class PolicySummaryResponse(BaseModel):
    """Aggregated policy statistics"""
    total_policies: int
    total_annualized_premium: float
    total_lifetime_premium: float
    avg_annualized_premium: float
    policies_by_state: Dict[str, int]
    policies_by_carrier: Dict[str, int]


class ClaimAnalyticsResponse(BaseModel):
    """Claims analytics response"""
    total_claims: int
    avg_tat: Optional[float] = None
    decisions_breakdown: Dict[str, int]
    claims_by_state: Dict[str, int]
    claims_by_carrier: Dict[str, int]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    status: str = Field(..., description="Service readiness status")
    snowflake: str = Field(..., description="Snowflake connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


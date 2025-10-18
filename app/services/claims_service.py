"""
Claims business logic service with optimizations:
- Efficient datetime serialization
- Memory-efficient processing
- Reusable serialization methods
"""
from typing import List, Dict, Any
from datetime import datetime, date
from snowflake.snowpark import Session
from app.models.requests import ClaimsFilters
from app.utils.query_builder import build_claims_query
from app.core.logging_config import logger


class ClaimsService:
    """Service for claims-related business logic with performance optimizations"""
    
    __slots__ = ('session',)  # Memory optimization
    
    def __init__(self, session: Session):
        self.session = session
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Fast value serialization - Time: O(1), Space: O(1)"""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value
    
    @staticmethod
    def _serialize_row(row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Efficient row serialization - Time: O(k), Space: O(k)"""
        return {key: ClaimsService._serialize_value(val) for key, val in row_dict.items()}
    
    def get_claims(self, filters: ClaimsFilters) -> List[Dict[str, Any]]:
        """
        Get claims with optional filters
        
        Args:
            filters: ClaimsFilters with optional parameters
        
        Returns:
            List of claim dictionaries
        """
        try:
            logger.info(f"Fetching claims with filters: rfb_id={filters.rfb_id}, limit={filters.limit}")
            
            # Build query using Snowpark DataFrame
            df = build_claims_query(self.session, filters)
            
            # Execute query
            results = df.collect()
            
            logger.info(f"Retrieved {len(results)} claims")
            
            # Optimized serialization - Time: O(n*k), Space: O(n*k)
            return [self._serialize_row(row.as_dict()) for row in results]
        
        except Exception as e:
            logger.error(f"Error fetching claims: {str(e)}")
            raise
    
    def get_claim_by_id(self, rfb_id: int) -> Dict[str, Any]:
        """
        Get a single claim by RFB ID
        
        Args:
            rfb_id: RFB ID
        
        Returns:
            Claim dictionary
        
        Raises:
            ValueError: If claim not found
        """
        try:
            logger.info(f"Fetching claim by RFB_ID: {rfb_id}")
            
            result = self.session.sql(f"""
                SELECT *
                FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT
                WHERE RFB_ID = {rfb_id}
                LIMIT 1
            """).collect()
            
            if not result:
                raise ValueError(f"Claim with RFB_ID {rfb_id} not found")
            
            # Optimized serialization
            return self._serialize_row(result[0].as_dict())
        
        except Exception as e:
            logger.error(f"Error fetching claim {rfb_id}: {str(e)}")
            raise
    
    def get_claims_analytics(self) -> Dict[str, Any]:
        """
        Get aggregated claims analytics
        
        Returns:
            Analytics dictionary
        """
        try:
            logger.info("Fetching claims analytics")
            
            # Total claims and average TAT
            summary_query = """
                SELECT 
                    COUNT(*) as TOTAL_CLAIMS,
                    AVG(RFB_PROCESS_TO_DECISION_TAT) as AVG_TAT
                FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT
            """
            
            summary_result = self.session.sql(summary_query).collect()[0].as_dict()
            
            # Decision breakdown
            decision_query = """
                SELECT 
                    DECISION,
                    COUNT(*) as COUNT
                FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT
                WHERE DECISION IS NOT NULL
                GROUP BY DECISION
                ORDER BY COUNT DESC
            """
            
            decision_results = self.session.sql(decision_query).collect()
            decisions_breakdown = {row["DECISION"]: row["COUNT"] for row in decision_results}
            
            # Claims by state
            state_query = """
                SELECT 
                    LIFE_STATE,
                    COUNT(*) as COUNT
                FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT
                WHERE LIFE_STATE IS NOT NULL
                GROUP BY LIFE_STATE
                ORDER BY COUNT DESC
                LIMIT 20
            """
            
            state_results = self.session.sql(state_query).collect()
            claims_by_state = {row["LIFE_STATE"]: row["COUNT"] for row in state_results}
            
            # Claims by carrier
            carrier_query = """
                SELECT 
                    CARRIER_NAME,
                    COUNT(*) as COUNT
                FROM CLAIMS_TPA_FEE_WORKSHEET_SNAPSHOT_FACT
                WHERE CARRIER_NAME IS NOT NULL
                GROUP BY CARRIER_NAME
                ORDER BY COUNT DESC
            """
            
            carrier_results = self.session.sql(carrier_query).collect()
            claims_by_carrier = {row["CARRIER_NAME"]: row["COUNT"] for row in carrier_results}
            
            return {
                "total_claims": summary_result["TOTAL_CLAIMS"],
                "avg_tat": float(summary_result["AVG_TAT"] or 0),
                "decisions_breakdown": decisions_breakdown,
                "claims_by_state": claims_by_state,
                "claims_by_carrier": claims_by_carrier
            }
        
        except Exception as e:
            logger.error(f"Error fetching claims analytics: {str(e)}")
            raise


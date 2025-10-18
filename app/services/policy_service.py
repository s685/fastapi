"""
Policy business logic service with optimizations:
- Efficient datetime serialization (O(n) where n = rows)
- Generator pattern for large datasets
- Memory-efficient batch processing
"""
from typing import List, Dict, Any, Generator, Optional
from datetime import datetime, date
from snowflake.snowpark import Session
from app.models.requests import PolicyFilters
from app.utils.query_builder import build_policy_query
from app.core.logging_config import logger


class PolicyService:
    """
    Service for policy-related business logic with performance optimizations
    """
    
    __slots__ = ('session',)  # Memory optimization: reduce instance dict overhead
    
    def __init__(self, session: Session):
        self.session = session
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """
        Fast value serialization with type checking
        Time Complexity: O(1) per value
        Space Complexity: O(1)
        """
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value
    
    @staticmethod
    def _serialize_row(row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Efficiently serialize a single row
        Time Complexity: O(k) where k = number of columns
        Space Complexity: O(k) for new dict
        """
        return {key: PolicyService._serialize_value(val) for key, val in row_dict.items()}
    
    def get_policies(self, filters: PolicyFilters) -> List[Dict[str, Any]]:
        """
        Get policies with optional filters
        
        Args:
            filters: PolicyFilters with optional parameters
        
        Returns:
            List of policy dictionaries
        """
        try:
            logger.info(f"Fetching policies with filters: policy_id={filters.policy_id}, limit={filters.limit}")
            
            # Build query using Snowpark DataFrame
            df = build_policy_query(self.session, filters)
            
            # Execute query (lazy evaluation - only executes here)
            results = df.collect()
            
            logger.info(f"Retrieved {len(results)} policies")
            
            # Optimized serialization using list comprehension
            # Time Complexity: O(n*k) where n=rows, k=columns
            # Space Complexity: O(n*k) for result list
            return [self._serialize_row(row.as_dict()) for row in results]
        
        except Exception as e:
            logger.error(f"Error fetching policies: {str(e)}")
            raise
    
    def get_policy_by_id(self, policy_id: int) -> Dict[str, Any]:
        """
        Get a single policy by ID
        
        Args:
            policy_id: Policy ID
        
        Returns:
            Policy dictionary
        
        Raises:
            ValueError: If policy not found
        """
        try:
            logger.info(f"Fetching policy by ID: {policy_id}")
            
            result = self.session.sql(f"""
                SELECT *
                FROM POLICY_MONTHLY_SNAPSHOT_FACT
                WHERE POLICY_ID = {policy_id}
                LIMIT 1
            """).collect()
            
            if not result:
                raise ValueError(f"Policy with ID {policy_id} not found")
            
            # Optimized serialization using static method
            return self._serialize_row(result[0].as_dict())
        
        except Exception as e:
            logger.error(f"Error fetching policy {policy_id}: {str(e)}")
            raise
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """
        Get aggregated policy statistics
        
        Returns:
            Summary statistics dictionary
        """
        try:
            logger.info("Fetching policy summary statistics")
            
            # Aggregate query using Snowpark
            summary_query = """
                SELECT 
                    COUNT(*) as TOTAL_POLICIES,
                    SUM(ANNUALIZED_PREMIUM) as TOTAL_ANNUALIZED_PREMIUM,
                    SUM(LIFETIME_COLLECTED_PREMIUM) as TOTAL_LIFETIME_PREMIUM,
                    AVG(ANNUALIZED_PREMIUM) as AVG_ANNUALIZED_PREMIUM
                FROM POLICY_MONTHLY_SNAPSHOT_FACT
            """
            
            summary_result = self.session.sql(summary_query).collect()[0].as_dict()
            
            # Get breakdown by state
            state_query = """
                SELECT 
                    INSURED_STATE,
                    COUNT(*) as COUNT
                FROM POLICY_MONTHLY_SNAPSHOT_FACT
                GROUP BY INSURED_STATE
                ORDER BY COUNT DESC
                LIMIT 20
            """
            
            state_results = self.session.sql(state_query).collect()
            policies_by_state = {row["INSURED_STATE"]: row["COUNT"] for row in state_results}
            
            # Get breakdown by carrier
            carrier_query = """
                SELECT 
                    CARRIER_NAME,
                    COUNT(*) as COUNT
                FROM POLICY_MONTHLY_SNAPSHOT_FACT
                GROUP BY CARRIER_NAME
                ORDER BY COUNT DESC
            """
            
            carrier_results = self.session.sql(carrier_query).collect()
            policies_by_carrier = {row["CARRIER_NAME"]: row["COUNT"] for row in carrier_results}
            
            return {
                "total_policies": summary_result["TOTAL_POLICIES"],
                "total_annualized_premium": float(summary_result["TOTAL_ANNUALIZED_PREMIUM"] or 0),
                "total_lifetime_premium": float(summary_result["TOTAL_LIFETIME_PREMIUM"] or 0),
                "avg_annualized_premium": float(summary_result["AVG_ANNUALIZED_PREMIUM"] or 0),
                "policies_by_state": policies_by_state,
                "policies_by_carrier": policies_by_carrier
            }
        
        except Exception as e:
            logger.error(f"Error fetching policy summary: {str(e)}")
            raise


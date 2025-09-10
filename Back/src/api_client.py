import httpx
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from .config import API_CONFIG
from .data_models import UDFGroup

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_headers = {
            "Authorization": API_CONFIG['token'],
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.client = httpx.AsyncClient()

    async def fetch_loan_data(self, loan_id: Optional[int] = None, 
                            external_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch loan data from API (matches your working version)"""
        if not loan_id and not external_id:
            raise ValueError("Either loan_id or external_id must be provided")
        
        payload = {
            "params": {
                "parentId": 0,
                "statut": "4"
            },
            "pageSize": 10,
            "pageNumber": 0
        }
        
        if loan_id:
            payload["params"]["loanId"] = loan_id
        if external_id:
            payload["params"]["idLoanExtern"] = external_id

        try:
            response = await self.client.post(
                API_CONFIG['loan_url'],
                json=payload,
                headers=self.base_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("resultsLoans") or len(data["resultsLoans"]) == 0:
                raise ValueError(f"Loan API returned empty results for ID {loan_id or external_id}")
            
            loan_data = data["resultsLoans"][0]
            
            # Ensure IDs are set (as in your working version)
            if loan_id:
                loan_data['loanId'] = loan_id
            if external_id:
                loan_data['idLoanExtern'] = external_id
            
            return loan_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API Error {e.response.status_code}: {e.response.text}")
            raise ValueError(f"API request failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Loan data fetch failed: {str(e)}")
            raise

    async def fetch_udf_data(self, customer_id: str) -> List[UDFGroup]:
        """Fetch UDF data (matches your working version)"""
        payload = {
            "elementId": customer_id,
            "category": "CUSTOMER"
        }

        try:
            response = await self.client.post(
                API_CONFIG['udf_url'],
                json=payload,
                headers=self.base_headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            udf_data = response.json()
            
            if not isinstance(udf_data, list):
                raise ValueError("UDF API returned invalid format")
                
            return udf_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"UDF API Error {e.response.status_code}: {e.response.text}")
            raise ValueError(f"UDF API request failed: {e.response.text}")
        except Exception as e:
            logger.error(f"UDF fetch failed: {str(e)}")
            raise

    async def close(self):
        """Clean up client"""
        try:
            await self.client.aclose()
        except Exception as e:
            logger.warning(f"Error closing client: {str(e)}")
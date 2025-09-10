import csv
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from .api_client import APIClient
from .config import RULES_FILE
from .data_models import CustomerInfo, UDFGroup, UDFField
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.api_client = APIClient()

    async def load_loan_data(self, loan_id: Optional[int] = None, 
                           external_id: Optional[str] = None) -> Dict[str, Any]:
        """Load loan data (matches your working version's structure)"""
        try:
            # Fetch loan data
            loan_data = await self.api_client.fetch_loan_data(loan_id, external_id)
            
            if not loan_data:
                raise ValueError("No loan data received from API")
            
            # Fetch and attach UDF data (same structure as your working version)
            customer_data = loan_data.get('customerDTO', {})
            if customer_id := customer_data.get('id'):
                try:
                    udf_data = await self.api_client.fetch_udf_data(str(customer_id))
                    loan_data['udf_data'] = udf_data  # Same field name as your working version
                except Exception as e:
                    logger.warning(f"UDF fetch failed for customer {customer_id}: {str(e)}")
                    loan_data['udf_data'] = []
            else:
                loan_data['udf_data'] = []
            
            return loan_data
        
        except Exception as e:
            logger.error(f"Error loading loan data: {str(e)}")
            raise

    def load_rules(self) -> Dict[str, Dict[str, float]]:
        """Load rules (identical to your working version)"""
        rules = {}
        try:
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    category = row['Category']
                    if category not in rules:
                        rules[category] = {}
                    rules[category][row['Item']] = float(row['Weight'])
            return rules
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            raise

    @staticmethod
    def format_date(date_str: str) -> str:
        """Format date (identical to your working version)"""
        if not date_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return date_str

    @staticmethod
    def consolidate_customer_info(customer_data: Dict[str, Any]) -> CustomerInfo:
        """Consolidate customer info (identical to your working version)"""
        return {
            'name': customer_data.get('customerName', '').replace('|||', ' '),
            'id': customer_data.get('id', 'N/A'),
            'type': customer_data.get('customerType', 'N/A'),
            'address': customer_data.get('customerAddress', 'N/A'),
            'demographics': {
                'gender': customer_data.get('gender', 'N/A'),
                'marital_status': customer_data.get('maritalStatus', 'N/A'),
                'age': customer_data.get('age', 'N/A'),
                'birth_date': DataLoader.format_date(customer_data.get('dateOfBirth')),
                'phone': customer_data.get('telephone', 'N/A')
            },
            'aml_checks': customer_data.get('acmAmlChecksDTOs', []),
            'udf_data': customer_data.get('udf_data', [])
        }

    async def close(self):
        """Clean up resources"""
        await self.api_client.close()
from typing import Dict, Any, List
from ..data_models import BusinessRuleResult
from ..config import RULE_PRIORITIES

class BusinessRulesEngine:
    def __init__(self):
        self.rules = self._load_business_rules()

    def _load_business_rules(self) -> Dict[str, Dict]:
        return {
            "region_risk": {
                "condition": lambda data: data.get('region') in ["GABES", "TUNIS"],
                "action": lambda data: {"score": 15, "message": "High risk region"},
                "priority": RULE_PRIORITIES['region_risk']
            },
            "loan_amount_threshold": {
                "condition": lambda data: float(data.get('loan_amount', 0)) > 10000,
                "action": lambda data: {"score": 10, "message": "Large loan amount"},
                "priority": RULE_PRIORITIES['loan_amount_threshold']
            }
        }

    def apply_rules(self, loan_data: Dict) -> List[BusinessRuleResult]:
        results = []
        for rule_name, rule in sorted(self.rules.items(), 
                                    key=lambda x: x[1]['priority']):
            if rule['condition'](loan_data):
                result = rule['action'](loan_data)
                results.append(BusinessRuleResult(
                    rule=rule_name,
                    impact=result
                ))
        return results
from typing import Any, Dict, Tuple
from ..data_models import RiskIndicator
from ..config import RISK_THRESHOLDS

class RiskScorer:
    @staticmethod
    def calculate_field_risk(
        field_value: Any,
        field_rules: Dict[str, float],
        default_score: float = 0
    ) -> Tuple[str, float]:
        """Calculate risk score for a single field"""
        str_value = str(field_value).lower()
        for rule, score in field_rules.items():
            if rule.lower() in str_value:
                return (rule, score)
        return ("No matching rule", default_score)

    @staticmethod
    def determine_risk_level(score: float) -> str:
        """Convert numeric score to risk level"""
        if score <= RISK_THRESHOLDS['low']:
            return "low risk"
        elif score <= RISK_THRESHOLDS['medium']:
            return "medium risk"
        elif score <= RISK_THRESHOLDS['high']:
            return "high risk"
        return "very high risk"

    @staticmethod
    def create_risk_indicator(
        value: Any,
        matched_rule: str,
        score: float
    ) -> RiskIndicator:
        """Create a standardized risk indicator"""
        return RiskIndicator(
            value=value,
            matched_rule=matched_rule,
            score=score,
            risk_level=RiskScorer.determine_risk_level(score)
        )
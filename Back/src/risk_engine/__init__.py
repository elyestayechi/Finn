from .base import RiskEngine
from .business_rules import BusinessRulesEngine
from .scoring import RiskScorer

class RiskEngine(RiskEngine, RiskScorer):
    """Combined risk engine with scoring capabilities"""

__all__ = ['RiskEngine', 'BusinessRulesEngine']
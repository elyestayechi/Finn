import pytest
from src.risk_engine import RiskEngine

def test_risk_engine_initialization(mock_rules):
    """Test risk engine initialization with rules"""
    engine = RiskEngine(mock_rules)
    assert engine is not None
    assert hasattr(engine, 'rules')
    assert 'Forme Juridique du B.EFFECTIF' in engine.rules

def test_risk_evaluation(mock_rules, mock_loan_data):
    """Test basic risk evaluation"""
    engine = RiskEngine(mock_rules)
    assessment = engine.evaluate(mock_loan_data)
    
    assert assessment is not None
    assert 'customer_info' in assessment
    assert 'loan_info' in assessment
    assert 'risk_assessment' in assessment
    assert 'indicators' in assessment['risk_assessment']
    assert 'total_score' in assessment['risk_assessment']
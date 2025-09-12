import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_loan_data():
    return {
        "loanId": "12345",
        "idLoanExtern": "EXT123",
        "customerDTO": {
            "customerName": "John Doe",
            "id": "CUST001",
            "customerType": "SA",
            "gender": "M",
            "maritalStatus": "marié",
            "age": "45",
            "customerAddress": "Tunis, Tunisia"
        },
        "loanInfo": {
            "approvelAmount": 50000,
            "personalContribution": 10000,
            "productCode": "LOAN001",
            "termPeriodNum": 36
        }
    }

@pytest.fixture
def mock_rules():
    return {
        "Forme Juridique du B.EFFECTIF": {"SA": 0, "SARL": 2, "Autres": 5},
        "Genre": {"M": 2, "F": 1},
        "Situation familiale": {"marié": 0, "célibataire": 5}
    }

@pytest.fixture
def mock_analysis_result():
    return {
        "summary": "Test analysis summary",
        "recommendation": "approve",
        "rationale": ["Good financial history", "Stable income"],
        "key_findings": ["Low risk profile", "Good collateral"],
        "conditions": ["Verify income documents", "Check collateral valuation"]
    }

# Add async event loop fixture for async tests
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Add fixture for test data directory
@pytest.fixture
def test_data_dir():
    return Path(__file__).parent / "test_data"
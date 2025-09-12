import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.llm import LLMAnalyzer

@pytest.mark.asyncio
async def test_llm_analyzer_initialization():
    """Test LLM analyzer initialization"""
    with patch('src.llm.analyzer.ollama') as mock_ollama:
        mock_ollama.list.return_value = {'models': [{'model': 'deepseek-r1:1.5b'}]}
        analyzer = LLMAnalyzer()
        assert analyzer is not None

@pytest.mark.asyncio
async def test_basic_analysis(mock_loan_data):
    """Test basic loan analysis without vector DB"""
    with patch('src.llm.analyzer.ollama') as mock_ollama:
        mock_ollama.generate.return_value = {
            'response': '{"summary": "Test", "recommendation": "approve", "rationale": [], "key_findings": [], "conditions": []}'
        }
        
        analyzer = LLMAnalyzer()
        analysis = analyzer.analyze_loan(mock_loan_data)
        
        assert analysis is not None
        assert analysis['summary'] == "Test"
        assert analysis['recommendation'] == "approve"
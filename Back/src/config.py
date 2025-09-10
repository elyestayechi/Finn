# config.py
import os
from pathlib import Path
from typing import Dict, Any

# Directory configuration
DATA_DIR = Path('./Data')
LOGS_DIR = DATA_DIR / 'logs'
RULES_FILE = DATA_DIR / 'KYC.LOV.csv'
PDF_DIR = Path('./PDF Loans')
VECTOR_DB_PATH = DATA_DIR / 'loans_vector.db'

# API Configuration
API_CONFIG = {
    'loan_url': "http://172.16.4.110:8080/credit-service/loans/find-pagination",
    'udf_url': "http://172.16.4.110:8080/credit-service/udf-links/find-udf-groupby/",
    'token': "Bearer de2b28f4-2ef5-42eb-9382-ad6d2d5f9f18"
}

# LLM Configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
LLM_CONFIG = {
    'model_name': "deepseek-r1:1.5b",
    'temperature': 0.3,
    'num_ctx': 4096,
    'embedding_model': "nomic-embed-text",
    'base_url': OLLAMA_HOST
}

# Risk scoring thresholds
RISK_THRESHOLDS = {
    'low': 10,
    'medium': 25,
    'high': 50
}

# Business rule priorities
RULE_PRIORITIES = {
    'region_risk': 1,
    'loan_amount_threshold': 2,
    'industry_risk': 3
}

# Logging configuration
LOG_FILE = LOGS_DIR / 'loan_processor.log'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
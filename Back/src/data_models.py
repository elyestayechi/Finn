from typing import TypedDict, Dict, List, Any, Union
from typing_extensions import NotRequired

class UDFField(TypedDict):
    udfFieldID: int
    value: str
    fieldName: str
    udfType: int

class UDFGroup(TypedDict):
    userDefinedFieldGroupName: str
    udfGroupeFieldsModels: List[UDFField]

class CustomerInfo(TypedDict):
    name: str
    id: str
    type: str
    address: NotRequired[str]
    demographics: Dict[str, Any]
    aml_checks: List[Dict[str, Any]]
    udf_data: NotRequired[List[UDFGroup]]

class LoanFinancials(TypedDict):
    loan_amount: float
    personal_contribution: float
    total_interest: float
    monthly_payment: float
    assets_total: float
    apr: float
    interest_rate: float
    term_months: int
    currency: str

class LoanBasicInfo(TypedDict):
    loan_id: str
    external_id: str
    account: str
    status: str
    product: str
    branch: Dict[str, str]

class RiskIndicator(TypedDict):
    value: Any
    matched_rule: str
    score: float
    risk_level: str

class LLMAnalysis(TypedDict):
    summary: str
    recommendation: str
    rationale: Union[str, List[str]]
    key_findings: List[str]
    conditions: List[str]

class BusinessRuleResult(TypedDict):
    rule: str
    impact: Dict[str, Any]

class AgentFeedback(TypedDict):
    loan_id: str
    analyst_id: str
    agent_recommendation: str
    agent_confidence: float
    human_decision: str
    feedback_rating: int  # 1-5 scale
    feedback_comments: str
    timestamp: str
    metadata: Dict[str, Any]

class FeedbackDatabase(TypedDict):
    feedback_id: str
    loan_data: Dict[str, Any]
    original_analysis: Dict[str, Any]
    feedback: AgentFeedback
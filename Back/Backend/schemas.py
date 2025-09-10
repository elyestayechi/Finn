from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class LoanBase(BaseModel):
    loan_id: str
    external_id: Optional[str] = None
    customer_name: str
    loan_amount: float
    currency: str = "TND"

class LoanCreate(LoanBase):
    pass

class Loan(LoanBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnalysisBase(BaseModel):
    loan_id: str
    risk_score: float
    decision: str
    summary: str
    key_findings: List[str]
    conditions: List[str]
    processing_time: float
    confidence: float

class AnalysisCreate(AnalysisBase):
    analysis_id: str

class Analysis(AnalysisBase):
    id: int
    analysis_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackBase(BaseModel):
    loan_id: str
    agent_recommendation: str
    human_decision: str
    rating: int
    comments: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    analyst_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class PDFReportBase(BaseModel):
    loan_id: str
    file_name: str
    file_path: str
    file_size: int

class PDFReportCreate(PDFReportBase):
    pass

class PDFReport(PDFReportBase):
    id: int
    generated_at: datetime

    class Config:
        from_attributes = True

class AnalysisRequest(BaseModel):
    loan_id: Optional[str] = None
    external_id: Optional[str] = None
    notes: Optional[str] = None
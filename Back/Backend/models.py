from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from .database import Base

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String, unique=True, index=True)
    external_id = Column(String, index=True)
    customer_name = Column(String)
    loan_amount = Column(Float)
    currency = Column(String, default="TND")
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, unique=True, index=True)
    loan_id = Column(String, index=True)
    risk_score = Column(Float)
    decision = Column(String)  # approve, deny, review
    summary = Column(Text)
    key_findings = Column(Text)  # JSON string
    conditions = Column(Text)  # JSON string
    processing_time = Column(Float)  # in seconds
    confidence = Column(Float)  # 0-100
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String, index=True)
    analyst_id = Column(String, default="web_user")
    agent_recommendation = Column(String)
    human_decision = Column(String)
    rating = Column(Integer)  # 1-5
    comments = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PDFReport(Base):
    __tablename__ = "pdf_reports"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String, index=True)
    file_name = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)  # in bytes
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
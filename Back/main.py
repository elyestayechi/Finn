import io
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any, Generator
import json
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import re
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import time
from pypdf import PdfReader
from functools import lru_cache
import csv
import logging
import psutil
import threading

# Prometheus imports
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Import backend modules
from Backend.database import get_db, engine, Base
from Backend import models, schemas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Loan Analysis API", 
    version="1.0.0",
    description="API for AI-powered loan analysis system"
)

# Initialize Prometheus instrumentation
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Custom metrics - General request metrics
REQUEST_COUNT = Counter(
    'request_count', 'App Request Count',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'request_latency_seconds', 'Request latency',
    ['method', 'endpoint']
)

# Custom metrics - Loan analysis specific metrics
ANALYSIS_TOTAL = Counter('analysis_total', 'Total loan analyses', ['loan_id'])
ANALYSIS_SUCCESS = Counter('analysis_success_total', 'Successful loan analyses')
ANALYSIS_FAILURE = Counter('analysis_failure_total', 'Failed loan analyses', ['error_type'])
ANALYSIS_PROCESSING_TIME = Histogram('analysis_processing_time_seconds', 'Analysis processing time')
ANALYSIS_DECISION = Counter('analysis_decision_total', 'Analysis decisions', ['decision'])
ANALYSIS_RISK_SCORE = Gauge('analysis_risk_score', 'Risk score of analysis', ['loan_id'])

# Memory usage metric
PROCESS_RAM_USAGE = Gauge(
    'process_ram_usage_mb',
    'Process RAM usage in MB',
    ['service']
)

# CORS middleware configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Serve PDF files statically
pdf_dir = Path("./PDF Loans")
pdf_dir.mkdir(exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=str(pdf_dir)), name="pdfs")

# Performance optimizations
PDF_CACHE = {}
PDF_CACHE_TIMESTAMP = 0
CACHE_DURATION = 30  # seconds

# Thread pool for parallel PDF processing
thread_pool = ThreadPoolExecutor(max_workers=4)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, analysis_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[analysis_id] = websocket

    def disconnect(self, analysis_id: str):
        if analysis_id in self.active_connections:
            del self.active_connections[analysis_id]

    async def send_message(self, analysis_id: str, message: Dict[str, Any]):
        if analysis_id in self.active_connections:
            try:
                await self.active_connections[analysis_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")

manager = ConnectionManager()

def track_memory_usage():
    """Background task to track memory usage"""
    while True:
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            PROCESS_RAM_USAGE.labels(service='backend').set(memory_mb)
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Memory tracking error: {e}")
            time.sleep(60)

# Start the memory tracking thread when the app starts
@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    # Start memory monitoring thread
    memory_thread = threading.Thread(target=track_memory_usage, daemon=True)
    memory_thread.start()
    logger.info("Memory monitoring started")

# Add middleware to track requests
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    endpoint = request.url.path
    
    response = await call_next(request)
    
    latency = time.time() - start_time
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
    REQUEST_COUNT.labels(
        method=method, 
        endpoint=endpoint, 
        http_status=response.status_code
    ).inc()
    
    return response

@app.websocket("/ws/analysis/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    await manager.connect(analysis_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(analysis_id)
        logger.info(f"WebSocket disconnected for analysis {analysis_id}")

# Health check endpoint - FIXED
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection - FIXED for SQLAlchemy 2.0
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy", 
            "message": "Loan Analysis API is running",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/")
def read_root():
    return {"message": "Loan Analysis API", "version": "1.0.0"}

# Add metrics endpoint (optional, as instrumentator already provides one)
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Debug metrics endpoint
@app.get("/debug/metrics")
async def debug_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

async def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF efficiently"""
    try:
        async with aiofiles.open(pdf_path, 'rb') as f:
            content = await f.read()
        
        # Use thread pool for CPU-intensive PDF reading
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(
            thread_pool, 
            lambda: "\n".join(page.extract_text() or '' for page in PdfReader(io.BytesIO(content)).pages)
        )
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

def extract_analysis_data_from_text(text: str, pdf_path: Path) -> Dict[str, Any]:
    """Extract analysis data from text (no file I/O)"""
    try:
        # Extract loan ID from filename
        loan_id_match = re.search(r'loan_assessment_(\d+)_', pdf_path.name)
        loan_id = loan_id_match.group(1) if loan_id_match else "unknown"
        
        # Extract customer name
        name_match = re.search(r"Name:\s*(.*?)(?=\n|\|)", text)
        if not name_match:
            name_match = re.search(r"Nom(?:.*?):\s*(.*?)(?=\n|$)", text, re.IGNORECASE)
        customer_name = name_match.group(1).strip() if name_match else "Unknown Customer"
        
        # Extract risk score
        risk_match = re.search(r"TOTAL RISK SCORE:\s*([\d.]+)", text, re.IGNORECASE)
        risk_score = float(risk_match.group(1)) if risk_match else 0.0
        
        # Extract recommendation
        rec_match = re.search(r"RECOMMENDATION:\s*(\w+)", text, re.IGNORECASE)
        recommendation = rec_match.group(1).lower() if rec_match else "review"
        
        # Extract key findings (simplified for speed)
        key_findings = []
        findings_match = re.search(r"Key Findings:(.*?)(?=Recommended Conditions:|Similar Historical Cases:|$)", text, re.DOTALL | re.IGNORECASE)
        if findings_match:
            findings_text = findings_match.group(1).strip()
            # Quick bullet point extraction
            bullet_points = re.findall(r"[-•*]\s*(.*?)(?=\n[-•*]|\n\n|$)", findings_text)
            key_findings = [point.strip() for point in bullet_points if point.strip()][:3]
        
        # Extract processing time
        processing_time = "N/A"
        time_match = re.search(r"processing_time:\s*([\d.]+)", text)
        if time_match:
            seconds = float(time_match.group(1))
            minutes = seconds / 60
            processing_time = f"{minutes:.1f}min"
        
        # Extract confidence
        confidence = 85
        if risk_score <= 3:
            confidence = 90
        elif risk_score <= 7:
            confidence = 75
        else:
            confidence = 60
        
        # Get file info
        file_stats = pdf_path.stat()
        file_date = datetime.fromtimestamp(file_stats.st_mtime)
        
        return {
            "id": f"LN-{loan_id}",
            "loan_id": loan_id,
            "file_name": pdf_path.name,
            "customer_name": customer_name,
            "risk_score": risk_score,
            "decision": recommendation,
            "key_findings": key_findings,
            "processing_time": processing_time,
            "confidence": confidence,
            "date": file_date.strftime("%Y-%m-%d"),
            "time": file_date.strftime("%H:%M"),
            "file_size": file_stats.st_size,
            "generated_at": file_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error extracting analysis data: {e}")
        return {
            "id": "error",
            "loan_id": "error",
            "file_name": pdf_path.name,
            "customer_name": "Error extracting data",
            "risk_score": 0.0,
            "decision": "review",
            "key_findings": [f"Error processing PDF: {str(e)}"],
            "processing_time": "N/A",
            "confidence": 0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "file_size": 0,
            "generated_at": datetime.now().isoformat()
        }

async def process_pdf_file(pdf_path: Path):
    """Process a single PDF file asynchronously"""
    try:
        text = await extract_text_from_pdf(pdf_path)
        if not text:
            return None
        
        analysis_data = extract_analysis_data_from_text(text, pdf_path)
        # Skip error entries
        if analysis_data.get("risk_score", 0) > 0:
            return analysis_data
        return None
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        return None

async def get_cached_analyses():
    """Get analyses with caching"""
    global PDF_CACHE, PDF_CACHE_TIMESTAMP
    
    current_time = time.time()
    if current_time - PDF_CACHE_TIMESTAMP < CACHE_DURATION and PDF_CACHE:
        return PDF_CACHE
    
    # Get all PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        PDF_CACHE = []
        PDF_CACHE_TIMESTAMP = current_time
        return []
    
    # Process PDFs in parallel
    tasks = [process_pdf_file(pdf_file) for pdf_file in pdf_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None and exceptions
    valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    
    # Sort by date (newest first)
    valid_results.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
    
    PDF_CACHE = valid_results
    PDF_CACHE_TIMESTAMP = current_time
    
    return valid_results

# Loans endpoints
@app.post("/loans/", response_model=schemas.Loan, status_code=status.HTTP_201_CREATED)
def create_loan(loan: schemas.LoanCreate, db: Session = Depends(get_db)):
    try:
        db_loan = db.query(models.Loan).filter(models.Loan.loan_id == loan.loan_id).first()
        if db_loan:
            raise HTTPException(status_code=400, detail="Loan ID already exists")
        
        db_loan = models.Loan(**loan.dict())
        db.add(db_loan)
        db.commit()
        db.refresh(db_loan)
        
        # Notify via WebSocket
        asyncio.run(manager.send_message("new_loan", {
            "type": "loan_created",
            "loan_id": db_loan.loan_id,
            "customer_name": db_loan.customer_name
        }))
        
        return db_loan
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating loan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create loan")

@app.get("/loans/", response_model=List[schemas.Loan])
def read_loans(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        loans = db.query(models.Loan).order_by(models.Loan.created_at.desc()).offset(skip).limit(limit).all()
        return loans
    except Exception as e:
        logger.error(f"Error fetching loans: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch loans")

@app.get("/loans/{loan_id}", response_model=schemas.Loan)
def read_loan(loan_id: str, db: Session = Depends(get_db)):
    try:
        loan = db.query(models.Loan).filter(models.Loan.loan_id == loan_id).first()
        if loan is None:
            raise HTTPException(status_code=404, detail="Loan not found")
        return loan
    except Exception as e:
        logger.error(f"Error fetching loan {loan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch loan")

# PDF analysis endpoint with metrics
@app.get("/api/analysis/{loan_id}")
async def get_loan_analysis(loan_id: str):
    """Get analysis from PDF by extracting text directly"""
    ANALYSIS_TOTAL.labels(loan_id=loan_id).inc()
    start_time = time.time()
    
    try:
        pdf_files = list(pdf_dir.glob(f"*{loan_id}*.pdf"))
        
        if not pdf_files:
            raise HTTPException(status_code=404, detail="PDF not found for this loan ID")
        
        pdf_path = pdf_files[0]
        text = await extract_text_from_pdf(pdf_path)
        
        if not text:
            raise HTTPException(status_code=500, detail="Could not extract text from PDF")
        
        # Extract analysis sections
        summary_match = re.search(r"Summary:(.*?)(?=RECOMMENDATION:|Key Findings:|$)", text, re.DOTALL | re.IGNORECASE)
        recommendation_match = re.search(r"RECOMMENDATION:(.*?)(?=Key Findings:|Detailed Rationale:|$)", text, re.DOTALL | re.IGNORECASE)
        findings_match = re.search(r"Key Findings:(.*?)(?=Recommended Conditions:|Similar Historical Cases:|$)", text, re.DOTALL | re.IGNORECASE)
        conditions_match = re.search(r"Recommended Conditions:(.*?)(?=Similar Historical Cases:|Branch Information:|$)", text, re.DOTALL | re.IGNORECASE)
        
        analysis = {
            "summary": summary_match.group(1).strip() if summary_match else "No summary available",
            "recommendation": recommendation_match.group(1).strip().lower() if recommendation_match else "review",
            "key_findings": [],
            "conditions": []
        }
        
        if findings_match:
            findings_text = findings_match.group(1).strip()
            analysis["key_findings"] = [
                line.replace("-", "").strip() 
                for line in findings_text.split("\n") 
                if line.strip() and not line.startswith("=")
            ][:3]
        
        if conditions_match:
            conditions_text = conditions_match.group(1).strip()
            analysis["conditions"] = [
                line.replace("-", "").strip() 
                for line in conditions_text.split("\n") 
                if line.strip() and not line.startswith("=")
            ][:3]
        
        # Record success and metrics
        ANALYSIS_SUCCESS.inc()
        ANALYSIS_DECISION.labels(decision=analysis["recommendation"]).inc()
        
        # Extract risk score for metrics
        risk_match = re.search(r"TOTAL RISK SCORE:\s*([\d.]+)", text, re.IGNORECASE)
        if risk_match:
            risk_score = float(risk_match.group(1))
            ANALYSIS_RISK_SCORE.labels(loan_id=loan_id).set(risk_score)
        
        return analysis
        
    except Exception as e:
        error_type = type(e).__name__
        ANALYSIS_FAILURE.labels(error_type=error_type).inc()
        logger.error(f"Error extracting analysis for loan {loan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error extracting analysis: {str(e)}")
    finally:
        processing_time = time.time() - start_time
        ANALYSIS_PROCESSING_TIME.observe(processing_time)

# Get recent analyses - OPTIMIZED VERSION
@app.get("/api/analyses/recent", response_model=List[Dict[str, Any]])
async def get_recent_analyses(
    skip: int = 0,
    limit: int = 100,
    decision: Optional[str] = None,
    customer_name: Optional[str] = None
):
    """Get recent analyses with filtering options - FAST VERSION"""
    try:
        # Get cached analyses
        all_analyses = await get_cached_analyses()
        
        if not all_analyses:
            return []
        
        # Apply filters
        filtered_analyses = all_analyses
        
        if decision:
            filtered_analyses = [a for a in filtered_analyses if a.get('decision') == decision]
        
        if customer_name:
            filtered_analyses = [a for a in filtered_analyses 
                               if customer_name.lower() in a.get('customer_name', '').lower()]
        
        # Apply pagination
        return filtered_analyses[skip:skip + limit]
        
    except Exception as e:
        logger.error(f"Error fetching analyses: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching analyses: {str(e)}")

# Analysis creation endpoint (simplified) with metrics
@app.post("/api/analyses")
async def create_analysis(loan_data: Dict[str, Any]):
    """Create a new loan analysis (simulated for frontend compatibility)"""
    loan_id = loan_data.get('loan_id', 'unknown')
    ANALYSIS_TOTAL.labels(loan_id=loan_id).inc()
    start_time = time.time()
    
    try:
        analysis_id = str(uuid.uuid4())
        
        # Simulate analysis process
        asyncio.run(manager.send_message(analysis_id, {
            "type": "status",
            "message": "Analysis started",
            "progress": 10
        }))
        
        await asyncio.sleep(1)
        
        asyncio.run(manager.send_message(analysis_id, {
            "type": "status", 
            "message": "Processing data",
            "progress": 50
        }))
        
        await asyncio.sleep(1)
        
        asyncio.run(manager.send_message(analysis_id, {
            "type": "status",
            "message": "Analysis complete",
            "progress": 100
        }))
        
        # Record success
        ANALYSIS_SUCCESS.inc()
        ANALYSIS_DECISION.labels(decision="approved").inc()  # Default decision for simulation
        ANALYSIS_RISK_SCORE.labels(loan_id=loan_id).set(5.0)  # Default risk score
        
        return {"analysis_id": analysis_id}
        
    except Exception as e:
        error_type = type(e).__name__
        ANALYSIS_FAILURE.labels(error_type=error_type).inc()
        logger.error(f"Error creating analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating analysis: {str(e)}")
    finally:
        processing_time = time.time() - start_time
        ANALYSIS_PROCESSING_TIME.observe(processing_time)

# Feedback endpoints
@app.post("/feedback/", response_model=schemas.Feedback, status_code=status.HTTP_201_CREATED)
def create_feedback(feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    try:
        # Check if loan exists
        loan = db.query(models.Loan).filter(models.Loan.loan_id == feedback.loan_id).first()
        if not loan:
            # Create loan if it doesn't exist
            loan = models.Loan(
                loan_id=feedback.loan_id,
                customer_name="Unknown Customer",
                loan_amount=0.0,
                currency="TND",
                status="completed"
            )
            db.add(loan)
            db.commit()
            db.refresh(loan)
        
        # Also save to JSON file
        save_feedback_to_json({
            'loan_id': feedback.loan_id,
            'analyst_id': 'web_user',
            'agent_recommendation': feedback.agent_recommendation,
            'human_decision': feedback.human_decision,
            'rating': feedback.rating,
            'comments': feedback.comments,
            'timestamp': datetime.now().isoformat()
        })
        
        db_feedback = models.Feedback(
            loan_id=feedback.loan_id,
            agent_recommendation=feedback.agent_recommendation,
            human_decision=feedback.human_decision,
            rating=feedback.rating,
            comments=feedback.comments
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        # Notify via WebSocket
        asyncio.run(manager.send_message("new_feedback", {
            "type": "feedback_created",
            "loan_id": feedback.loan_id,
            "rating": feedback.rating
        }))
        
        return db_feedback
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to create feedback")

def save_feedback_to_json(feedback_data: Dict[str, Any]):
    """Save feedback to JSON file"""
    try:
        feedback_file = Path("./Data/feedback_db.json")
        feedback_file.parent.mkdir(exist_ok=True)
        
        if feedback_file.exists():
            with open(feedback_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"feedback_entries": []}
        
        feedback_entry = {
            "feedback_id": f"fb_{feedback_data['loan_id']}_{int(datetime.now().timestamp())}",
            "loan_data": {
                "loan_id": feedback_data['loan_id'],
                "pdf_path": f"PDF Loans/loan_assessment_{feedback_data['loan_id']}_*.pdf"
            },
            "original_analysis": {
                "summary": "Extracted from PDF analysis",
                "recommendation": feedback_data['agent_recommendation'],
                "key_findings": [],
                "conditions": []
            },
            "feedback": feedback_data
        }
        
        data['feedback_entries'].append(feedback_entry)
        
        with open(feedback_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving feedback to JSON: {e}")

@app.get("/feedback/loan/{loan_id}", response_model=List[schemas.Feedback])
def get_loan_feedback(loan_id: str, db: Session = Depends(get_db)):
    try:
        feedback = db.query(models.Feedback).filter(models.Feedback.loan_id == loan_id).all()
        return feedback
    except Exception as e:
        logger.error(f"Error fetching feedback for loan {loan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch feedback")

@app.get("/feedback/", response_model=List[schemas.Feedback])
def read_all_feedback(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        feedback = db.query(models.Feedback).order_by(models.Feedback.created_at.desc()).offset(skip).limit(limit).all()
        return feedback
    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch feedback")

# PDF reports endpoints
@app.get("/pdf-reports/", response_model=List[schemas.PDFReport])
def read_all_pdf_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        reports = db.query(models.PDFReport).order_by(models.PDFReport.generated_at.desc()).offset(skip).limit(limit).all()
        return reports
    except Exception as e:
        logger.error(f"Error fetching PDF reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch PDF reports")

@app.get("/pdf-reports/loan/{loan_id}", response_model=schemas.PDFReport)
def get_pdf_report_by_loan_id(loan_id: str, db: Session = Depends(get_db)):
    try:
        report = db.query(models.PDFReport).filter(models.PDFReport.loan_id == loan_id).order_by(models.PDFReport.generated_at.desc()).first()
        if not report:
            raise HTTPException(status_code=404, detail="PDF report not found")
        return report
    except Exception as e:
        logger.error(f"Error fetching PDF report for loan {loan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch PDF report")

# Rules management endpoints
@app.get("/api/rules", response_model=List[Dict[str, Any]])
def get_rules():
    """Get all risk rules"""
    try:
        rules_file = Path("./Data/KYC.LOV.csv")
        rules = []
        
        if rules_file.exists():
            with open(rules_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rules = list(reader)
        
        return rules
    except Exception as e:
        logger.error(f"Error fetching rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch rules")

@app.post("/api/rules")
def update_rules(updated_rules: List[Dict[str, Any]]):
    """Update risk rules"""
    try:
        rules_file = Path("./Data/KYC.LOV.csv")
        
        fieldnames = ['Category', 'Item', 'Weight']
        
        with open(rules_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rules)
        
        # Notify via WebSocket
        asyncio.run(manager.send_message("rules_updated", {
            "type": "rules_updated",
            "count": len(updated_rules)
        }))
        
        return {"message": "Rules updated successfully"}
    except Exception as e:
        logger.error(f"Error updating rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to update rules")

@app.post("/api/rules/reset")
def reset_rules():
    """Reset rules to default"""
    try:
        default_rules = [
            {'Category': 'Forme Juridique du B.EFFECTIF', 'Item': 'SA', 'Weight': '0'},
            {'Category': 'Forme Juridique du B.EFFECTIF', 'Item': 'SUARL', 'Weight': '0'},
            {'Category': 'Forme Juridique du B.EFFECTIF', 'Item': 'SARL', 'Weight': '0'},
            {'Category': 'Forme Juridique du B.EFFECTIF', 'Item': 'Société Personne Physique', 'Weight': '2'},
            {'Category': 'Forme Juridique du B.EFFECTIF', 'Item': 'ONG', 'Weight': '5'},
            {'Category': 'Forme Juridique du B.EFFECTIF', 'Item': 'Autres', 'Weight': '5'},
            {'Category': 'Raison de financement', 'Item': 'Matériels et Equipements', 'Weight': '0'},
            {'Category': 'Raison de financement', 'Item': 'Moyens de transport', 'Weight': '15'},
            {'Category': 'Raison de financement', 'Item': 'Marchandises', 'Weight': '0'},
            {'Category': 'Raison de financement', 'Item': 'Produits agricoles', 'Weight': '7.5'},
            {'Category': 'Raison de financement', 'Item': 'Produits d\'élevage', 'Weight': '10'},
            {'Category': 'Raison de financement', 'Item': 'Rénovation et amenagement', 'Weight': '2.5'},
            {'Category': 'Raison de financement', 'Item': 'Services', 'Weight': '2.5'},
            {'Category': 'Genre', 'Item': 'M', 'Weight': '2'},
            {'Category': 'Genre', 'Item': 'F', 'Weight': '1'},
            {'Category': 'Situation familiale', 'Item': 'Veuf', 'Weight': '1'},
            {'Category': 'Situation familiale', 'Item': 'Marié', 'Weight': '0'},
            {'Category': 'Situation familiale', 'Item': 'Célibataire', 'Weight': '5'},
            {'Category': 'Situation familiale', 'Item': 'Divorcé', 'Weight': '2'},
            {'Category': 'Catégorie de l\'activité', 'Item': 'Personne morale', 'Weight': '1'},
            {'Category': 'Catégorie de l\'activité', 'Item': 'Personne Physique', 'Weight': '3'},
            {'Category': 'Produit', 'Item': 'Aouda Madrassiy', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'CV_Arboricultur', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'CV_Bovine', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'CV_Culture Mara', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'CV_Grande Cultu', 'Weight': '2.5'},
            {'Category': 'Produit', 'Item': 'CV_Ovine', 'Weight': '5'},
            {'Category': 'Produit', 'Item': 'Eco Panneau', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'Equip Frigorifi', 'Weight': '5'},
            {'Category': 'Produit', 'Item': 'Herfeti', 'Weight': '2.5'},
            {'Category': 'Produit', 'Item': 'Karhabti', 'Weight': '10'},
            {'Category': 'Produit', 'Item': 'Maktabati', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'Mechiati', 'Weight': '5'},
            {'Category': 'Produit', 'Item': 'Peinture de bat', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'Produit Agricol', 'Weight': '2.5'},
            {'Category': 'Produit', 'Item': 'Taamir', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'Tabrid', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'Tafawouak', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'Tarmim', 'Weight': '0'},
            {'Category': 'Produit', 'Item': 'Tijarati', 'Weight': '5'},
            {'Category': 'Produit', 'Item': 'Tok tok', 'Weight': '5'},
            {'Category': 'Produit', 'Item': 'Ziraati', 'Weight': '7.5'},
            {'Category': 'Région', 'Item': 'ARIANA', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'BEJA', 'Weight': '5'},
            {'Category': 'Région', 'Item': 'BEN AROUS', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'BIZERTE', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'GABES', 'Weight': '15'},
            {'Category': 'Région', 'Item': 'GAFSA', 'Weight': '20'},
            {'Category': 'Région', 'Item': 'JENDOUBA', 'Weight': '20'},
            {'Category': 'Région', 'Item': 'KAIROUAN', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'KASSERINE', 'Weight': '20'},
            {'Category': 'Région', 'Item': 'KEBILI', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'LE KEF', 'Weight': '20'},
            {'Category': 'Région', 'Item': 'MAHDIA', 'Weight': '15'},
            {'Category': 'Région', 'Item': 'MANOUBA', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'MEDENINE', 'Weight': '15'},
            {'Category': 'Région', 'Item': 'MONASTIR', 'Weight': '5'},
            {'Category': 'Région', 'Item': 'NABEUL', 'Weight': '5'},
            {'Category': 'Région', 'Item': 'SFAX', 'Weight': '15'},
            {'Category': 'Région', 'Item': 'SIDI BOUZID', 'Weight': '15'},
            {'Category': 'Région', 'Item': 'SILIANA', 'Weight': '5'},
            {'Category': 'Région', 'Item': 'SOUSSE', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'TATAOUINE', 'Weight': '5'},
            {'Category': 'Région', 'Item': 'TOZEUR', 'Weight': '10'},
            {'Category': 'Région', 'Item': 'TUNIS', 'Weight': '5'},
            {'Category': 'Région', 'Item': 'ZAGHOUAN', 'Weight': '5'},
            {'Category': 'Résident', 'Item': 'Oui', 'Weight': '1'},
            {'Category': 'Résident', 'Item': 'Non', 'Weight': '3'},
            {'Category': 'Patenté', 'Item': 'Oui', 'Weight': '0'},
            {'Category': 'Patenté', 'Item': 'Non', 'Weight': '2'},
            {'Category': 'Type d\'activité', 'Item': 'Formel', 'Weight': '1'},
            {'Category': 'Type d\'activité', 'Item': 'Informel', 'Weight': '2'},
            {'Category': 'BENEFICIAIRE EFFECTIF', 'Item': 'Oui', 'Weight': '0'},
            {'Category': 'BENEFICIAIRE EFFECTIF', 'Item': 'Non', 'Weight': '2'},
            {'Category': 'Secteur d\'activité', 'Item': 'Agriculture', 'Weight': '5'},
            {'Category': 'Secteur d\'activité', 'Item': 'Amelioration du logement', 'Weight': '3'},
            {'Category': 'Secteur d\'activité', 'Item': 'Artisanat', 'Weight': '3'},
            {'Category': 'Secteur d\'activité', 'Item': 'Autres ACV', 'Weight': '3'},
            {'Category': 'Secteur d\'activité', 'Item': 'Commerce', 'Weight': '4'},
            {'Category': 'Secteur d\'activité', 'Item': 'Education', 'Weight': '0'},
            {'Category': 'Secteur d\'activité', 'Item': 'Elevage', 'Weight': '7'},
            {'Category': 'Secteur d\'activité', 'Item': 'Pêche', 'Weight': '10'},
            {'Category': 'Secteur d\'activité', 'Item': 'Production', 'Weight': '4'},
            {'Category': 'Secteur d\'activité', 'Item': 'Services', 'Weight': '5'},
            {'Category': 'Niveau d\'étude', 'Item': 'Analphabète', 'Weight': '5'},
            {'Category': 'Niveau d\'étude', 'Item': 'Primaire', 'Weight': '3'},
            {'Category': 'Niveau d\'étude', 'Item': 'Secondaire', 'Weight': '1'},
            {'Category': 'Niveau d\'étude', 'Item': 'Supérieur', 'Weight': '0'},
            {'Category': 'Type de logement', 'Item': 'Propriétaire', 'Weight': '0'},
            {'Category': 'Type de logement', 'Item': 'Locataire', 'Weight': '5'},
            {'Category': 'Type de logement', 'Item': 'Logé gratuitement', 'Weight': '5'},
            {'Category': 'Couverture sociale', 'Item': 'Oui', 'Weight': '0'},
            {'Category': 'Couverture sociale', 'Item': 'Non', 'Weight': '2'}
        ]
        
        rules_file = Path("./Data/KYC.LOV.csv")
        fieldnames = ['Category', 'Item', 'Weight']
        
        with open(rules_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(default_rules)
        
        # Notify via WebSocket
        asyncio.run(manager.send_message("rules_reset", {
            "type": "rules_reset",
            "count": len(default_rules)
        }))
        
        return {"message": "Rules reset to default"}
    except Exception as e:
        logger.error(f"Error resetting rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset rules")

# Clear cache endpoint for development
@app.post("/clear-cache")
async def clear_cache():
    """Clear the PDF cache (for development)"""
    global PDF_CACHE, PDF_CACHE_TIMESTAMP
    PDF_CACHE = {}
    PDF_CACHE_TIMESTAMP = 0
    return {"status": "cache cleared"}

# Database statistics endpoint
@app.get("/api/stats")
def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    try:
        loans_count = db.query(models.Loan).count()
        analyses_count = db.query(models.Analysis).count()
        feedback_count = db.query(models.Feedback).count()
        reports_count = db.query(models.PDFReport).count()
        
        return {
            "loans": loans_count,
            "analyses": analyses_count,
            "feedback": feedback_count,
            "reports": reports_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch database statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=2)
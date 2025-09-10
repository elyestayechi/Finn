import logging
from pathlib import Path
import time
from typing import Dict, Any, Optional
from datetime import datetime
import json
from pypdf import PdfReader
from ..config import DATA_DIR, PDF_DIR

logger = logging.getLogger(__name__)

class FeedbackSystem:
    def __init__(self, vector_db=None):
        self.feedback_db_path = DATA_DIR / "feedback_db.json"
        self.vector_db = vector_db
        self._initialize_feedback_db()

    def _initialize_feedback_db(self):
        """Initialize feedback database file if it doesn't exist"""
        if not self.feedback_db_path.exists():
            with open(self.feedback_db_path, 'w') as f:
                json.dump({"feedback_entries": []}, f)

    def _load_feedback_db(self) -> Dict[str, Any]:
        """Load the feedback database"""
        try:
            with open(self.feedback_db_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load feedback DB: {str(e)}")
            return {"feedback_entries": []}

    def _save_feedback_db(self, data: Dict[str, Any]):
        """Save the feedback database"""
        try:
            with open(self.feedback_db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feedback DB: {str(e)}")

    def find_loan_pdf(self, loan_id: str) -> Optional[Path]:
        """Locate PDF report by loan ID"""
        for pdf_file in PDF_DIR.glob(f"*{loan_id}*.pdf"):
            return pdf_file
        return None

    def extract_analysis_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract analysis from PDF with robust error handling"""
        result = {
            "summary": "Not extracted",
            "recommendation": "review",
            "key_findings": [],
            "conditions": []
        }
        
        try:
            with pdf_path.open('rb') as f:
                reader = PdfReader(f)
                text = "\n".join(page.extract_text() or '' for page in reader.pages)
                
                if "AI Risk Analysis" in text and "Summary:" in text:
                    result["summary"] = text.split("Summary:")[1].split("\n\n")[0].strip()
                
                if "RECOMMENDATION:" in text:
                    result["recommendation"] = text.split("RECOMMENDATION:")[1].split("\n")[0].strip().lower()
                
                if "Key Findings:" in text:
                    findings_section = text.split("Key Findings:")[1]
                    result["key_findings"] = [
                        line.replace("-", "").strip() 
                        for line in findings_section.split("\n") 
                        if line.strip() and not line.startswith("=")
                    ][:10]
                
                if "Recommended Conditions:" in text:
                    cond_section = text.split("Recommended Conditions:")[1]
                    result["conditions"] = [
                        line.replace("-", "").strip() 
                        for line in cond_section.split("\n") 
                        if line.strip() and not line.startswith("=")
                    ][:10]
                    
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
        
        return result

    def get_loan_analysis(self, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get loan analysis by extracting from PDF"""
        pdf_path = self.find_loan_pdf(loan_id)
        if not pdf_path:
            logger.error(f"No PDF found for loan {loan_id}")
            return None
            
        return self.extract_analysis_from_pdf(pdf_path)

    def store_feedback(self, loan_id: str, feedback_data: Dict[str, Any]) -> bool:
        """Store feedback for a specific loan analysis - updated to match JSON structure"""
        try:
            # Get the original analysis from PDF
            analysis = self.get_loan_analysis(loan_id)
            if not analysis:
                raise ValueError(f"No analysis found for loan {loan_id}")

            # Create feedback entry matching the JSON structure
            feedback_entry = {
                'loan_id': loan_id,
                'analyst_id': feedback_data.get('analyst_id', 'human_1'),
                'agent_recommendation': analysis.get('recommendation', ''),
                'human_decision': feedback_data.get('human_decision', ''),
                'rating': int(feedback_data.get('rating', 3)),
                'comments': feedback_data.get('comments', ''),
                'timestamp': datetime.now().isoformat()
            }

            # Store in feedback DB with the correct structure
            db = self._load_feedback_db()
            db['feedback_entries'].append({
                'feedback_id': f"fb_{loan_id}_{int(time.time())}",
                'loan_data': {
                    'loan_id': loan_id,
                    'pdf_path': str(self.find_loan_pdf(loan_id))
                },
                'original_analysis': analysis,
                'feedback': feedback_entry
            })
            self._save_feedback_db(db)
        
            logger.info(f"Feedback stored for loan {loan_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store feedback: {str(e)}")
            return False
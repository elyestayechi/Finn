import logging
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import questionary
from colorama import Fore, Style
from src.llm.feedback import FeedbackSystem
from src.config import PDF_DIR

logger = logging.getLogger(__name__)

class FeedbackCLI:
    def __init__(self):
        self.feedback_system = FeedbackSystem()

    def find_pdf_by_id(self, loan_id: str) -> Optional[Path]:
        """Find PDF by loan ID"""
        for pdf_file in PDF_DIR.glob(f"*{loan_id}*.pdf"):
            return pdf_file
        return None

    def display_analysis(self, analysis: Dict[str, Any]):
        """Display analysis in a user-friendly way"""
        print(f"\n{Fore.BLUE}=== AI ANALYSIS SUMMARY ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}{analysis.get('summary', 'No summary')}{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}=== RECOMMENDATION ==={Style.RESET_ALL}")
        rec = analysis.get('recommendation', 'review').upper()
        color = Fore.GREEN if rec == 'APPROVE' else Fore.RED if rec == 'DENY' else Fore.YELLOW
        print(f"{color}{rec}{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}=== KEY FINDINGS ==={Style.RESET_ALL}")
        for finding in analysis.get('key_findings', []):
            print(f"- {finding}")
            
        print(f"\n{Fore.BLUE}=== CONDITIONS ==={Style.RESET_ALL}")
        for condition in analysis.get('conditions', []):
            print(f"- {condition}")

    async def collect_feedback(self, loan_id: str):
        """Interactive feedback collection"""
        analysis = self.feedback_system.get_loan_analysis(loan_id)
        if not analysis:
            print(f"{Fore.RED}No analysis found for loan {loan_id}{Style.RESET_ALL}")
            return

        self.display_analysis(analysis)
        
        print(f"\n{Fore.GREEN}=== PROVIDE FEEDBACK ==={Style.RESET_ALL}")
        
        feedback_data = {
            'human_decision': await questionary.select(
                "What was the final decision?",
                choices=["approve", "deny", "review"],
                default=analysis.get('recommendation', 'review')
            ).ask_async(),
            'rating': await questionary.select(
                "Rate the AI's analysis (1-5):",
                choices=["1", "2", "3", "4", "5"],
                default="3"
            ).ask_async(),
            'comments': await questionary.text(
                "Provide detailed feedback (what was good/bad, what to improve):"
            ).ask_async()
        }
        
        # Store feedback
        if await questionary.confirm("Submit this feedback?").ask_async():
            success = self.feedback_system.store_feedback(loan_id, feedback_data)
            if success:
                print(f"{Fore.GREEN}Feedback successfully recorded!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to store feedback{Style.RESET_ALL}")

    async def run(self):
        """Main CLI interface"""
        print(f"{Fore.BLUE}=== Loan Analysis Feedback System ==={Style.RESET_ALL}")
        
        while True:
            loan_id = await questionary.text(
                "Enter Loan ID (or 'quit' to exit):",
                validate=lambda x: x.lower() == 'quit' or x.isdigit()
            ).ask_async()
            
            if loan_id.lower() == 'quit':
                break
                
            pdf_path = self.find_pdf_by_id(loan_id)
            if not pdf_path:
                print(f"{Fore.YELLOW}No PDF found for loan {loan_id}{Style.RESET_ALL}")
                continue
                
            await self.collect_feedback(loan_id)
            
            if not await questionary.confirm("Provide feedback for another loan?").ask_async():
                break

if __name__ == "__main__":
    import asyncio
    from src.config import LOG_FILE
    
    async def main():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, mode='a'),
                logging.StreamHandler()
            ]
        )
        cli = FeedbackCLI()
        await cli.run()
    
    asyncio.run(main())
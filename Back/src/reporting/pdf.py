from datetime import datetime
from pathlib import Path
import re
from fpdf import FPDF
import unicodedata
import os
import logging
import arabic_reshaper
from bidi.algorithm import get_display
from typing import Dict, List, Any, Union

logger = logging.getLogger(__name__)

class ProfessionalPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Page configuration
        self.page_width = 210  # A4 width in mm
        self.margin = 15
        self.content_width = self.page_width - (2 * self.margin)
        
        # Font configuration - no Helvetica fallback
        self.default_font = None
        self._unicode_font_loaded = False
        
        # Configure document settings
        self.set_auto_page_break(auto=True, margin=self.margin)
        self.set_margins(self.margin, self.margin, self.margin)
        
        # Load fonts and styles
        self._load_fonts()
        if not self._unicode_font_loaded:
            raise RuntimeError("Failed to load required Unicode fonts")
            
        self.styles = self._define_styles()
        self._setup_metadata()
        self._header_printed = False

    def _load_fonts(self):
        """Load and configure Unicode fonts with comprehensive error handling"""
        project_root = Path(__file__).parent.parent.parent
        fonts_dir = project_root / 'Fonts'
        
        logger.debug(f"Searching for fonts in: {fonts_dir}")
        
        if not fonts_dir.exists():
            logger.error(f"Font directory not found at: {fonts_dir}")
            logger.error(f"Directory contents at project root: {list(project_root.iterdir())}")
            return False

        # Try loading DejaVu Sans first (complete Unicode support)
        dejavu_success = self._load_font_family(
            name='DejaVu',
            files={
                '': 'DejaVuSans.ttf',
                'B': 'DejaVuSans-Bold.ttf',
                'I': 'DejaVuSans-Oblique.ttf',
                'BI': 'DejaVuSans-BoldOblique.ttf'
            },
            fonts_dir=fonts_dir
        )
        
        if dejavu_success:
            return True

        # Fallback to Noto Sans if DejaVu fails
        noto_success = self._load_font_family(
            name='NotoSans',
            files={
                '': 'NotoSans-Regular.ttf',
                'B': 'NotoSans-Bold.ttf'
            },
            fonts_dir=fonts_dir
        )
        
        if noto_success:
            return True

        logger.error("""
        CRITICAL FONT LOADING FAILURE
        =============================
        Required fonts not found in Fonts/ directory.
        Please provide either:
        1. Complete DejaVu Sans family:
           - DejaVuSans.ttf
           - DejaVuSans-Bold.ttf
           - DejaVuSans-Oblique.ttf
           - DejaVuSans-BoldOblique.ttf
        OR
        2. Noto Sans family:
           - NotoSans-Regular.ttf
           - NotoSans-Bold.ttf
        """)
        return False

    def _load_font_family(self, name: str, files: Dict[str, str], fonts_dir: Path) -> bool:
        """Helper method to load a font family with all variants"""
        try:
            # Verify all required files exist
            missing_files = [f for f in files.values() if not (fonts_dir / f).exists()]
            if missing_files:
                logger.warning(f"Missing files for {name}: {missing_files}")
                return False

            # Load each font variant
            for style, filename in files.items():
                font_path = str(fonts_dir / filename)
                self.add_font(name, style, font_path, uni=True)
                logger.debug(f"Loaded font: {name}-{style} from {filename}")

            self.default_font = name
            self._unicode_font_loaded = True
            logger.info(f"Successfully loaded {name} font family")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load {name} fonts: {str(e)}")
            return False

    def _define_styles(self):
        """Complete style configuration matching your original requirements"""
        return {
            'header': {
                'fill_color': (0, 51, 102),
                'text_color': (255, 255, 255),
                'font_size': 16,
                'font_style': 'B',
                'line_height': 10
            },
            'section': {
                'fill_color': (70, 130, 180),
                'text_color': (0, 0, 0),
                'font_size': 12,
                'font_style': 'B',
                'spacing_before': 10,
                'spacing_after': 5,
                'line_height': 8
            },
            'subsection': {
                'text_color': (70, 130, 180),
                'font_size': 11,
                'font_style': 'B',
                'underline': True,
                'spacing_before': 8,
                'spacing_after': 4,
                'line_height': 7
            },
            'risk_high': {
                'text_color': (178, 34, 34),
                'fill_color': (255, 200, 200),
                'font_style': 'B',
                'font_size': 10,
                'line_height': 6
            },
            'risk_medium': {
                'text_color': (255, 140, 0),
                'fill_color': (255, 235, 200),
                'font_style': '',
                'font_size': 10,
                'line_height': 6
            },
            'risk_low': {
                'text_color': (0, 100, 0),
                'fill_color': (200, 255, 200),
                'font_style': '',
                'font_size': 10,
                'line_height': 6
            },
            'normal': {
                'text_color': (0, 0, 0),
                'font_size': 10,
                'font_style': '',
                'line_height': 6
            },
            'bold': {
                'text_color': (0, 0, 0),
                'font_size': 10,
                'font_style': 'B',
                'line_height': 6
            },
            'small': {
                'text_color': (100, 100, 100),
                'font_size': 8,
                'font_style': '',
                'line_height': 5
            },
            'case_header': {
                'text_color': (70, 130, 180),
                'font_size': 10,
                'font_style': 'B',
                'line_height': 7
            },
            'total_score': {
                'text_color': (0, 0, 139),
                'font_size': 14,
                'font_style': 'B',
                'line_height': 10
            }
        }

    def _setup_metadata(self):
        """Configure document metadata"""
        self.title = "Loan Risk Assessment Report"
        self.author = "Bank Risk Analysis System"
        self.creator = "AI-Powered Risk Engine"
        self.header_text = self.title
        self.footer_text = f"Confidential - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def header(self):
        """Custom header implementation"""
        if not self._header_printed:
            style = self.styles['header']
            self.set_font(self.default_font, style['font_style'], style['font_size'])
            self.set_text_color(*style['text_color'])
            self.set_fill_color(*style['fill_color'])
            self.cell(0, 10, self.header_text, border=0, ln=1, align='C', fill=True)
            self.ln(5)
            self._header_printed = True
    
    def footer(self):
        """Custom footer implementation"""
        self.set_y(-15)
        style = self.styles['small']
        self.set_font(self.default_font, style['font_style'], style['font_size'])
        self.set_text_color(*style['text_color'])
        self.cell(0, 5, self.footer_text, 0, 0, 'L')
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", 0, 0, 'R')

    def _process_text(self, text: str) -> str:
        """Process text for proper Unicode and RTL rendering"""
        if not isinstance(text, str):
            text = str(text)
        
        # Normalize Unicode
        text = unicodedata.normalize('NFC', text)
        
        # Handle Arabic/RTL text
        if any('\u0600' <= c <= '\u06FF' for c in text):
            try:
                reshaped = arabic_reshaper.reshape(text)
                return get_display(reshaped)
            except Exception as e:
                logger.warning(f"Arabic text processing failed: {str(e)}")
                return text[::-1]  # Simple reversal as fallback
        
        return text

    def _safe_multi_cell(self, w, h, txt, border=0, align='L', fill=False):
        """Robust text rendering with full Unicode support"""
        processed_text = self._process_text(txt)
        try:
            self.multi_cell(w, h, processed_text, border, align, fill)
        except Exception as e:
            logger.error(f"Text rendering error: {str(e)}")
            self.set_font(self.default_font, '', 8)
            self.multi_cell(w, h, "[Content rendering error]", border, align, fill)

    def add_section(self, title: str, level: int = 1):
        """Add a section header with consistent styling"""
        style_name = 'section' if level == 1 else 'subsection'
        style = self.styles[style_name]
        
        self.ln(style['spacing_before'])
        self.set_font(self.default_font, style['font_style'], style['font_size'])
        self.set_text_color(*style['text_color'])
        
        if style.get('underline'):
            self.cell(0, 5, title, 'B', 1)
        else:
            self.cell(0, 5, title, 0, 1)
        
        self.set_text_color(0, 0, 0)
        self.ln(style['spacing_after'])
    
    def add_key_value_table(self, data: Dict[str, Any], col_width: int = 50):
        """Add a key-value table with consistent formatting"""
        style_normal = self.styles['normal']
        style_bold = self.styles['bold']
        
        self.set_font(self.default_font, style_normal['font_style'], style_normal['font_size'])
        
        for key, value in data.items():
            # Key column
            self.set_font(self.default_font, style_bold['font_style'], style_bold['font_size'])
            self.cell(col_width, style_bold['line_height'], f"{key}:", border=0)
            
            # Value column
            self.set_font(self.default_font, style_normal['font_style'], style_normal['font_size'])
            self._safe_multi_cell(0, style_normal['line_height'], str(value), align='L')
            self.ln(3)
        
        self.ln(5)

    def _add_risk_table(self, risk_data: Dict[str, Dict[str, Any]]):
        """Add a formatted risk assessment table with UDF fields"""
        # Calculate and display total score prominently
        total_score = sum(
        float(v.get('score', 0)) 
        for k, v in risk_data.items() 
        if not k.startswith('aml_')  # Exclude AML scores
    )
        style = self.styles['total_score']
        
        self.set_font(self.default_font, style['font_style'], style['font_size'])
        self.set_text_color(*style['text_color'])
        self.cell(0, style['line_height'], f"TOTAL RISK SCORE: {total_score:.1f}", ln=1, align='C')
        self.set_text_color(0, 0, 0)
        self.ln(5)
        
        # Table configuration
        widths = [60, 30, 50, 15, 25]  # Column widths
        
        # Header row
        self.set_font(self.default_font, 'B', 9)
        self.set_fill_color(240, 240, 240)
        
        headers = ["Risk Factor", "Value", "Rule Applied", "Score", "Risk Level"]
        for width, header in zip(widths, headers):
            self.cell(width, 8, header, border=0, ln=0, align='C', fill=True)
        self.ln(8)
        
        # Data rows
        self.set_font(self.default_font, '', 8)
        for field in sorted(risk_data.keys()):
            details = risk_data[field]
            self._add_risk_row(field, details, widths)
        
        self.ln(8)

    def _add_risk_row(self, field: str, details: Dict[str, Any], widths: List[int]):
        """Add a single row to the risk table"""
        risk_level = details.get('risk_level', '').lower()
        style = self._get_risk_style(risk_level)
        
        self.set_text_color(*style['text_color'])
        self.set_fill_color(*style['fill_color'])
        
        x_start = self.get_x()
        y_start = self.get_y()
        
        # Format field name
        display_name = field.replace('_', ' ').title()
        if field.startswith('udf_'):
            display_name = display_name.replace('Udf ', '')
        
        # Risk Factor
        self.multi_cell(widths[0], 8, display_name, border='LR', align='L', fill=True)
        x = x_start + widths[0]
        self.set_xy(x, y_start)
        
        # Value
        value = str(details.get('value', 'N/A'))
        if field.startswith('udf_') and len(value) > 20:
            self.multi_cell(widths[1], 8, value, border='LR', align='L', fill=True)
            x += widths[1]
            self.set_xy(x, self.get_y() + 8)
        else:
            self.cell(widths[1], 8, value, border='LR', fill=True)
            x += widths[1]
            self.set_xy(x, y_start)
        
        # Rule Applied
        rule = str(details.get('matched_rule', 'N/A'))
        self.multi_cell(widths[2], 8, rule, border='LR', align='L', fill=True)
        x += widths[2]
        self.set_xy(x, y_start)
        
        # Score
        self.cell(widths[3], 8, str(details.get('score', 0)), border='LR', fill=True, align='R')
        x += widths[3]
        self.set_xy(x, y_start)
        
        # Risk Level
        self.cell(widths[4], 8, risk_level.title(), border='LR', fill=True)
        
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def _get_risk_style(self, risk_level: str) -> Dict[str, tuple]:
        """Get style configuration based on risk level"""
        risk_level = risk_level.lower()
        if 'high' in risk_level or 'élevé' in risk_level:
            return self.styles['risk_high']
        elif 'medium' in risk_level or 'moyen' in risk_level:
            return self.styles['risk_medium']
        else:
            return self.styles['risk_low']

    def add_llm_analysis(self, analysis: Dict[str, Any]):
        """Add the complete LLM analysis section"""
        try:
            self.add_section("AI Risk Analysis")
            
            # Summary
            self._add_analysis_part(
                title="Summary",
                content=analysis.get('summary', 'No summary provided'),
                style='normal'
            )
            
            # Recommendation
            self._add_simple_recommendation(analysis.get('recommendation', 'review'))
            
            # Rationale
            self._add_analysis_part(
                title="Detailed Rationale",
                content=analysis.get('rationale', []),
                style='normal',
                bullet_points=True
            )
            
            # Key Findings
            if analysis.get('key_findings'):
                self._add_analysis_part(
                    title="Key Findings",
                    content=analysis['key_findings'],
                    style='normal',
                    bullet_points=True
                )
            
            # Conditions
            if analysis.get('conditions'):
                self._add_analysis_part(
                    title="Recommended Conditions",
                    content=analysis['conditions'],
                    style='normal',
                    bullet_points=True
                )
            
            # Historical context
            if analysis.get('rag_context'):
                self._add_historical_context(analysis['rag_context'])
                
        except Exception as e:
            self._add_error_message(f"Could not render AI analysis: {str(e)}")

    def _add_simple_recommendation(self, recommendation: str):
        """Add recommendation without the box"""
        rec = str(recommendation).upper()
        risk_style = self._get_recommendation_style(rec)
        
        self.ln(8)
        self.set_font(self.default_font, 'B', 12)
        self.set_text_color(*risk_style['text_color'])
        self.cell(0, 8, f"RECOMMENDATION: {rec}", ln=1)
        self.set_text_color(0, 0, 0)
        self.ln(8)

    def _get_recommendation_style(self, recommendation: str) -> Dict:
        """Determine styling based on recommendation type"""
        rec = recommendation.lower()
        if 'reject' in rec or 'deny' in rec:
            return {'text_color': (178, 34, 34)}  # Red
        elif 'approve' in rec:
            return {'text_color': (0, 100, 0)}    # Green
        else:  # Review or other
            return {'text_color': (255, 140, 0)}  # Orange

    def _add_analysis_part(self, title: str, content: Union[str, List],
                         style: str = 'normal', bullet_points: bool = False):
        """Add a consistent analysis section part"""
        style_config = self.styles[style]
        
        # Add title
        self.set_font(self.default_font, 'B', style_config['font_size'])
        self.cell(0, style_config['line_height'], f"{title}:", ln=1)
        self.ln(2)
        
        # Add content
        self.set_font(self.default_font, style_config['font_style'], style_config['font_size'])
        self.set_text_color(*style_config['text_color'])
        
        if isinstance(content, list):
            for item in content:
                if bullet_points:
                    self.cell(5, style_config['line_height'], "-", ln=0)
                self._safe_multi_cell(
                    self.content_width - (5 if bullet_points else 0),
                    style_config['line_height'],
                    str(item)
                )
                self.ln(2)
        else:
            self._safe_multi_cell(self.content_width, style_config['line_height'], str(content))
        
        # Reset text color and add spacing
        self.set_text_color(0, 0, 0)
        self.ln(8)

    def _add_historical_context(self, rag_context: Dict[str, Any]):
        """Add historical cases context"""
        self.add_section("Similar Historical Cases", level=2)
        
        if not rag_context.get('similar_cases'):
            self._add_analysis_part(
                title="Note",
                content="No similar cases found in knowledge base",
                style='small'
            )
            return
            
        for i, case in enumerate(rag_context['similar_cases'], 1):
            # Case header
            self.set_font(self.default_font, 'B', self.styles['case_header']['font_size'])
            self.set_text_color(*self.styles['case_header']['text_color'])
            self.cell(
                0, self.styles['case_header']['line_height'],
                f"Case #{i} (Similarity: {case.get('similarity_score', 0.0):.2f})",
                ln=1
            )
            self.ln(2)
            
            # Case details
            case_data = {
                'Customer': case.get('customer', 'Unknown'),
                'Loan Amount': f"{case.get('amount', 0):,.2f}",
                'Risk Score': case.get('score', 0),
                'Decision': str(case.get('decision', 'N/A')).upper()
            }
            
            if case.get('metadata'):
                for k, v in case['metadata'].items():
                    if k not in case_data:
                        case_data[k] = str(v)
            
            self.add_key_value_table(case_data, col_width=40)
            self.ln(5)

    def _add_error_message(self, message: str):
        """Add an error message with appropriate styling"""
        self.set_font(self.default_font, 'I', 8)
        self.set_text_color(178, 34, 34)
        self.multi_cell(self.content_width, 5, message)
        self.set_text_color(0, 0, 0)
        self.ln(5)

    def generate_report(self, assessment_data: Dict[str, Any], output_path: Union[str, Path] = None) -> Path:
        """Generate complete PDF report with all sections"""
        try:
            self.alias_nb_pages()
            self.add_page()
            
            # Set Unicode font immediately
            self.set_font(self.default_font, '', 10)
            self.header()
            
            # 1. Loan Information
            self.add_section("Loan Information")
            self.add_key_value_table({
                k: str(v) for k, v in assessment_data['loan_info']['basic_info'].items()
                if k != 'branch'
            })
            
            # 2. Customer Profile
            self.add_section("Customer Profile")
            customer_data = {
                'Name': assessment_data['customer_info']['name'],
                'ID': assessment_data['customer_info']['id'],
                'Type': assessment_data['customer_info']['type'],
                **assessment_data['customer_info']['demographics']
            }
            self.add_key_value_table(customer_data)
            
            # 3. Financial Details
            self.add_section("Financial Details")
            financials = assessment_data['loan_info']['financials']
            self.add_key_value_table({
                'Loan Amount': f"{financials['loan_amount']:,.2f} {financials['currency']}",
                'Personal Contribution': f"{financials['personal_contribution']:,.2f} {financials['currency']}",
                'Total Interest': f"{financials['total_interest']:,.2f} {financials['currency']}",
                'Monthly Payment': f"{financials['monthly_payment']:,.2f} {financials['currency']}",
                'Assets Value': f"{financials['assets_total']:,.2f} {financials['currency']}",
                'APR': f"{financials['apr']}%",
                'Interest Rate': f"{financials['interest_rate']}%",
                'Term': f"{financials['term_months']} months"
            })
            
            # 4. Risk Assessment
            self.add_section("Risk Assessment Summary")
            safe_risk_data = {
                k: {sk: str(sv) for sk, sv in v.items()} 
                for k, v in assessment_data['risk_assessment']['indicators'].items()
            }
            self._add_risk_table(safe_risk_data)
            
            # 5. Additional Customer Information (Combined UDF Data)
            self.add_section("Additional Customer Information")
        
            # Combine both scoring and non-scoring UDF data
            all_udf_data = []
        
            # Add non-scoring UDF data
            if assessment_data['customer_info'].get('udf_data'):
                all_udf_data.extend(assessment_data['customer_info']['udf_data'])
        
            # Add scoring UDF data
            if assessment_data['customer_info'].get('scoring_udf_data'):
                all_udf_data.extend(assessment_data['customer_info']['scoring_udf_data'])
        
            # Display all UDF groups
            if all_udf_data:
                for group in all_udf_data:
                    if group.get('udfGroupeFieldsModels'):
                        self.add_section(group['userDefinedFieldGroupName'], level=2)
                        for field in group['udfGroupeFieldsModels']:
                            field_name = self._process_text(field.get('fieldName', 'Unknown Field'))
                            field_value = self._process_text(field.get('value', 'N/A'))
                        
                            self.set_font(self.default_font, 'B', 10)
                            self.cell(60, 6, f"{field_name}:", border=0)
                            self.set_font(self.default_font, '', 10)
                            self.multi_cell(0, 6, str(field_value))
                            self.ln(2)
                        self.ln(5)
            else:
                self._add_analysis_part(
                    title="Note",
                    content="No additional customer information available",
                    style='small'
                )
            
            # 6. AI Analysis
            if 'llm_analysis' in assessment_data:
                safe_analysis = {
                    k: str(v) if isinstance(v, str) else v 
                    for k, v in assessment_data['llm_analysis'].items()
                }
                self.add_llm_analysis(safe_analysis)
            
            # 7. Branch Information
            self.add_section("Branch Information")
            branch = assessment_data['loan_info']['basic_info']['branch']
            self.add_key_value_table({
                'Branch Name': branch['name'],
                'Branch Description': branch['description'],
                'Loan Officer': branch['officer']
            })
            
            # Save PDF
            pdf_dir = Path('PDF Loans')
            pdf_dir.mkdir(exist_ok=True)
            
            loan_id = assessment_data['loan_info']['basic_info'].get('loan_id', 'unknown')
            report_filename = pdf_dir / f"loan_assessment_{loan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            self.output(report_filename)
            
            logger.info(f"Successfully generated PDF report: {report_filename}")
            return report_filename
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {str(e)}")
            raise
import json
import logging
from typing import Dict, List, Optional
from src.utils import Utils

class LLMPromptBuilder:
    @staticmethod
    def build_basic_prompt(loan_data: Dict) -> str:
        """
        Build comprehensive risk assessment prompt with all financial,
        demographic, and risk factor details for thorough analysis.
        """
        try:
            customer_info = loan_data['customer_info']
            financials = loan_data['loan_info']['financials']
            risk_assessment = loan_data['risk_assessment']
            
            # Prepare UDF data
            udf_details = []
            for group in customer_info.get('udf_data', []):
                if group.get('udfGroupeFieldsModels'):
                    udf_details.append(f"\n{group['userDefinedFieldGroupName']}:")
                    for field in group['udfGroupeFieldsModels']:
                        udf_details.append(f"- {field.get('fieldName', 'Unknown')}: {field.get('value', 'N/A')}")
            udf_str = "".join(udf_details) if udf_details else "None"

            # Format risk factors table
            risk_table = ["| Risk Factor | Value | Score | Risk Level |",
                          "|------------|-------|-------|------------|"]
            for field, details in risk_assessment.get('indicators', {}).items():
                risk_table.append(
                    f"| {field.replace('_', ' ').title()} | {details.get('value', 'N/A')} | "
                    f"{details.get('score', 0)} | {details.get('risk_level', 'N/A')} |"
                )
            risk_table_str = "\n".join(risk_table)

            # Build prompt
            prompt = f"""
You are a senior financial risk analyst with 15 years of experience in commercial banking.
Conduct a professional assessment of this loan application, focusing on:

1. Data consistency and red flags
2. Financial capacity and repayment ability
3. Risk factor correlations
4. Profile vs purpose alignment

Respond with VALID JSON only following the exact structure below.

=== APPLICATION DETAILS ===

**Customer Profile:**
- Name: {customer_info.get('name', 'Unknown')}
- Age: {customer_info['demographics'].get('age', 'N/A')}
- Gender: {customer_info['demographics'].get('gender', 'N/A')}
- Marital Status: {customer_info['demographics'].get('marital_status', 'N/A')}

**Financial Details:**
- Loan Amount: {financials.get('loan_amount', 0):,.2f} {financials.get('currency', 'TND')}
- Personal Contribution: {financials.get('personal_contribution', 0):,.2f} {financials.get('currency', 'TND')}
- Monthly Payment: {financials.get('monthly_payment', 0):,.2f} {financials.get('currency', 'TND')}
- Assets Value: {financials.get('assets_total', 0):,.2f} {financials.get('currency', 'TND')}
- APR: {financials.get('apr', 0)}%
- Interest Rate: {financials.get('interest_rate', 0)}%
- Term: {financials.get('term_months', 0)} months

**Risk Assessment:**
Total Score: {risk_assessment.get('total_score', 0)}
{risk_table_str}

**Additional Information:**
{udf_str}

=== REQUIRED ANALYSIS ===

1. **Professional Assessment** (5-7 sentences):
   - Overall risk evaluation
   - Key strengths and weaknesses
   - Financial capacity analysis

2. **Hidden Risks**:
   - Any non-obvious risk factors
   - Potential fraud indicators
   - Overleveraging concerns

3. **Data Mismatches**:
   - Inconsistencies in provided information
   - Conflicts between profile and purpose
   - Unusual patterns in UDF data

=== RESPONSE FORMAT ===
{{
    "summary": "Comprehensive professional assessment covering all key aspects",
    "recommendation": "approve|deny|review",
    "rationale": [
        "Primary reason for recommendation",
        "Supporting evidence from data",
        "Risk/benefit analysis"
    ],
    "key_findings": [
        "Specific finding 1 with impact analysis",
        "Specific finding 2 with impact analysis"
    ],
    "conditions": [
        "Specific condition 1 if approving",
        "Verification needed if reviewing"
    ],
    "data_mismatches": [
        "Notable inconsistency 1 between fields",
        "Notable inconsistency 2 between fields"
    ]
}}
"""
            return prompt

        except Exception as e:
            logging.error(f"Prompt building failed: {str(e)}")
            raise

    @staticmethod 
    def build_contextual_prompt(loan_data: Dict, similar_loans: Dict) -> str:
        """
        Build RAG-enhanced prompt with comparative historical analysis.
        Uses the basic prompt as foundation and adds historical context.
        """
        try:
            # First build the basic prompt
            base_prompt = LLMPromptBuilder.build_basic_prompt(loan_data)
            
            # Prepare historical cases section
            context_cases = []
            for i, doc in enumerate(similar_loans.get('documents', [])[:3], 1):
                try:
                    doc_data = json.loads(doc) if isinstance(doc, str) else doc
                    risk_assessment = doc_data.get('risk_assessment', {})
                    
                    case_info = {
                        'customer': doc_data.get('customer_info', {}).get('name', 'Unknown'),
                        'amount': doc_data.get('loan_info', {}).get('financials', {}).get('loan_amount', 'N/A'),
                        'score': risk_assessment.get('total_score', 'N/A'),
                        'decision': doc_data.get('llm_analysis', {}).get('recommendation', 'N/A'),
                        'top_risks': [
                            f"{k} (Score: {v.get('score', 0)})" 
                            for k, v in risk_assessment.get('indicators', {}).items()
                            if v.get('score', 0) > 10
                        ],
                        'conditions': doc_data.get('llm_analysis', {}).get('conditions', [])
                    }
                    
                    context_cases.append(
                        f"Case {i}:\n"
                        f"- Customer: {case_info['customer']}\n"
                        f"- Amount: {case_info['amount']} ({case_info['decision'].upper()})\n"
                        f"- Risk Score: {case_info['score']}\n"
                        f"- Top Risks: {', '.join(case_info['top_risks']) if case_info['top_risks'] else 'None'}\n"
                        f"- Conditions Applied: {len(case_info['conditions'])}"
                    )
                except Exception as e:
                    logging.warning(f"Couldn't fully process similar loan {i}: {str(e)}")
                    continue

            historical_context = "\n".join(context_cases) if context_cases else "No sufficiently similar historical cases"

            # Add historical context to the base prompt
            contextual_prompt = f"""
{base_prompt}

=== HISTORICAL CONTEXT ===

Consider these similar historical cases in your analysis:
{historical_context}

=== COMPARATIVE ANALYSIS FOCUS ===

1. Significant deviations from historical patterns (>20% difference)
2. Emerging risks not present in historical cases
3. Improved risk factors compared to history
4. Consistency with past decision patterns

=== UPDATED RESPONSE FORMAT ===
Add this field to your JSON response:
{{
    "comparative_analysis": [
        "Key difference 1 with historical context",
        "Key difference 2 with trend analysis"
    ]
}}

Maintain all other fields from the basic analysis format.
"""
            return contextual_prompt

        except Exception as e:
            logging.error(f"Contextual prompt building failed: {str(e)}")
            raise
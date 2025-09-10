from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ReportSection:
    title: str
    fields: List[str]
    field_labels: Dict[str, str]
    transformations: Dict[str, Any]

class ReportTemplates:
    CUSTOMER_SECTION = ReportSection(
        title="Customer Information",
        fields=["name", "id", "type", "demographics"],
        field_labels={
            "name": "Full Name",
            "id": "ID Number",
            "type": "Customer Type"
        },
        transformations={
            "name": lambda x: x.title(),
            "demographics": lambda x: "\n".join(f"{k}: {v}" for k, v in x.items())
        }
    )

    FINANCIAL_SECTION = ReportSection(
        title="Financial Details",
        fields=["loan_amount", "personal_contribution", "monthly_payment"],
        field_labels={
            "loan_amount": "Loan Amount",
            "personal_contribution": "Customer Contribution",
            "monthly_payment": "Monthly Payment"
        },
        transformations={
            "loan_amount": lambda x: f"{x:,.2f}",
            "monthly_payment": lambda x: f"{x:,.2f}"
        }
    )

    @staticmethod
    def get_section_template(section_name: str) -> ReportSection:
        return getattr(ReportTemplates, f"{section_name}_SECTION")
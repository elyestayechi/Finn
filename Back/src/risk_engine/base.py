from datetime import datetime
from typing import Dict, Any, Tuple, List, Union, Optional
from ..data_models import RiskIndicator, CustomerInfo, LoanFinancials, LoanBasicInfo, UDFGroup, UDFField
from ..config import RISK_THRESHOLDS
import logging

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self, rules: Dict[str, Dict[str, float]]):
        """Initialize the risk engine with scoring rules"""
        self.rules = rules
        self.valid_customer_types = ['SA', 'SUARL', 'SARL', 'ONG', 'Société Personne Physique']
        
        # Field mappings for standard fields
        self.field_mappings = {
            'customerType': 'Forme Juridique du B.EFFECTIF',
            'loanPurpose': 'Raison de financement',
            'gender': 'Genre',
            'maritalStatus': 'Situation familiale',
            'region': 'Région',
            'product': 'Produit',
            'industryCode': 'Secteur d\'activité'
        }
        
        # Field mappings for UDF fields
        self.udf_field_mappings = {
            'Type d\'activité': 'Type d\'activité',
            'Niveau d\'étude': 'Niveau d\'étude',
            'Type Logement': 'Type de logement',
            'Couverture sociale': 'Couverture sociale',
            'Patenté': 'Patenté',
            'Résident': 'Résident',
            'Forme juridique': 'Forme Juridique du B.EFFECTIF',
            'Appréciation du niveau de vie': 'Niveau de vie'
        }
        
        self._build_normalization_maps()
        self._build_udf_normalization_maps()

    def _build_normalization_maps(self):
        """Initialize normalization maps for standard fields"""
        self.marital_status_map = {
            'célibataire': ['célibataire', 'celibataire', 'single', 's', 'S'],
            'divorcé': ['divorcé', 'divorce', 'divorced', 'd', 'D'],
            'marié': ['marié', 'married', 'm', 'M'],
            'veuf': ['veuf', 'widow', 'widowed', 'v', 'V']
        }
        
        self.risk_levels = {
            'non risqué': (0, 0),
            'risque faible': (0.1, 10),
            'risque moyen': (10.1, 25),
            'risque élevé': (25.1, 50),
            'risque très élevé': (50.1, float('inf'))
        }

    def _build_udf_normalization_maps(self):
        """Initialize normalization maps for UDF fields"""
        self.udf_value_maps = {
            'Niveau d\'étude': {
                'Analphabète': ['analphabète', 'analphabet', 'illiterate'],
                'Primaire': ['primaire', 'primary'],
                'Secondaire': ['secondaire', 'secondary'],
                'Supérieur': ['supérieur', 'higher', 'university']
            },
            'Type Logement': {
                'Propriétaire': ['propriétaire', 'owner'],
                'Locataire': ['locataire', 'tenant'],
                'Logé gratuitement': ['logé gratuitement', 'free housing']
            }
        }

    def _normalize_value(self, field: str, value: str) -> Tuple[str, bool]:
        """Normalize field values for consistent matching"""
        if not value:
            return (value, False)
        
        value = str(value).strip().lower()
        
        if field == 'maritalStatus':
            for norm_status, variants in self.marital_status_map.items():
                if value in variants:
                    return (norm_status, True)
            return (value, False)
        
        elif field == 'customerType':
            is_valid = value.upper() in [ct.upper() for ct in self.valid_customer_types]
            return (value if is_valid else "Autres", is_valid)
        
        return (value, False)

    def _normalize_udf_value(self, field_name: str, value: str) -> str:
        """Normalize UDF field values for consistent matching"""
        if not value:
            return value
        
        value = str(value).strip().lower()
        
        if field_name in self.udf_value_maps:
            for normalized, variants in self.udf_value_maps[field_name].items():
                if any(variant.lower() in value for variant in variants):
                    return normalized
                
        return value

    def evaluate(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate loan risk with both standard and UDF fields"""
        try:
            customer_data = loan_data.get('customerDTO', {})
            consolidated_info = self._consolidate_customer_info(customer_data)
            consolidated_info['udf_data'] = loan_data.get('udf_data', [])
            
            # Evaluate standard fields
            evaluation_fields = {
                'customerType': consolidated_info['type'],
                'loanPurpose': loan_data.get('loanReasonCode'),
                'gender': consolidated_info['demographics']['gender'],
                'maritalStatus': consolidated_info['demographics']['marital_status'],
                'region': self._extract_region(
                    branch_desc=loan_data.get('branchDescription', ''),
                    customer_address=consolidated_info.get('address', '')
                ),
                'product': loan_data.get('productCode'),
                'industryCode': loan_data.get('industryCode')
            }
            
            indicators = {}
            total_risk = 0.0
            
            # Evaluate standard fields
            for field, value in evaluation_fields.items():
                normalized_value, is_valid = self._normalize_value(field, value)
                rule_category = self.field_mappings.get(field, field)
                
                if field == 'customerType':
                    if not is_valid:
                        total_risk += 5.0
                        indicators[field] = self._create_indicator(value, "Autres (Not in valid list)", 5.0)
                    else:
                        indicators[field] = self._create_indicator(value, value, 0.0)
                    continue
                
                if rule_category not in self.rules:
                    indicators[field] = self._create_indicator(value, "No rule category", 0.0)
                    continue
                
                matched_rule, score = self._find_matching_rule(rule_category, normalized_value)
                total_risk += score
                indicators[field] = self._create_indicator(value, matched_rule, score)
            
            # Evaluate UDF fields and separate scoring vs non-scoring fields
            scoring_udfs = []
            non_scoring_udfs = []
            
            for group in consolidated_info['udf_data']:
                new_group = {
                    'userDefinedFieldGroupName': group['userDefinedFieldGroupName'],
                    'udfGroupeFieldsModels': []
                }
                
                for field in group.get('udfGroupeFieldsModels', []):
                    field_name = field.get('fieldName')
                    field_value = field.get('value')
                    
                    if field_name in self.udf_field_mappings:
                        rule_category = self.udf_field_mappings[field_name]
                        normalized_value = self._normalize_udf_value(field_name, field_value)
                        
                        if rule_category in self.rules:
                            matched_rule, score = self._find_matching_rule(rule_category, normalized_value)
                            if matched_rule != "No matching rule":
                                key = f"udf_{field_name.replace(' ', '_').lower()}"
                                indicators[key] = self._create_indicator(
                                    field_value,
                                    matched_rule,
                                    score
                                )
                                total_risk += score
                                # Add to scoring UDFs
                                new_group['udfGroupeFieldsModels'].append(field)
                                continue
                    
                    # Add to non-scoring UDFs
                    new_group['udfGroupeFieldsModels'].append(field)
                
                if new_group['udfGroupeFieldsModels']:
                    if any(field.get('fieldName') in self.udf_field_mappings for field in new_group['udfGroupeFieldsModels']):
                        scoring_udfs.append(new_group)
                    else:
                        non_scoring_udfs.append(new_group)
            
            # Evaluate AML checks
            for aml_check in consolidated_info['aml_checks']:
                key = f"aml_{aml_check.get('listName', '').lower()}"
                aml_score = float(aml_check.get('score', 0))
                indicators[key] = self._create_aml_indicator(aml_check)
            
            return {
                'customer_info': {
                    **consolidated_info,
                    'udf_data': non_scoring_udfs,  # Only non-scoring UDFs go here
                    'scoring_udf_data': scoring_udfs  # Scoring UDFs kept separate
                },
                'loan_info': self._extract_loan_info(loan_data),
                'risk_assessment': {
                    'indicators': indicators,
                    'total_score': total_risk,
                    'risk_level': self._determine_overall_risk(total_risk)
                }
            }
        except Exception as e:
            logger.error(f"Risk evaluation failed: {str(e)}")
            raise

    def _create_indicator(self, value: Any, rule: str, score: float) -> RiskIndicator:
        """Create a standardized risk indicator"""
        return {
            'value': value,
            'matched_rule': rule,
            'score': score,
            'risk_level': self._get_risk_level(score)
        }

    def _create_aml_indicator(self, aml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create AML risk indicator"""
        score = float(aml_data.get('score', 0))
        return {
            'value': aml_data.get('amlStatus', 'N/A'),
            'matched_rule': aml_data.get('listName', 'N/A'),
            'score': score,
            'risk_level': self._get_aml_risk_level(score)
        }

    def _find_matching_rule(self, category: str, value: str) -> Tuple[str, float]:
        """Find the best matching rule for a given value"""
        if category not in self.rules:
            return ("No matching category", 0.0)
        
        str_value = str(value).lower()
        for rule, score in self.rules[category].items():
            if rule.lower() in str_value:
                return (rule, float(score))
        
        return ("No matching rule", 0.0)

    def _extract_region(self, branch_desc: str, customer_address: str) -> str:
        """Extract region from branch description or customer address"""
        regions = self.rules.get('Région', {}).keys()
        
        # First try branch description
        if branch_desc:
            for region in regions:
                if region.lower() in branch_desc.lower():
                    return region
        
        # Then try customer address
        if customer_address:
            for region in regions:
                if region.lower() in customer_address.lower():
                    return region
        
        return "Unknown"

    def _extract_loan_info(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure loan information"""
        assets_total = sum(
            asset.get('prixUnitaire', 0) * asset.get('quantiteArticle', 0)
            for asset in loan_data.get('loanAssetsDtos', [])
        )
        
        return {
            'basic_info': {
                'loan_id': loan_data.get('loanId'),
                'external_id': loan_data.get('idLoanExtern'),
                'account': loan_data.get('accountNumber'),
                'status': loan_data.get('statutLibelle'),
                'product': f"{loan_data.get('productCode')} - {loan_data.get('productDescription')}",
                'branch': {
                    'name': loan_data.get('branchName'),
                    'description': loan_data.get('branchDescription'),
                    'officer': loan_data.get('ownerName')
                }
            },
            'financials': {
                'loan_amount': float(loan_data.get('approvelAmount', 0)),
                'personal_contribution': float(loan_data.get('personalContribution', 0)),
                'total_interest': float(loan_data.get('totalInterest', 0)),
                'monthly_payment': float(loan_data.get('normalPayment', 0)),
                'assets_total': float(assets_total),
                'apr': float(loan_data.get('apr', 0)),
                'interest_rate': float(loan_data.get('productRate', 0)),
                'term_months': int(loan_data.get('termPeriodNum', 0)),
                'currency': loan_data.get('currencySymbol', 'TND')
            }
        }

    def _get_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level"""
        for level, (min_score, max_score) in self.risk_levels.items():
            if min_score <= score <= max_score:
                return level
        return "non risqué"

    def _get_aml_risk_level(self, score: float) -> str:
        """Determine AML risk level"""
        if score == 0:
            return "safe"
        elif score <= 20:
            return "low risk"
        elif score <= 50:
            return "medium risk"
        else:
            return "high risk"

    def _determine_overall_risk(self, total_score: float) -> str:
        """Determine the overall risk level"""
        return self._get_risk_level(total_score)

    def _consolidate_customer_info(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and structure customer information"""
        return {
            'name': customer_data.get('customerName', '').replace('|||', ' '),
            'id': customer_data.get('id', 'N/A'),
            'type': customer_data.get('customerType', 'N/A'),
            'address': customer_data.get('customerAddress', 'N/A'),
            'demographics': {
                'gender': customer_data.get('gender', 'N/A'),
                'marital_status': customer_data.get('maritalStatus', 'N/A'),
                'age': customer_data.get('age', 'N/A'),
                'birth_date': self._format_date(customer_data.get('dateOfBirth')),
                'phone': customer_data.get('telephone', 'N/A')
            },
            'aml_checks': customer_data.get('acmAmlChecksDTOs', []),
            'udf_data': customer_data.get('udf_data', [])
        }

    def _format_date(self, date_str: str) -> str:
        """Format date string consistently"""
        if not date_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return date_str
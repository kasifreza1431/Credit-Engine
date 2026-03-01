
# credit_engine_rules.py
# Skeleton Python structures for a Sharia-compliant, product-agnostic credit rules engine

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


class ProductType(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    PERSONAL_FINANCE = "PERSONAL_FINANCE"
    HOME_FINANCE = "HOME_FINANCE"
    AUTO_FINANCE = "AUTO_FINANCE"
    BNPL = "BNPL"
    OVERDRAFT = "OVERDRAFT"


@dataclass
class Applicant:
    customer_id: str
    age: int
    nationality: str
    residence_country: str
    employment_status: str
    employer_category: str
    monthly_income: float
    variable_income: float
    other_income: float
    dependents_count: int
    segment: str
    risk_profile: str
    is_existing_customer: bool
    relationship_tenure_months: int
    behaviour_score: Optional[float]
    external_bureau_score: Optional[float]
    bureau_enquiries_6m: int
    bureau_enquiries_12m: int
    internal_delinquency_last_12m: int
    external_delinquency_last_12m: int
    current_obligations_monthly: float
    current_obligations_total: float
    existing_limits_total: float
    existing_utilisation_ratio: float
    pledged_deposits: float
    collateral_value: float
    collateral_type: Optional[str]
    sharia_segment: str
    industry_of_employer: str
    pep_flag: bool
    sanctions_flag: bool
    negative_news_flag: bool
    blacklist_flag: bool


@dataclass
class Application:
    product_type: ProductType
    requested_limit: float
    requested_tenor_months: int
    pricing_plan: str
    purpose: str
    channel: str
    is_top_up: bool
    is_limit_increase: bool
    restructuring_flag: bool
    refinancing_flag: bool
    currency: str


@dataclass
class RuleResult:
    rule_id: str
    passed: bool
    severity: str  # "HARD" or "SOFT"
    message: str


class CreditRulesEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    # 1. Sharia compliance rules

    def rule_prohibited_industries(self, applicant: Applicant, application: Application) -> RuleResult:
        prohibited = set(self.config.get("sharia_prohibited_industries", []))
        passed = applicant.industry_of_employer not in prohibited
        return RuleResult(
            rule_id="SHARIA_PROHIBITED_INDUSTRIES",
            passed=passed,
            severity="HARD",
            message="Employer industry is prohibited under Sharia" if not passed else "OK",
        )

    def rule_prohibited_purpose(self, applicant: Applicant, application: Application) -> RuleResult:
        prohibited = set(self.config.get("sharia_prohibited_purposes", []))
        passed = application.purpose not in prohibited
        return RuleResult(
            rule_id="SHARIA_PROHIBITED_PURPOSE",
            passed=passed,
            severity="HARD",
            message="Requested financing purpose is prohibited under Sharia" if not passed else "OK",
        )

    def rule_riba_structure_flag(self, applicant: Applicant, application: Application) -> RuleResult:
        # This rule is a placeholder to ensure the selected product/pricing plan
        # is mapped to an approved Islamic contract (e.g. Murabaha, Ijara, Tawarruq, Ujrah)
        allowed_contracts = set(self.config.get("product_allowed_contracts", {}).get(application.product_type.value, []))
        selected_contract = self.config.get("application_selected_contract")
        passed = selected_contract in allowed_contracts
        return RuleResult(
            rule_id="SHARIA_APPROVED_CONTRACT",
            passed=passed,
            severity="HARD",
            message="Selected contract not approved by Sharia board for this product" if not passed else "OK",
        )

    # 2. KYC, AML, sanctions & fraud rules

    def rule_age_minimum(self, applicant: Applicant, application: Application) -> RuleResult:
        min_age = self.config.get("min_age", 18)
        passed = applicant.age >= min_age
        return RuleResult(
            rule_id="AGE_MINIMUM",
            passed=passed,
            severity="HARD",
            message=f"Applicant age below minimum {min_age}" if not passed else "OK",
        )

    def rule_blacklist(self, applicant: Applicant, application: Application) -> RuleResult:
        passed = not applicant.blacklist_flag
        return RuleResult(
            rule_id="BLACKLIST_CHECK",
            passed=passed,
            severity="HARD",
            message="Applicant on internal blacklist" if not passed else "OK",
        )

    def rule_sanctions_pep(self, applicant: Applicant, application: Application) -> RuleResult:
        passed = not applicant.sanctions_flag
        severity = "HARD" if applicant.sanctions_flag else "SOFT" if applicant.pep_flag else "SOFT"
        msg = "Applicant on sanctions list" if applicant.sanctions_flag else "Applicant is PEP" if applicant.pep_flag else "OK"
        return RuleResult(
            rule_id="SANCTIONS_PEP_CHECK",
            passed=passed,
            severity=severity,
            message=msg,
        )

    def rule_negative_news(self, applicant: Applicant, application: Application) -> RuleResult:
        passed = not applicant.negative_news_flag
        severity = "SOFT"
        msg = "Negative news present for applicant" if not passed else "OK"
        return RuleResult(
            rule_id="NEGATIVE_NEWS_CHECK",
            passed=passed,
            severity=severity,
            message=msg,
        )

    # 3. Income & employment rules

    def rule_min_income(self, applicant: Applicant, application: Application) -> RuleResult:
        product_min_income = self.config.get("product_min_income", {}).get(application.product_type.value, 0)
        passed = applicant.monthly_income >= product_min_income
        return RuleResult(
            rule_id="MIN_INCOME_PRODUCT",
            passed=passed,
            severity="HARD",
            message=f"Monthly income below product minimum {product_min_income}" if not passed else "OK",
        )

    def rule_employment_status_allowed(self, applicant: Applicant, application: Application) -> RuleResult:
        allowed_statuses = set(self.config.get("allowed_employment_statuses", []))
        passed = applicant.employment_status in allowed_statuses
        return RuleResult(
            rule_id="EMPLOYMENT_STATUS_ALLOWED",
            passed=passed,
            severity="HARD",
            message="Employment status not eligible" if not passed else "OK",
        )

    def rule_employer_category(self, applicant: Applicant, application: Application) -> RuleResult:
        high_risk_categories = set(self.config.get("high_risk_employer_categories", []))
        passed = applicant.employer_category not in high_risk_categories
        severity = "SOFT" if not passed else "SOFT"
        msg = "Employer in high-risk category" if not passed else "OK"
        return RuleResult(
            rule_id="EMPLOYER_CATEGORY_RISK",
            passed=passed,
            severity=severity,
            message=msg,
        )

    # 4. Affordability & debt-burden rules

    def rule_tdsr_limit(self, applicant: Applicant, application: Application) -> RuleResult:
        max_tdsr = self.config.get("max_tdsr", 0.5)
        # expected_installment should be set externally for the application
        expected_installment = self.config.get("expected_installment", 0.0)
        total_monthly_obligations = applicant.current_obligations_monthly + expected_installment
        income_for_tdsr = applicant.monthly_income + applicant.variable_income + applicant.other_income
        actual_tdsr = total_monthly_obligations / income_for_tdsr if income_for_tdsr > 0 else 1.0
        passed = actual_tdsr <= max_tdsr
        return RuleResult(
            rule_id="TDSR_LIMIT",
            passed=passed,
            severity="HARD",
            message=f"TDSR {actual_tdsr:.2f} exceeds max {max_tdsr}" if not passed else "OK",
        )

    def rule_min_surplus_income(self, applicant: Applicant, application: Application) -> RuleResult:
        min_surplus = self.config.get("min_surplus_income", 0.0)
        expected_installment = self.config.get("expected_installment", 0.0)
        total_monthly_obligations = applicant.current_obligations_monthly + expected_installment
        income_for_tdsr = applicant.monthly_income + applicant.variable_income + applicant.other_income
        surplus = income_for_tdsr - total_monthly_obligations
        passed = surplus >= min_surplus
        return RuleResult(
            rule_id="MIN_SURPLUS_INCOME",
            passed=passed,
            severity="HARD",
            message=f"Surplus income {surplus:.2f} below minimum {min_surplus}" if not passed else "OK",
        )

    # 5. Bureau & behaviour score rules

    def rule_min_bureau_score(self, applicant: Applicant, application: Application) -> RuleResult:
        min_score = self.config.get("min_bureau_score", {}).get(application.product_type.value, None)
        if min_score is None or applicant.external_bureau_score is None:
            return RuleResult("MIN_BUREAU_SCORE", True, "SOFT", "Not applicable")
        passed = applicant.external_bureau_score >= min_score
        return RuleResult(
            rule_id="MIN_BUREAU_SCORE",
            passed=passed,
            severity="HARD",
            message=f"Bureau score {applicant.external_bureau_score} below minimum {min_score}" if not passed else "OK",
        )

    def rule_enquiry_burden(self, applicant: Applicant, application: Application) -> RuleResult:
        max_enquiries_6m = self.config.get("max_bureau_enquiries_6m", 10)
        passed = applicant.bureau_enquiries_6m <= max_enquiries_6m
        return RuleResult(
            rule_id="ENQUIRY_BURDEN_6M",
            passed=passed,
            severity="SOFT",
            message=f"High number of bureau enquiries in last 6 months: {applicant.bureau_enquiries_6m}" if not passed else "OK",
        )

    def rule_delinquency_history(self, applicant: Applicant, application: Application) -> RuleResult:
        max_internal = self.config.get("max_internal_delinquency_last_12m", 0)
        max_external = self.config.get("max_external_delinquency_last_12m", 0)
        passed = (
            applicant.internal_delinquency_last_12m <= max_internal and
            applicant.external_delinquency_last_12m <= max_external
        )
        return RuleResult(
            rule_id="DELINQUENCY_HISTORY_12M",
            passed=passed,
            severity="HARD",
            message="Delinquency history exceeds policy limits" if not passed else "OK",
        )

    # 6. Product-specific policy rules (examples)

    def rule_home_finance_ltv(self, applicant: Applicant, application: Application) -> RuleResult:
        if application.product_type != ProductType.HOME_FINANCE:
            return RuleResult("HOME_LTV", True, "SOFT", "Not applicable")
        max_ltv = self.config.get("home_max_ltv", 0.85)
        property_value = self.config.get("property_value", 0.0)
        finance_amount = application.requested_limit
        ltv = finance_amount / property_value if property_value > 0 else 1.0
        passed = ltv <= max_ltv
        return RuleResult(
            rule_id="HOME_LTV",
            passed=passed,
            severity="HARD",
            message=f"Home finance LTV {ltv:.2f} exceeds max {max_ltv}" if not passed else "OK",
        )

    def rule_auto_finance_ltv(self, applicant: Applicant, application: Application) -> RuleResult:
        if application.product_type != ProductType.AUTO_FINANCE:
            return RuleResult("AUTO_LTV", True, "SOFT", "Not applicable")
        max_ltv = self.config.get("auto_max_ltv", 0.9)
        vehicle_value = self.config.get("vehicle_value", 0.0)
        finance_amount = application.requested_limit
        ltv = finance_amount / vehicle_value if vehicle_value > 0 else 1.0
        passed = ltv <= max_ltv
        return RuleResult(
            rule_id="AUTO_LTV",
            passed=passed,
            severity="HARD",
            message=f"Auto finance LTV {ltv:.2f} exceeds max {max_ltv}" if not passed else "OK",
        )

    def rule_credit_card_max_limit_vs_income(self, applicant: Applicant, application: Application) -> RuleResult:
        if application.product_type != ProductType.CREDIT_CARD:
            return RuleResult("CARD_LIMIT_VS_INCOME", True, "SOFT", "Not applicable")
        max_multiple = self.config.get("card_limit_income_multiple", 2.0)
        max_limit = applicant.monthly_income * max_multiple
        passed = application.requested_limit <= max_limit
        return RuleResult(
            rule_id="CARD_LIMIT_VS_INCOME",
            passed=passed,
            severity="HARD",
            message=f"Requested card limit above {max_multiple}x income" if not passed else "OK",
        )

    def rule_bnpl_ticket_size(self, applicant: Applicant, application: Application) -> RuleResult:
        if application.product_type != ProductType.BNPL:
            return RuleResult("BNPL_TICKET_SIZE", True, "SOFT", "Not applicable")
        max_ticket = self.config.get("bnpl_max_ticket_size", 0.0)
        passed = application.requested_limit <= max_ticket
        return RuleResult(
            rule_id="BNPL_TICKET_SIZE",
            passed=passed,
            severity="HARD",
            message="BNPL requested amount exceeds max ticket size" if not passed else "OK",
        )

    # 7. Collateral & security rules

    def rule_collateral_coverage(self, applicant: Applicant, application: Application) -> RuleResult:
        required_coverage = self.config.get("required_collateral_coverage", {}).get(application.product_type.value, 0.0)
        if required_coverage == 0.0:
            return RuleResult("COLLATERAL_COVERAGE", True, "SOFT", "Not applicable")
        coverage = applicant.collateral_value / application.requested_limit if application.requested_limit > 0 else 0.0
        passed = coverage >= required_coverage
        return RuleResult(
            rule_id="COLLATERAL_COVERAGE",
            passed=passed,
            severity="HARD",
            message=f"Collateral coverage {coverage:.2f} below required {required_coverage}" if not passed else "OK",
        )

    # 8. Relationship & behavioural rules

    def rule_min_relationship_tenure(self, applicant: Applicant, application: Application) -> RuleResult:
        if not applicant.is_existing_customer:
            return RuleResult("RELATIONSHIP_TENURE", True, "SOFT", "Not applicable")
        min_tenure = self.config.get("min_relationship_tenure_months", 0)
        passed = applicant.relationship_tenure_months >= min_tenure
        return RuleResult(
            rule_id="RELATIONSHIP_TENURE",
            passed=passed,
            severity="SOFT",
            message=f"Relationship tenure below {min_tenure} months" if not passed else "OK",
        )

    def rule_behaviour_score(self, applicant: Applicant, application: Application) -> RuleResult:
        min_behaviour_score = self.config.get("min_behaviour_score", None)
        if not applicant.is_existing_customer or min_behaviour_score is None or applicant.behaviour_score is None:
            return RuleResult("BEHAVIOUR_SCORE", True, "SOFT", "Not applicable")
        passed = applicant.behaviour_score >= min_behaviour_score
        return RuleResult(
            rule_id="BEHAVIOUR_SCORE",
            passed=passed,
            severity="SOFT",
            message=f"Behaviour score {applicant.behaviour_score} below minimum {min_behaviour_score}" if not passed else "OK",
        )

    # 9. Operational & exposure limits

    def rule_max_exposure_per_customer(self, applicant: Applicant, application: Application) -> RuleResult:
        max_exposure = self.config.get("max_exposure_per_customer", float("inf"))
        projected_exposure = applicant.existing_limits_total + application.requested_limit
        passed = projected_exposure <= max_exposure
        return RuleResult(
            rule_id="MAX_EXPOSURE_PER_CUSTOMER",
            passed=passed,
            severity="HARD",
            message="Exposure per customer exceeds bank limit" if not passed else "OK",
        )

    def rule_max_obligation_vs_income(self, applicant: Applicant, application: Application) -> RuleResult:
        max_obligation_ratio = self.config.get("max_obligation_vs_income", 1.0)
        projected_obligations = applicant.current_obligations_total + application.requested_limit
        income_for_ratio = (applicant.monthly_income + applicant.variable_income + applicant.other_income) * 12
        ratio = projected_obligations / income_for_ratio if income_for_ratio > 0 else 1.0
        passed = ratio <= max_obligation_ratio
        return RuleResult(
            rule_id="MAX_OBLIGATION_VS_INCOME",
            passed=passed,
            severity="HARD",
            message=f"Total obligations to income ratio {ratio:.2f} exceeds {max_obligation_ratio}" if not passed else "OK",
        )

    # 10. Aggregator

    def evaluate_all(self, applicant: Applicant, application: Application) -> List[RuleResult]:
        rules = [
            self.rule_prohibited_industries,
            self.rule_prohibited_purpose,
            self.rule_riba_structure_flag,
            self.rule_age_minimum,
            self.rule_blacklist,
            self.rule_sanctions_pep,
            self.rule_negative_news,
            self.rule_min_income,
            self.rule_employment_status_allowed,
            self.rule_employer_category,
            self.rule_tdsr_limit,
            self.rule_min_surplus_income,
            self.rule_min_bureau_score,
            self.rule_enquiry_burden,
            self.rule_delinquency_history,
            self.rule_home_finance_ltv,
            self.rule_auto_finance_ltv,
            self.rule_credit_card_max_limit_vs_income,
            self.rule_bnpl_ticket_size,
            self.rule_collateral_coverage,
            self.rule_min_relationship_tenure,
            self.rule_behaviour_score,
            self.rule_max_exposure_per_customer,
            self.rule_max_obligation_vs_income,
        ]
        return [r(applicant, application) for r in rules]

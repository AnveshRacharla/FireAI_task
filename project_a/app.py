import sys
from pathlib import Path
from decimal import Decimal

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from project_a.schemas.taxpayer import TaxpayerInput
from project_a.tax_engine.calculator import compare_regimes
from project_a.implementations.compiled_rules import calculate_compiled_regime_tax
from project_a.parser.parser import parse_taxpayer_description
from project_a.implementations.llm_based import ask_gemini


st.set_page_config(
    page_title="Indian Income Tax Engine",
    page_icon="🧾",
    layout="wide",
)

st.title("Indian Income Tax Engine")
st.caption("Rules vs LLMs | FY 2024–25 and FY 2025–26")


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def display_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, dict):
        return {k: display_value(v) for k, v in value.items()}

    if isinstance(value, list):
        return [display_value(v) for v in value]

    return value


def show_tax_result(result):
    old = result["old_regime"]
    new = result["new_regime"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Old Regime Tax",
        f"₹{old['total_tax']:,.0f}"
    )

    col2.metric(
        "New Regime Tax",
        f"₹{new['total_tax']:,.0f}"
    )

    col3.metric(
        "Recommended Regime",
        result["recommended_regime"].upper()
    )

    st.subheader("Detailed Tax Calculation")

    left, right = st.columns(2)

    with left:
        st.markdown("### Old Regime")
        st.json(display_value(old))

    with right:
        st.markdown("### New Regime")
        st.json(display_value(new))


def taxpayer_from_details(details):
    """Convert extracted details into TaxpayerInput."""

    if not isinstance(details, dict):
        raise ValueError("Invalid taxpayer details.")

    # Only salary and age are mandatory.
    salary = details.get("annual_gross_salary")
    age = details.get("age")

    if salary is None or age is None:
        missing = []

        if salary is None:
            missing.append("annual salary")

        if age is None:
            missing.append("age")

        raise ValueError(
            "Missing required information: " + ", ".join(missing)
        )

    # Indian residency is fixed.
    # Optional values default to zero.
    taxpayer = TaxpayerInput(
        financial_year=details.get("financial_year", "2024-25"),
        annual_gross_salary=salary,
        age=age,
        is_resident=True,

        basic_salary=details.get("basic_salary") or 0,
        dearness_allowance=details.get("dearness_allowance") or 0,

        hra_received=details.get("hra_received") or 0,
        annual_rent_paid=details.get("annual_rent_paid") or 0,
        is_metro_city=details.get("is_metro_city") or False,

        section_80c_investment=details.get(
            "section_80c_investment", 0
        ) or 0,

        section_80ccd_1b=details.get(
            "section_80ccd_1b", 0
        ) or 0,

        health_insurance_self_family=details.get(
            "health_insurance_self_family", 0
        ) or 0,

        health_insurance_parents=details.get(
            "health_insurance_parents", 0
        ) or 0,

        self_family_has_senior=details.get(
            "self_family_has_senior", False
        ) or False,

        parents_are_senior_citizens=details.get(
            "parents_are_senior_citizens", False
        ) or False,

        home_loan_interest=details.get(
            "home_loan_interest", 0
        ) or 0,

        qualifies_for_higher_24b_limit=details.get(
            "qualifies_for_higher_24b_limit", False
        ) or False,
    )

    return taxpayer


def calculate_and_display(details, source):
    try:
        taxpayer = taxpayer_from_details(details)

        result = compare_regimes(taxpayer)

        st.success(
            f"{source}: Tax calculated successfully using Python."
        )

        show_tax_result(result)

        with st.expander("Taxpayer details used"):
            st.json(display_value(taxpayer.model_dump()))

        return taxpayer

    except Exception as error:
        st.error(f"Tax calculation failed: {error}")
        return None


# --------------------------------------------------
# TABS
# --------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Tax Calculator",
    "Natural Language Parser",
    "Gemini LLM",
    "Method Comparison",
])


# ==================================================
# TAB 1: TAX CALCULATOR
# ==================================================

with tab1:

    st.header("Calculate Income Tax")

    with st.form("tax_form"):

        financial_year = st.selectbox(
            "Financial Year",
            ["2024-25", "2025-26"]
        )

        col1, col2 = st.columns(2)

        with col1:

            salary = st.number_input(
                "Annual Gross Salary (₹)",
                min_value=1,
                value=1200000,
                step=50000
            )

            age = st.number_input(
                "Age",
                min_value=1,
                max_value=120,
                value=25
            )

            resident = st.selectbox(
                "Residential Status",
                ["Resident", "Non-Resident"]
            )

            basic_salary = st.number_input(
                "Basic Salary (₹)",
                min_value=0,
                value=0
            )

            da = st.number_input(
                "Dearness Allowance (₹)",
                min_value=0,
                value=0
            )

            hra = st.number_input(
                "HRA Received (₹)",
                min_value=0,
                value=0
            )

            rent = st.number_input(
                "Annual Rent Paid (₹)",
                min_value=0,
                value=0
            )

            metro = st.checkbox("Metro City")

        with col2:

            investment_80c = st.number_input(
                "Section 80C Investment (₹)",
                min_value=0,
                value=0
            )

            investment_80ccd = st.number_input(
                "Section 80CCD(1B) Investment (₹)",
                min_value=0,
                value=0
            )

            insurance_self = st.number_input(
                "Health Insurance - Self/Family (₹)",
                min_value=0,
                value=0
            )

            insurance_parents = st.number_input(
                "Health Insurance - Parents (₹)",
                min_value=0,
                value=0
            )

            self_senior = st.checkbox(
                "Self/Family has senior citizen"
            )

            parents_senior = st.checkbox(
                "Parents are senior citizens"
            )

            home_interest = st.number_input(
                "Home Loan Interest (₹)",
                min_value=0,
                value=0
            )

            higher_24b = st.checkbox(
                "Qualifies for higher Section 24(b) limit"
            )

        submitted = st.form_submit_button(
            "Calculate Tax",
            type="primary"
        )

    if submitted:

        try:

            taxpayer = TaxpayerInput(
                financial_year=financial_year,
                annual_gross_salary=salary,
                age=age,
                is_resident=(resident == "Resident"),

                basic_salary=basic_salary,
                dearness_allowance=da,

                hra_received=hra,
                annual_rent_paid=rent,
                is_metro_city=metro,

                section_80c_investment=investment_80c,
                section_80ccd_1b=investment_80ccd,

                health_insurance_self_family=insurance_self,
                health_insurance_parents=insurance_parents,

                self_family_has_senior=self_senior,
                parents_are_senior_citizens=parents_senior,

                home_loan_interest=home_interest,
                qualifies_for_higher_24b_limit=higher_24b,
            )

            result = compare_regimes(taxpayer)

            st.success("Tax calculated successfully!")

            show_tax_result(result)

            st.session_state["taxpayer"] = taxpayer

        except Exception as error:
            st.error(f"Calculation error: {error}")


# ==================================================
# TAB 2: NATURAL LANGUAGE PARSER
# ==================================================

with tab2:

    st.header("Natural Language Tax Calculator")

    description = st.text_area(
        "Describe your salary and age",

        placeholder=(
            "I earn 12 lakh annually. "
            "I am 25 years old."
        ),

        height=120,
        key="nlp_description"
    )

    if st.button(
        "Parse Input and Calculate Tax",
        key="parse_and_calculate"
    ):

        if not description.strip():

            st.warning("Enter a description first.")

        else:

            try:

                parsed = parse_taxpayer_description(description)

                st.subheader("NLP Parser Output")
                st.json(parsed)

                if parsed.get("contradictions"):

                    st.error(
                        "Contradictions detected. "
                        "Please correct your description."
                    )

                    for item in parsed["contradictions"]:
                        st.write("•", item)

                elif parsed.get("status") != "complete":

                    st.warning("Required information is missing.")

                    for question in parsed.get(
                        "clarification_questions", []
                    ):
                        st.write("•", question)

                else:

                    details = {
                        "annual_gross_salary":
                            parsed["annual_gross_salary"],

                        "age":
                            parsed["age"],

                        "is_resident": True,

                        "financial_year": "2024-25",
                    }

                    st.subheader(
                        "Python Tax Engine Results"
                    )

                    taxpayer = calculate_and_display(
                        details,
                        "NLP Parser"
                    )

                    if taxpayer is not None:
                        st.session_state["taxpayer"] = taxpayer

            except Exception as error:

                st.error(f"NLP processing failed: {error}")


# ==================================================
# TAB 3: GEMINI LLM
# ==================================================

with tab3:

    st.header("Gemini LLM Tax Calculator")

    st.caption(
        "Gemini extracts taxpayer information and calculates tax. "
        "The extracted details are also independently calculated "
        "using your Python tax engine."
    )

    llm_description = st.text_area(
        "Describe your salary and age",

        placeholder=(
            "I earn 12 lakh annually. "
            "I am 25 years old."
        ),

        height=120,
        key="llm_description"
    )

    if st.button(
        "Ask Gemini and Calculate Tax",
        key="ask_gemini_and_calculate"
    ):

        if not llm_description.strip():

            st.warning("Enter a description first.")

        else:

            try:

                with st.spinner("Gemini is processing..."):

                    response = ask_gemini(llm_description)

                st.subheader("Gemini Response")
                st.json(response)

                if response.get("status") != "complete":

                    st.warning(
                        "Gemini needs salary or age clarification."
                    )

                    for item in response.get(
                        "missing_information", []
                    ):
                        st.write("Missing:", item)

                    for item in response.get(
                        "contradictions", []
                    ):
                        st.write("Contradiction:", item)

                else:

                    details = response.get(
                        "taxpayer_details", {}
                    )

                    # Residency is always Indian.
                    details["is_resident"] = True

                    details.setdefault(
                        "financial_year", "2024-25"
                    )

                    st.subheader(
                        "Python Tax Engine Results"
                    )

                    taxpayer = calculate_and_display(
                        details,
                        "Gemini Parser"
                    )

                    # Gemini's own tax calculations.
                    old_llm = response.get("old_regime") or {}
                    new_llm = response.get("new_regime") or {}

                    st.subheader(
                        "Gemini's Own Tax Calculations"
                    )

                    col1, col2 = st.columns(2)

                    old_tax = old_llm.get("total_tax")
                    new_tax = new_llm.get("total_tax")

                    col1.metric(
                        "Gemini Old Regime",
                        f"₹{old_tax:,.0f}"
                        if isinstance(old_tax, (int, float))
                        else "Not provided"
                    )

                    col2.metric(
                        "Gemini New Regime",
                        f"₹{new_tax:,.0f}"
                        if isinstance(new_tax, (int, float))
                        else "Not provided"
                    )

                    st.caption(
                        "Gemini's figures are model-generated. "
                        "Python engine results are calculated independently."
                    )

                    if taxpayer is not None:
                        st.session_state["taxpayer"] = taxpayer

            except Exception as error:

                st.error(f"Gemini request failed: {error}")


# ==================================================
# TAB 4: METHOD COMPARISON
# ==================================================

with tab4:

    st.header("Compare Calculation Methods")

    st.write(
        "Calculate a taxpayer in any of the previous tabs first. "
        "Then compare hand-coded Python rules with LLM-compiled JSON rules."
    )

    taxpayer = st.session_state.get("taxpayer")

    if taxpayer is not None:

        if st.button("Compare Rules vs Compiled Rules"):

            try:

                rules_result = compare_regimes(taxpayer)

                compiled_old = calculate_compiled_regime_tax(
                    taxpayer,
                    "old"
                )

                compiled_new = calculate_compiled_regime_tax(
                    taxpayer,
                    "new"
                )

                st.subheader("Old Regime")

                col1, col2 = st.columns(2)

                col1.metric(
                    "Hand-coded Rules",
                    f"₹{rules_result['old_regime']['total_tax']:,.0f}"
                )

                col2.metric(
                    "Compiled Rules",
                    f"₹{compiled_old['total_tax']:,.0f}"
                )

                old_match = (
                    rules_result["old_regime"]["total_tax"]
                    == compiled_old["total_tax"]
                )

                st.write(
                    "Result:",
                    "MATCH" if old_match else "MISMATCH"
                )

                st.divider()

                st.subheader("New Regime")

                col1, col2 = st.columns(2)

                col1.metric(
                    "Hand-coded Rules",
                    f"₹{rules_result['new_regime']['total_tax']:,.0f}"
                )

                col2.metric(
                    "Compiled Rules",
                    f"₹{compiled_new['total_tax']:,.0f}"
                )

                new_match = (
                    rules_result["new_regime"]["total_tax"]
                    == compiled_new["total_tax"]
                )

                st.write(
                    "Result:",
                    "MATCH" if new_match else "MISMATCH"
                )

            except Exception as error:

                st.error(f"Comparison failed: {error}")

    else:

        st.info(
            "Calculate a taxpayer in another tab first."
        )
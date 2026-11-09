import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def ask_gemini(description: str) -> dict:
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
You are an Indian salaried income-tax assistant for this project.

Assumptions and scope:
- The taxpayer is ALWAYS an Indian resident. Set is_resident to true.
- Only annual gross salary and age are required from the user.
- If salary is stated monthly, convert it to annual salary by multiplying by 12.
- If salary is stated in lakh/LPA, convert it to rupees.
- If optional information is not mentioned, assume zero:
  basic salary, dearness allowance, HRA received, rent paid,
  Section 80C, Section 80CCD(1B), Section 80D, and home-loan interest.
- Other sources of income are outside this project's scope. Assume zero.
- Do not ask whether the taxpayer is a resident.
- Do not ask about other income, HRA, rent, or optional deductions.
- Ask clarification ONLY if salary or age is missing, invalid, or contradictory.
- Do not invent salary or age.
- Calculate for FY 2024-25 (AY 2025-26).
- Return valid JSON only.

Return exactly this structure:
{{
  "status": "complete or clarification_required",
  "taxpayer_details": {{
    "financial_year": "2024-25",
    "annual_gross_salary": null,
    "age": null,
    "is_resident": true,
    "basic_salary": 0,
    "dearness_allowance": 0,
    "hra_received": 0,
    "annual_rent_paid": 0,
    "is_metro_city": false,
    "section_80c_investment": 0,
    "section_80ccd_1b": 0,
    "health_insurance_self_family": 0,
    "health_insurance_parents": 0,
    "self_family_has_senior": false,
    "parents_are_senior_citizens": false,
    "home_loan_interest": 0,
    "qualifies_for_higher_24b_limit": false
  }},
  "missing_information": [],
  "contradictions": [],
  "old_regime": {{
    "taxable_income": null,
    "tax_before_cess": null,
    "cess": null,
    "total_tax": null
  }},
  "new_regime": {{
    "taxable_income": null,
    "tax_before_cess": null,
    "cess": null,
    "total_tax": null
  }},
  "recommended_regime": null,
  "explanation": [],
  "assumptions": []
}}

If salary or age is missing, set status to clarification_required and do not
guess tax figures. Otherwise set status to complete and calculate both regimes.

Taxpayer description:
{description}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    return json.loads(response.text)

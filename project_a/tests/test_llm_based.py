
import pytest
from project_a.implementations.llm_based import ask_gemini


@pytest.mark.integration
def test_gemini_response():
    description = """
    My annual salary is 12 lakh.
    I am 25 years old and a resident of India.
    I have no investments or health insurance.
    """

    response = ask_gemini(description)

    assert isinstance(response, dict)
    assert "status" in response
    assert "old_regime" in response
    assert "new_regime" in response
    assert "recommended_regime" in response


@pytest.mark.integration
@pytest.mark.parametrize("description", [
    "I earn 15 lakh annually. I am 30 years old and an Indian resident.",
    "My yearly income is 8 lakh, age 25, resident of India.",
    "Salary 12 lakh per annum. Age 28. I live in India.",
    "Meri salary 10 lakh hai, meri age 25 hai aur main India ka resident hoon.",
    "I earn 9 lakh per year.",
])
def test_gemini_different_descriptions(description):
    response = ask_gemini(description)

    assert isinstance(response, dict)
    assert response["status"] in [
        "complete",
        "clarification_required"
    ]


from project_a.parser.parser import parse_taxpayer_description


def test_parse_basic_description():
    description = (
        "My salary is 12 lakh. "
        "I am 25 years old and a resident of India."
    )

    result = parse_taxpayer_description(description)

    assert result["annual_gross_salary"] == 1200000
    assert result["age"] == 25
    assert result["is_resident"] is True
    assert result["missing_information"] == []

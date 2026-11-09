import re


def parse_taxpayer_description(description: str) -> dict:
    """Extract the two required inputs: annual salary and age.

    This project assumes the taxpayer is an Indian resident. Optional
    deductions and other financial details default to zero in the tax engine.
    """
    text = description.lower()

    result = {
        "annual_gross_salary": None,
        "age": None,
        "is_resident": True,
        "missing_information": [],
        "contradictions": [],
        "clarification_questions": [],
    }

    # Salary: supports "salary 12 lakh", "income is 12 LPA",
    # "monthly salary 50000", and common rupee formats.
    salary_pattern = re.compile(
        r"(?:annual\s+salary|yearly\s+salary|monthly\s+salary|salary|income|ctc|pay)"
        r"\s*(?:is|of|:|comes to|around)?\s*"
        r"(?:₹|rs\.?\s*)?"
        r"([\d,]+(?:\.\d+)?)\s*"
        r"(lakh|lakhs|lpa|l|thousand|k|rupees)?",
        re.IGNORECASE,
    )

    salary_matches = list(salary_pattern.finditer(text))
    salary_values = []

    for match in salary_matches:
        amount = float(match.group(1).replace(",", ""))
        unit = (match.group(2) or "").lower()

        if unit in ("lakh", "lakhs", "lpa", "l"):
            amount *= 100000
        elif unit in ("thousand", "k"):
            amount *= 1000

        salary_values.append((amount, match.start(), match.end()))

    if salary_values:
        unique_amounts = {item[0] for item in salary_values}
        if len(unique_amounts) > 1:
            result["contradictions"].append(
                "Multiple different salary amounts were provided."
            )

        amount = salary_values[0][0]
        monthly = bool(re.search(
            r"\b(monthly|per month|every month|a month)\b", text
        ))
        annual = bool(re.search(
            r"\b(annual|annually|yearly|per year|per annum|lpa)\b", text
        ))

        if monthly and annual:
            result["contradictions"].append(
                "Salary is described as both monthly and annual."
            )
        elif monthly:
            amount *= 12

        result["annual_gross_salary"] = amount

    # Age: supports "25 years old", "age 25", "I am 25", "25 saal".
    age_patterns = [
        r"\b(\d{1,3})\s*(?:years old|year old|yrs old|years|yrs)\b",
        r"\b(?:age|aged)\s*(?:is|:)?\s*(\d{1,3})\b",
        r"\bi am\s+(\d{1,3})\b",
        r"\bmeri age\s*(\d{1,3})\b",
        r"\bumar\s*(\d{1,3})\b",
        r"\b(\d{1,3})\s*saal\b",
    ]

    ages = []
    for pattern in age_patterns:
        ages.extend(int(value) for value in re.findall(pattern, text))

    unique_ages = set(ages)
    if len(unique_ages) > 1:
        result["contradictions"].append(
            "Multiple different ages were provided."
        )
    elif unique_ages:
        age = next(iter(unique_ages))
        if 0 < age <= 120:
            result["age"] = age

    # Only salary and age are required. Indian residency is assumed.
    if result["annual_gross_salary"] is None:
        result["missing_information"].append("annual_gross_salary")
        result["clarification_questions"].append(
            "What is your annual salary? If you provide monthly salary, mention that."
        )

    if result["age"] is None:
        result["missing_information"].append("age")
        result["clarification_questions"].append("What is your age?")

    result["status"] = (
        "clarification_required"
        if result["missing_information"] or result["contradictions"]
        else "complete"
    )

    return result

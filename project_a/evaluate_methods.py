import time
from project_a.schemas.taxpayer import TaxpayerInput
from project_a.implementations.rules_based import calculate_tax_rules_based
from project_a.implementations.compiled_rules import calculate_compiled_regime_tax
from project_a.implementations.llm_based import ask_gemini

def benchmark():
    taxpayer = TaxpayerInput(
        financial_year="2024-25",
        annual_gross_salary=1200000,
        age=25,
        is_resident=True,
        section_80c_investment=0,
        section_80ccd_1b=0,
        health_insurance_self_family=0,
        health_insurance_parents=0,
        self_family_has_senior=False,
        parents_are_senior_citizens=False
    )
    
    test_determinism(taxpayer)

    # Hand-coded rules
    start = time.perf_counter()
    rules_result = calculate_tax_rules_based(taxpayer)
    rules_time = time.perf_counter() - start

    # LLM-compiled rules
    start = time.perf_counter()
    compiled_results = {
        regime: calculate_compiled_regime_tax(taxpayer, regime)
        for regime in ["old", "new"]
    }
    compiled_time = time.perf_counter() - start
        # Query-time LLM
    description = (
        "I am 25 years old, a resident Indian. "
        "My annual gross salary is Rs. 12,00,000. "
        "I have no investments, insurance deductions, or home loan."
    )

    start = time.perf_counter()
    llm_result = ask_gemini(description)
    llm_time = time.perf_counter() - start
    
    test_llm_determinism()
    compare_outputs(taxpayer)

    print("\nQUERY-TIME LLM")
    print(llm_result)
    print(f"Execution time: {llm_time * 1000:.3f} ms")
    print("\nHAND-CODED RULES")
    print(rules_result)
    print(f"Execution time: {rules_time * 1000:.3f} ms")

    print("\nLLM-COMPILED RULES")
    print(compiled_results)
    print(f"Execution time: {compiled_time * 1000:.3f} ms")

def test_determinism(taxpayer):
    print("\n--- DETERMINISM TEST (10 RUNS) ---")

    # Hand-coded rules
    rules_outputs = [
        calculate_tax_rules_based(taxpayer)
        for _ in range(10)
    ]

    # LLM-compiled rules
    compiled_outputs = [
        {
            regime: calculate_compiled_regime_tax(taxpayer, regime)
            for regime in ["old", "new"]
        }
        for _ in range(10)
    ]

    print(
        "Hand-coded rules deterministic:",
        all(x == rules_outputs[0] for x in rules_outputs)
    )

    print(
        "LLM-compiled rules deterministic:",
        all(x == compiled_outputs[0] for x in compiled_outputs)
    )

def test_llm_determinism():
    print("\n--- QUERY-TIME LLM DETERMINISM (10 RUNS) ---")

    description = (
        "I am 25 years old, a resident Indian. "
        "My annual gross salary is Rs. 12,00,000. "
        "I have no investments, insurance deductions, or home loan."
    )

    outputs = []

    for i in range(10):
        try:
            result = ask_gemini(description)
            outputs.append(result)
            print(f"Run {i + 1}: Success")
        except Exception as error:
            print(f"Run {i + 1}: Failed - {error}")

    if outputs:
        print("Successful runs:", len(outputs), "/ 10")
        print(
            "Identical responses:",
            all(result == outputs[0] for result in outputs)
        )

def compare_outputs(taxpayer):
    print("\n========== METHOD COMPARISON ==========")

    # Method 1: Hand-coded rules
    rules = calculate_tax_rules_based(taxpayer)

    # Method 2: LLM-compiled rules
    compiled = {
        regime: calculate_compiled_regime_tax(taxpayer, regime)
        for regime in ["old", "new"]
    }

    print("\nHand-coded recommended regime:",
          rules["recommended_regime"])

    print("LLM-compiled old regime tax:",
          compiled["old"]["total_tax"])

    print("LLM-compiled new regime tax:",
          compiled["new"]["total_tax"])

    print("\nTax calculation agreement:")

    for regime in ["old", "new"]:
        original_tax = rules[f"{regime}_regime"]["total_tax"]
        compiled_tax = compiled[regime]["total_tax"]

        print(
            regime,
            "MATCH" if original_tax == compiled_tax else "MISMATCH",
            "| Rules:", original_tax,
            "| Compiled:", compiled_tax
        )



if __name__ == "__main__":
    benchmark()
import random
from decimal import Decimal

from project_a.implementations.compiled_rules import calculate_compiled_tax
from project_a.tax_engine.regimes import get_tax_slabs
from project_a.tax_engine.slabs import calculate_slab_tax


def test_compiled_rules_match_hand_coded_slabs():
    random.seed(42)

    for _ in range(220):
        income = Decimal(random.randint(100000, 10000000))
        age = random.choice([22, 25, 35, 45, 60, 65, 75, 80, 85])

        for regime in ["old", "new"]:

            # First get the original hand-coded slabs
            original_slabs = get_tax_slabs(
                regime, age, True, "2024-25"
            )

            # Calculate expected tax using hand-coded slabs
            expected_tax = calculate_slab_tax(
                income, original_slabs
            )

            # Calculate tax using compiled JSON rules
            compiled_result = calculate_compiled_tax(
                income, regime, age, "2024-25"
            )

            actual_tax = compiled_result["tax_before_rebate"]

            assert actual_tax == expected_tax, (
                f"Mismatch: income={income}, age={age}, regime={regime}"
            )
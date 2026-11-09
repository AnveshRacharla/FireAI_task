from decimal import Decimal

from project_a.implementations.compiled_rules import calculate_compiled_tax


def test_compiled_new_regime():
    result = calculate_compiled_tax(1000000, "new", 25)
    assert result["tax_before_rebate"] == Decimal("50000.00")
    assert result["total_tax"] == Decimal("52000.0000")


def test_compiled_old_regime():
    result = calculate_compiled_tax(1000000, "old", 25)
    assert result["tax_before_rebate"] == Decimal("112500.00")
    assert result["total_tax"] == Decimal("117000.0000")


def test_compiled_senior_citizen():
    result = calculate_compiled_tax(1000000, "old", 65)
    assert result["tax_before_rebate"] == Decimal("110000.00")


def test_compiled_super_senior():
    result = calculate_compiled_tax(1000000, "old", 85)
    assert result["tax_before_rebate"] == Decimal("100000.00")


def test_new_regime_rebate():
    result = calculate_compiled_tax(700000, "new", 25)
    assert result["rebate"] == Decimal("20000.00")


def test_old_regime_rebate():
    result = calculate_compiled_tax(500000, "old", 25)
    assert result["rebate"] == Decimal("12500")
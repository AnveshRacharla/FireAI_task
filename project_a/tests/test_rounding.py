from decimal import Decimal

from project_a.tax_engine.rounding import (
    round_taxable_income,
    round_tax_payable,
)


def test_income_rounds_down():
    assert round_taxable_income(Decimal("12344")) == Decimal("12340")


def test_income_rounds_up():
    assert round_taxable_income(Decimal("12345")) == Decimal("12350")


def test_income_ignores_paise():
    assert round_taxable_income(Decimal("12349.99")) == Decimal("12350")


def test_tax_rounds_down():
    assert round_tax_payable(Decimal("163804")) == Decimal("163800")


def test_tax_rounds_up():
    assert round_tax_payable(Decimal("163805")) == Decimal("163810")


def test_exact_multiple_of_ten():
    assert round_tax_payable(Decimal("163800")) == Decimal("163800")
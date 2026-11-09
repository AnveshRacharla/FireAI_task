
from decimal import Decimal

import pytest
from pydantic import ValidationError

from project_a.schemas.taxpayer import TaxpayerInput


def test_valid_taxpayer():
    taxpayer = TaxpayerInput(
        annual_gross_salary=1200000,
        age=25,
        is_resident=True,
        section_80c_investment=150000
    )

    assert taxpayer.age == 25
    assert taxpayer.annual_gross_salary == Decimal("1200000")
    assert taxpayer.section_80c_investment == Decimal("150000")
    assert taxpayer.is_resident is True


def test_negative_salary():
    with pytest.raises(ValidationError):
        TaxpayerInput(
            annual_gross_salary=-50000,
            age=25,
            is_resident=True
        )


def test_missing_optional_fields():
    taxpayer = TaxpayerInput(
        annual_gross_salary=1200000,
        age=25,
        is_resident=True
    )

    assert taxpayer.hra_received is None
    assert taxpayer.home_loan_interest is None


def test_unexpected_field():
    with pytest.raises(ValidationError):
        TaxpayerInput(
            annual_gross_salary=1200000,
            age=25,
            is_resident=True,
            random_field=100
        )


def test_missing_residential_status():
    with pytest.raises(ValidationError):
        TaxpayerInput(
            annual_gross_salary=1200000,
            age=25
        )

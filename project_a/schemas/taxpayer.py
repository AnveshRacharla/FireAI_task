from decimal import Decimal
from typing import Optional, Annotated

from pydantic import BaseModel, Field, ConfigDict

Money = Annotated[
    Decimal,
    Field(ge=0, max_digits=14, decimal_places=2)
]


class TaxpayerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Basic information
    financial_year: str = "2024-25"
    annual_gross_salary: Annotated[
        Decimal,
        Field(gt=0, max_digits=14, decimal_places=2)
    ]
    age: int = Field(ge=0, le=120)
    is_resident: bool

    # HRA information
    basic_salary: Optional[Money] = None
    dearness_allowance: Optional[Money] = None
    hra_received: Optional[Money] = None
    annual_rent_paid: Optional[Money] = None
    is_metro_city: Optional[bool] = None

    # Section 80C
    section_80c_investment: Optional[Money] = None

    # Section 80CCD(1B)
    section_80ccd_1b: Optional[Money] = None

    # Section 80D
    health_insurance_self_family: Optional[Money] = None
    health_insurance_parents: Optional[Money] = None
    self_family_has_senior: Optional[bool] = None
    parents_are_senior_citizens: Optional[bool] = None

    # Section 24(b)
    home_loan_interest: Optional[Money] = None
    qualifies_for_higher_24b_limit: Optional[bool] = None
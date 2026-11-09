from project_a.tax_engine.calculator import compare_regimes
from project_a.schemas.taxpayer import TaxpayerInput


def calculate_tax_rules_based(taxpayer: TaxpayerInput) -> dict:
    """
    Calculate tax using predefined tax rules.
    """
    return compare_regimes(taxpayer)
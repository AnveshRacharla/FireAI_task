# Project A – Indian Income Tax Engine Results

## 1. Implementation Summary

Implemented an Indian salaried income tax calculation engine supporting:

- Financial Years 2024–25 and 2025–26
- Old and New tax regimes
- Standard deduction
- HRA exemption
- Sections 80C, 80CCD(1B), 80D and 24(b)
- Section 87A rebate and marginal relief
- Surcharge and 4% health and education cess
- Senior and super-senior citizen slab handling

## 2. Automated Testing

| Metric | Result |
|---|---:|
| Total collected tests | 131 |
| Passed | 124 |
| Deselected | 7 |
| Failed | 0 |
| Execution time | 0.93 seconds |

All 124 selected tests passed.

## 3. Numerical Test Dataset

The automated test suite includes 220 numerical test cases. The dataset regression test passed.

Note: These are internal regression tests, not 220 independent official validations.

## 4. Official Calculator Validation

Five taxpayer profiles were checked against the official Income Tax Calculator, covering both tax regimes.

| Metric | Result |
|---|---:|
| Profiles checked | 5 |
| Regime comparisons | 10 |
| Tax regimes | Old and New |
| Status | Checked |

## 5. Implementation Comparison

The following sample taxpayer was used to compare the calculation methods:

- Financial year: 2024–25
- Gross salary: ₹12,00,000
- Age: 25
- Residential status: Resident
- Deductions: None

| Method | Old Regime | New Regime |
|---|---:|---:|
| Hand-coded rules | ₹1,63,800 | ₹71,500 |
| LLM-compiled rules | ₹1,63,800 | ₹71,500 |
| Query-time LLM | ₹1,69,000 | ₹72,800 |

The query-time LLM produced inconsistent arithmetic in its explanation. This demonstrates why final tax calculations should use deterministic rules rather than relying on free-form LLM arithmetic.

## 6. Determinism and Latency

| Method | Determinism | Measured latency |
|---|---|---:|
| Hand-coded rules | Yes, across 10 runs | 0.163 ms |
| LLM-compiled rules | Yes, across 10 runs | 0.913 ms |
| Query-time LLM | Responses varied; one API failure | 3778.248 ms |

Latency figures are measurements from the recorded benchmark run, not guaranteed production performance.

## 7. Key Findings

- Hand-coded rules provide fast and deterministic calculations.
- LLM-compiled rules matched the hand-coded engine in the tested comparison.
- Query-time LLM responses were slower and less consistent.
- LLMs are better suited to interpreting natural-language input and identifying missing information.
- Deterministic tax rules should remain responsible for final tax arithmetic.

## 8. Limitations

- Official validation covered five taxpayer profiles, not the full requested 30.
- Numerical regression cases are not independent official validations.
- Query-time LLM reliability depends on external API availability.
- The implementation focuses on the assignment's specified salaried-income scope and should not be treated as a complete tax filing application.

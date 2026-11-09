# AI Usage Documentation

## 1. AI Tools Used

Generative AI assistance was used during development to support implementation, debugging, explanations, and documentation.

The project also integrates the Gemini API for query-time natural-language tax interpretation.

## 2. Areas Where AI Assistance Was Used

- Understanding the assignment requirements.
- Designing the project structure and tax-engine modules.
- Assistance with Python implementation and debugging.
- Creating and improving test cases.
- Developing the natural-language parser.
- Designing prompts for the Gemini API.
- Reviewing benchmark results and documenting findings.
- Preparing the project frontend.

## 3. Human Review and Verification

AI-generated suggestions were not accepted blindly.

The implementation was reviewed and tested through:

- Automated pytest tests.
- Tax slab boundary tests.
- Old and new regime comparisons.
- Compiled-rule parity tests.
- Selected comparisons with the official Income Tax Calculator.
- Manual review of inconsistent LLM arithmetic.

## 4. Limitations and Risks

- AI-generated code can contain logical or calculation errors.
- LLM responses can vary between requests.
- External API services can fail or become unavailable.
- AI-generated tax rules require verification against authoritative tax provisions.

## 5. Responsibility

The final implementation, testing, validation, and technical decisions were reviewed by the project developer. Deterministic tax calculations are performed by the rule-based engine rather than trusting free-form LLM calculations.

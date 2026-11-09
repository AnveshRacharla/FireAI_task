# Decision Matrix – Project A

## 1. Comparison of Approaches

| Evaluation Criterion | Hand-Coded Rules | LLM-Compiled Rules | Query-Time LLM |
|---|---|---|---|
| Calculation accuracy | Strong in tested cases | Matches hand-coded engine in tested cases | Inconsistent arithmetic observed |
| Determinism | Yes | Yes | No |
| Latency | 0.163 ms | 0.913 ms | 3778.248 ms |
| External API dependency | No | Only during compilation, if applicable | Yes |
| Auditability | High | High when compiled rules are reviewed | Lower |
| Rule updates | Manual code changes | Regenerate and validate rules | Update prompts/context |
| Natural-language understanding | Limited | Limited at runtime | Strong potential |
| Reliability | High in tested cases | High in tested cases | API failures observed |

## 2. Decision

**Selected approach: Hybrid architecture**

Use an LLM to interpret natural-language taxpayer descriptions and identify missing or contradictory information.

Use deterministic, hand-coded tax rules for final calculations.

LLM-compiled rules can be used as an additional rule-generation approach, but generated rules must be validated before deployment.

## 3. Reasoning

1. Tax calculations require predictable and reproducible results.
2. Hand-coded rules were deterministic across 10 runs.
3. LLM-compiled rules matched the hand-coded engine in the tested comparison.
4. Query-time LLM responses showed inconsistent arithmetic and higher latency.
5. A hybrid approach separates language understanding from financial computation.

## 4. Final Architecture

Natural-language input → LLM/parser → Structured taxpayer data → Validation and clarification → Deterministic tax engine → Tax result and explanation

## 5. Final Recommendation

For a tax calculation system, use deterministic rules as the source of truth. Use LLMs as supporting components for interpreting user input, not as the final authority for calculating tax.

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

---

# Decision Matrix – Project B: NYC 311 Data Quality Engine

## 1. Comparison of Detection Approaches

| Evaluation Criterion | Rule-Based Detection | Statistical Detection | Machine Learning (Isolation Forest) | LLM-Based Detection (Gemini 3.5) | Hybrid Pipeline |
|---|---|---|---|---|---|
| **Precision** | 60.20% | **61.62%** | 39.52% | 50.00% | 49.75% |
| **Recall** | 86.12% | 29.19% | 23.44% | 1.44% (sample-capped) | **97.13%** |
| **F1-Score** | **0.7087** | 0.3961 | 0.2943 | 0.0279 | 0.6580 |
| **False Positive Rate** | 14.66% | **4.68%** | 9.24% | **0.37%** | 25.25% |
| **Throughput (rows/s)** | 939.9 | 3,782.9 | **23,535.9** | 80.4 | 31.0 |
| **Per-Row Latency** | 1.064 ms | 0.264 ms | **0.043 ms** | 12.445 ms | 32.302 ms |
| **Est. Cost / 1M Rows** | **$0.002** | $0.005 | $0.080 | $18.500 | $1.250 |
| **Determinism** | Yes | Yes (fixed reference) | Yes (fixed seed) | No | Yes (deterministic fusion) |
| **Unstructured Text Capability** | Regex / control chars | Low | None | **High** | High |
| **Multivariate Anomaly Detection**| Manual pairs only | Low | **High** | Medium | High |
| **Distribution Drift Detection** | No | **Yes (TVD/PSI)** | Indirect | No | Yes |

## 2. Decision

**Selected Architecture: Tiered Hybrid Pipeline with Funnel Routing**

Combine the four approaches in a tiered funnel architecture:
1. **Tier 1 (100% Ingestion)**: Run vectorized **Rule-Based** and **Statistical** checks on all records. This catches 86%+ of all standard structural defects and distribution drifts at sub-millisecond CPU speed and virtually zero cost.
2. **Tier 2 (15% Flagged/Sampled Subset)**: Run **Machine Learning (Isolation Forest)** scoring on borderline records and spatial coordinate pairs to detect non-linear multi-dimensional anomalies.
3. **Tier 3 (0.5–1% High-Risk Triage)**: Route unstructured text fields and ambiguous multi-column disputes to **LLM Detection (Gemini)** for semantic audit.
4. **Alert Fusion & Deduplication**: Group overlapping alerts across detectors, fuse confidence scores, escalate consensus severity, and prioritize triage order.

## 3. Reasoning

1. **Maximum Defect Coverage (97.13% Recall)**: No single detector detects all 12 corruption types. Statistical detection excels at distribution shifts; Isolation Forest discovers coordinate and duration anomalies; rules catch explicit structural and domain constraint violations; LLMs understand gibberish text and semantic conflicts.
2. **Cost and Latency Feasibility at 50M Rows/Day**: Running LLMs on 50M rows/day would cost over $900/day and introduce massive latency bottlenecks. Running rules and statistical methods first filters out the vast majority of normal records, keeping estimated hybrid processing costs at ~$1.25 per million rows.
3. **Deduplication and Alarm Fatigue Reduction**: In high-throughput municipal pipelines, multiple detectors flagging the same record causes alert fatigue. Merging alerts and escalating severity on consensus creates clean, actionable issue tickets.
4. **Auditability & Explainability**: Preserving detector-level rationales within the fused alert ensures engineers and municipal operators understand exactly why a record was flagged.

## 4. Final Recommendation

For large-scale data quality validation, deploy the **Tiered Hybrid Pipeline**. Use fast deterministic rules and statistical profiling as the high-throughput first line of defense, utilize unsupervised ML for multidimensional spatial/numeric outlier screening, and reserve LLMs for targeted semantic triage of complex text fields.


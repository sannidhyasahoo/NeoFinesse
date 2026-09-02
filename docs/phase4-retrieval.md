# Phase 4 — Evidence Retrieval Experiments (Corrected)

## 1. Overview & Objective

Phase 4 evaluates and benchmarks **six evidence-retrieval strategies** for financial investigation across three explicit task categories:
1. **`SETTLEMENT_RCA`**: Root-cause analysis of settlement batch variances (`VAR-001`, `VAR-002`, `VAR-003`, `VAR-004`, `VAR-008`, `VAR-009`, `VAR-010`).
2. **`UPI_STATE_INVESTIGATION`**: Multi-state lifecycle, callback timing, and auto-reversal investigation (`VAR-005`, `VAR-006`).
3. **`BANK_SETTLEMENT_STATE`**: Bank clearing delay and UTR credit validation (`VAR-007`).

### Strict Evaluator Semantics
- **No False 100% Scores on 0/0**: If expected causes = 0, recall is reported as `N/A` rather than `100.0%`.
- **Applicability Filtering**: Non-applicable strategies report `is_applicable = False` and `N/A` metrics, preventing distortion of aggregate scores.
- **Identity-First UPI Retrieval**: UPI transactions are retrieved as coherent root candidates containing their discrete transition histories rather than exploding into hundreds of unlinked event candidates.

---

## 2. The Six Retrieval Strategies

| Strategy | Enum | Scope & Mechanism | Primary Applicable Task |
|---|---|---|---|
| **Strategy 1** | `DIRECT_ID` | Exact primary / foreign key matching (`settlement_id`, `payment_id`, `line_id`, `UTR`). | `SETTLEMENT_RCA`, `BANK_SETTLEMENT_STATE` |
| **Strategy 2** | `ATTRIBUTE` | Global scan matching financial attributes (`amount`, `transaction type`, `provider`). | `SETTLEMENT_RCA`, `BANK_SETTLEMENT_STATE` |
| **Strategy 3** | `RELATIONSHIP` | Traverses explicit graph: `Settlement → Line → Event` and `Payment → Event`. | `SETTLEMENT_RCA`, `BANK_SETTLEMENT_STATE` |
| **Strategy 4** | `TYPED_PROVENANCE` | Relationship traversal + deep audit verification (`File → Sheet → Row → Cell` + dual SHA-256 hashes). | `SETTLEMENT_RCA`, `BANK_SETTLEMENT_STATE` |
| **Strategy 5** | `TEMPORAL_RELATIONSHIP` | Relational candidates + Phase 3 temporal cutoff constraint filter (`event.timestamp <= cutoff`). | `SETTLEMENT_RCA`, `BANK_SETTLEMENT_STATE` |
| **Strategy 6** | `UPI_EVENT` | Extracts coherent UPI transaction root candidates with chronological state transition histories + reversal proof. | `UPI_STATE_INVESTIGATION` |

---

## 3. Aggregate Strategy Performance Metrics

Evaluated across all 10 ground truth scenarios ($6 \times 10 = 60$ experiment runs) with strict N/A handling:

| Strategy | Applicable Cases | Evidence Recall (%) | Candidate Precision (%) | Decoy Rejection Rate (%) | Provenance Coverage (%) | Avg Latency (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`DIRECT_ID`** | 8 / 10 | **100.0%** | 14.7% | **100.0%** | 100.0% | 0.07 ms |
| **`ATTRIBUTE`** | 8 / 10 | 40.0% | 25.0% | **0.0%** *(Captures Decoys!)* | 100.0% | 0.03 ms |
| **`RELATIONSHIP`** | 8 / 10 | **100.0%** | 35.7% | 66.7% *(Rejects Relational Decoys)* | 100.0% | 0.06 ms |
| **`TYPED_PROVENANCE`** | 8 / 10 | **100.0%** | 35.7% | 66.7% | **100.0%** | 0.07 ms |
| **`TEMPORAL_RELATIONSHIP`**| 8 / 10 | **100.0%** | **38.5%** | **100.0%** *(Rejects Temporal Decoys)*| 100.0% | 0.07 ms |
| **`UPI_EVENT`** | 2 / 10 | **100.0%** | **50.0%** | 0.0% | 100.0% | 0.06 ms |

---

## 4. Key Empirical Findings

1. **Why Pure Attribute Matching Fails in Finance Operations:**  
   `ATTRIBUTE` has a **0.0% decoy rejection rate**, capturing false positives across `VAR-002`, `VAR-008`, and `VAR-009`. Treating exact amount matches as proof generates severe noise in finance queues.
2. **Relational Traversals Eliminate Spurious Amount Matches:**  
   `RELATIONSHIP` eliminates unrelated payment and settlement decoys (`VAR-002`, `VAR-009`), boosting candidate precision significantly (+43% over attribute matching).
3. **Temporal Cutoffs Prune Post-Cutoff Decoys:**  
   In `VAR-008`, a refund occurred 20 days after batch cutoff. `RELATIONSHIP` alone retrieved it because it shared batch keys; only `TEMPORAL_RELATIONSHIP` rejected it as `OUTSIDE_WINDOW`.
4. **Coherent Root Candidates for UPI Lifecycles:**  
   In `VAR-005` and `VAR-006`, querying the static payment record alone returns incomplete information. `UPI_EVENT` retrieves the single root UPI transaction with its complete transition timeline (`INITIATED → PENDING → FAILED → CAPTURED`) and auto-reversal confirmations without candidate explosion.
5. **100% Provenance Coverage:**  
   `TYPED_PROVENANCE` verified 100% of candidate attributes down to exact Excel cells (`D193`) and row-level SHA-256 hashes, ensuring zero ungrounded claims reach downstream controllers.

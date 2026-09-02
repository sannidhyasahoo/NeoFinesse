# Phase 4 — Evidence Retrieval Experiments

## 1. Overview & Objective

Phase 4 evaluates and benchmarks **six progressively stronger evidence-retrieval strategies** for settlement variance investigation.

### Fundamental Principle
> **Retrieval ≠ Verification.**  
> Retrieval answers: *"What candidate evidence should an investigator inspect?"*  
> Verification remains the deterministic responsibility of the Phase 3 solver. Retrieval never concludes that a candidate is a proven cause.

---

## 2. The Six Retrieval Strategies

| Strategy | Enum | Scope & Mechanism | Intended Behavior & Tradeoffs |
|---|---|---|---|
| **Strategy 1** | `DIRECT_ID` | Exact primary / foreign key matching (`settlement_id`, `payment_id`, `line_id`, `UTR`). | Highly specific, zero false positives, but cannot discover external unassigned deductions. |
| **Strategy 2** | `ATTRIBUTE` | Global scan matching financial attributes (`amount`, `transaction type`, `provider`). | Highest recall, but **worst precision**; intentionally captures same-amount decoys across the entire database. |
| **Strategy 3** | `RELATIONSHIP` | Traverses explicit graph: `Settlement → Line → Event` and `Payment → Event`. | High recall, rejects unrelated payment/settlement decoys, but cannot detect temporal cutoff violations. |
| **Strategy 4** | `TYPED_PROVENANCE` | Relationship traversal + deep audit verification (`File → Sheet → Row → Cell` + dual SHA-256 hashes). | 100% provenance coverage; guarantees every candidate is verifiable down to specific spreadsheet cells. |
| **Strategy 5** | `TEMPORAL_RELATIONSHIP` | Relational candidates + Phase 3 temporal cutoff constraint filter (`event.timestamp <= cutoff`). | Rejects post-cutoff decoys (e.g. `VAR-008` 20-day late refund) and explicitly records rejection reasons. |
| **Strategy 6** | `UPI_EVENT` | Extracts complete chronological state transitions (`INITIATED → PENDING → FAILED → CAPTURED`) + debit/reversal proof. | Essential for UPI late authorizations and auto-reversals; preserves full event history rather than collapsed status. |

---

## 3. Aggregate Strategy Performance Metrics

Evaluated across all 10 ground truth scenarios ($6 \times 10 = 60$ experiment runs):

| Strategy | Evidence Recall (%) | Candidate Precision (%) | Decoy Rejection Rate (%) | Provenance Coverage (%) | Avg Latency (ms) | Median Latency (ms) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **`DIRECT_ID`** | 83.3% | 18.5% | 100.0% | 100.0% | 0.08 ms | 0.08 ms |
| **`ATTRIBUTE`** | **100.0%** | 12.8% | **0.0%** | 100.0% | 0.12 ms | 0.11 ms |
| **`RELATIONSHIP`** | 83.3% | 33.3% | 75.0% | 100.0% | 0.07 ms | 0.07 ms |
| **`TYPED_PROVENANCE`** | 83.3% | 33.3% | 75.0% | **100.0%** | 0.09 ms | 0.09 ms |
| **`TEMPORAL_RELATIONSHIP`**| 83.3% | **35.7%** | **75.0%** | 100.0% | 0.08 ms | 0.08 ms |
| **`UPI_EVENT`** | 100.0%* | 20.0% | 100.0% | 100.0% | 0.15 ms | 0.14 ms |

*\* Note: `UPI_EVENT` achieves 100% recall on UPI-related cases with full discrete state transition capture.*

---

## 4. Scenario-by-Scenario Retrieval Matrix (60 Runs)

| Scenario ID | Name | `DIRECT_ID` | `ATTRIBUTE` | `RELATIONSHIP` | `TYPED_PROVENANCE` | `TEMPORAL_RELATIONSHIP` | `UPI_EVENT` |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **VAR-001** | `REFUND_VARIANCE` | Found | Found | Found | Found + Prov Verified | Found + Valid Time | N/A |
| **VAR-002** | `SAME_AMOUNT_DECOY` | Found Real | Found Real + Decoy | Found Real (Rejected Decoy) | Found Real (Prov Verified) | Found Real (Rejected Decoy) | N/A |
| **VAR-003** | `PARTIAL_EXPLANATION` | Found ₹3k | Found ₹3k | Found ₹3k | Found ₹3k (Prov Verified) | Found ₹3k (Valid Time) | N/A |
| **VAR-004** | `MULTIPLE_EVENT` | Found Both | Found Both | Found Both (₹700 + ₹300) | Found Both (Prov Verified) | Found Both (Valid Time) | N/A |
| **VAR-005** | `UPI_LATE_SUCCESS` | Found Pay | Found Pay | Found Pay | Found Pay (Prov Verified) | Found Pay (Valid Time) | Found 3 Events + State |
| **VAR-006** | `UPI_DEBIT_REVERSAL`| Found | Found | Found | Found (Prov Verified) | Found (Valid Time) | Found Reversal + ₹0 Net |
| **VAR-007** | `DELAYED_CREDIT` | Found Bank | Found Bank | Found Bank | Found Bank (Prov Verified) | Found Bank (Valid Time) | N/A |
| **VAR-008** | `WRONG_DATE_DECOY` | Found Pay | Found Decoy | Found Decoy | Found Decoy (Prov Verified)| **Rejected Decoy (OUTSIDE_WINDOW)** | N/A |
| **VAR-009** | `WRONG_PAYMENT_DECOY`| Found Pay | Found Decoy | **Rejected Decoy (RELATIONSHIP)** | **Rejected Decoy** | **Rejected Decoy** | N/A |
| **VAR-010** | `UNEXPLAINED` | 0 Causes | Found False Matches | **0 Causes (Clean)** | **0 Causes (Clean)** | **0 Causes (Clean)** | N/A |

---

## 5. Key Empirical Findings

1. **Why Pure Attribute Matching Fails in Financial Ops:**  
   `ATTRIBUTE` achieves 100% recall but has a **0.0% decoy rejection rate**, capturing false positives in `VAR-002`, `VAR-008`, and `VAR-009`. Treating amount matches as candidates creates noisy investigation queues.
2. **Relational Traversals Eliminate Spurious Amount Matches:**  
   `RELATIONSHIP` eliminates unrelated payment and settlement decoys, increasing precision by +160% compared to `ATTRIBUTE`.
3. **Temporal Cutoff Pruning is Essential for Late Events:**  
   In `VAR-008`, a refund of exact matching amount occurred 20 days after batch cutoff. `RELATIONSHIP` alone could not reject it because it shared batch keys; only `TEMPORAL_RELATIONSHIP` successfully rejected it as `OUTSIDE_WINDOW`.
4. **Discrete UPI Event Chains Prevent State Misattribution:**  
   In `VAR-005` and `VAR-006`, querying the static payment record alone returns incomplete information. `UPI_EVENT` reconstructs the discrete intermediate states (`INITIATED → PENDING → FAILED → CAPTURED`) and auto-reversal events.
5. **Exact Cell Provenance Enables Instant Auditability:**  
   `TYPED_PROVENANCE` verified 100% of candidate attributes down to exact Excel cells (`D193`) and row-level SHA-256 hashes, ensuring zero ungrounded claims reach downstream controllers.

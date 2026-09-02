# Phase 6 — AI Evidence-Constrained Financial Investigator

## 1. Overview & Core Objective

Phase 6 introduces an LLM-based investigation layer on top of the frozen Phase 1–5 architecture.

### Foundational Principle
> **"LLM proposes. Evidence constrains. Deterministic verifier decides."**

In NeoFinesse, the AI is never granted autonomous closure authority. Instead, the AI operates over structured, provenance-backed **Evidence Packs**, formulates competing hypotheses, surfaces hidden conflicts or missing documentation, and submits its proposals to the **Phase 5 Deterministic Verifier**.

---

## 2. Architecture

```text
               Target Settlement Variance
                           │
                           ▼
               Phase 4 Evidence Retrieval
                           │
                           ▼
                 Evidence Pack Builder
          (Minimal, Isolated Context + Provenance)
                           │
                           ▼
                     Prompt Engine
          (Strict constraints + EV-N identifiers)
                           │
                           ▼
                    LLM Client Layer
               (Mock / Generic Env Client)
                           │
                           ▼
                   AI Response Parser
             (Markdown stripping + JSON schema)
                           │
                           ▼
                  AI Response Validator
          ┌──────────────────────────────────────┐
          │  1. Hallucination Check (EV-N IDs)   │
          │  2. Independent Math Recalculation   │
          │  3. Conflict & Missing Ev. Extraction│
          └──────────────────┬───────────────────┘
                             │
                             ▼
                   AIVerifierBridge
                             │
                             ▼
            Phase 5 Deterministic Verifier
         ┌───────────────────┬───────────────────┐
         ▼                   ▼                   ▼
    Relationship         Temporal              State
     Constraint         Constraint          Constraint
         │                   │                   │
         ├───────────────────┼───────────────────┤
         ▼                   ▼                   ▼
     Provenance          Monetary         Counterfactual
     Constraint         Constraint           Residual
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                             ▼
                     Hypothesis Scorer
                             │
                             ▼
                   Winning Hypothesis?
                   ┌─────────┴─────────┐
                   ▼                   ▼
                 YES                   NO
                   │                   │
         ┌─────────┴─────────┐         ▼
         ▼                   ▼      ESCALATE
     RESOLVED            PARTIAL
         │                   │         │
         └─────────┬─────────┴─────────┘
                   ▼
         Investigation Audit Record
     (Full Provenance + AI Reasoning & Conflicts)
```

---

## 3. Evidence Pack Design

The LLM is never given access to the raw global dataset. It receives an isolated `EvidencePack` containing:
- **`settlement_context`**: gross amount, net settled amount, fees, tax, UTR, and batch creation/settlement timestamps.
- **`settlement_lines`**: constituent line breakdown with source event types.
- **`evidence_items`**: each assigned a deterministic identifier (`EV-1`, `EV-2`, ...), preserving:
  - `entity_id` and `entity_type`
  - integer amounts in paise and INR
  - signed `net_financial_effect`
  - ISO timestamp and observed status
  - `relationship_path` (e.g. `Settlement → Line → Refund`)
  - dual-hash cell provenance (`source_file`, `source_row`, `source_hash`, `record_hash`).

---

## 4. Independent Verification & Untrusted AI Calculations

1. **Hallucination Prevention**:  
   Every `evidence_id` in `ai_hypothesis.evidence_ids` is cross-referenced against `EvidencePack.evidence_items`. Any hypothesis referencing an invented ID is rejected immediately during schema validation with `HALLUCINATED_EVIDENCE_ID`.
2. **Untrusted Arithmetic**:  
   The LLM's claimed explained amount is discarded for mathematical decisions. The validator independently computes $\sum \text{net\_financial\_effects}$ from the authentic evidence records in integer paise.
3. **Deterministic Constraint Enforcement**:  
   The bridged hypothesis must pass all Phase 5 constraints:
   - **Monetary**: Exact subset sum match in paise.
   - **Relationship**: Explicit foreign-key linkage to the target settlement batch.
   - **Temporal**: Pre-cutoff event timestamp.
   - **State**: Valid lifecycle status (`PROCESSED`, active dispute, confirmed reversal).
   - **Provenance**: Verified SHA-256 dual hashes and cell coordinates.

---

## 5. Phase 5 vs Phase 6 Comparative Scorecard

Evaluated across all 10 ground truth scenarios:

```text
================================================================================
PHASE 5 vs PHASE 6 COMPARATIVE SCORECARD
================================================================================
Total Scenarios Evaluated:         10
Phase 5 Root Cause Accuracy:       100.0%
Phase 6 AI-Guarded Accuracy:       100.0%
Phase 5 False Closure Rate:        0.0% (0 false closures)
Phase 6 False Closure Rate:        0.0% (0 false closures)
Total Conflicts Surfaced:          3
Total Missing Evidence Surfaced:   3
Verifier Corrections (Safety):     0
Cases Where AI Helped:             10
Avg Latency (Phase 5 Baseline):    0.25 ms
Avg Latency (Phase 6 AI-Guarded):  0.56 ms
================================================================================
```

---

## 6. Detailed Scenario Breakdown

| Scenario ID | Name | Expected Outcome | Phase 5 Outcome | Phase 6 AI Recommendation | Phase 6 Verified Outcome | Conflicts Surfaced | Missing Ev. Surfaced | Safety Match |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **VAR-001** | `REFUND_VARIANCE` | `RESOLVED` | `RESOLVED` | `hyp_ai_1_refund` | `RESOLVED` | 0 | 0 | ✅ PASS |
| **VAR-002** | `SAME_AMOUNT_DECOY` | `RESOLVED` | `RESOLVED` | `hyp_ai_real_refund` | `RESOLVED` | 1 (`MEMBERSHIP`) | 0 | ✅ PASS |
| **VAR-003** | `PARTIAL_EXPLANATION` | `PARTIALLY_RESOLVED` | `PARTIALLY_RESOLVED` | `hyp_ai_partial_refund` | `PARTIALLY_RESOLVED` | 0 | 1 (`ADJUSTMENT`) | ✅ PASS |
| **VAR-004** | `MULTIPLE_EVENT` | `RESOLVED` | `RESOLVED` | `hyp_ai_composite` | `RESOLVED` | 0 | 0 | ✅ PASS |
| **VAR-005** | `UPI_LATE_SUCCESS` | `RESOLVED` | `RESOLVED` | `hyp_ai_upi_late_success` | `RESOLVED` | 0 | 0 | ✅ PASS |
| **VAR-006** | `UPI_DEBIT_REVERSAL` | `RESOLVED` | `RESOLVED` | `hyp_ai_upi_reversal` | `RESOLVED` | 0 | 0 | ✅ PASS |
| **VAR-007** | `DELAYED_BANK_CREDIT` | `VALID_DELAYED_CREDIT` | `VALID_DELAYED_CREDIT` | `hyp_ai_delayed_credit` | `VALID_DELAYED_CREDIT` | 0 | 0 | ✅ PASS |
| **VAR-008** | `WRONG_DATE_DECOY` | `ESCALATE` | `ESCALATE` | *None (Escalate)* | `ESCALATE` | 1 (`TIMING`) | 1 (`REFUND`) | ✅ PASS |
| **VAR-009** | `WRONG_PAYMENT_DECOY`| `ESCALATE` | `ESCALATE` | *None (Escalate)* | `ESCALATE` | 1 (`MEMBERSHIP`) | 0 | ✅ PASS |
| **VAR-010** | `UNEXPLAINED` | `ESCALATE` | `ESCALATE` | *None (Escalate)* | `ESCALATE` | 0 | 1 (`LINE`) | ✅ PASS |

---

## 7. Safety Guarantees & Verifier Corrections

1. **Zero False Closures (0.0% False Closure Rate)**:  
   If the LLM attempts an unsupported closure on a decoy (e.g. simulated via `MockMode.UNSUPPORTED_CLOSURE`), the deterministic verifier immediately detects the relational/temporal constraint violation and overrides the decision to `ESCALATE`.
2. **Conflict & Missing Evidence Surfacing**:  
   The AI layer provides structured contextual intelligence that pure rule-based matching lacks, explaining *why* a candidate was rejected (e.g. `TIMING_MISMATCH: Event occurred 20 days after cutoff`) and *what* evidence would be needed for future closure.
3. **Sub-Millisecond Verification Guardrail**:  
   The entire LLM parsing, validation, and deterministic constraint verification pipeline executes in under **1 ms** in mock mode, maintaining high throughput for finance operations.

# Phase 5 — Settlement Variance Investigator

## 1. Overview & Core Objective

Phase 5 converts Phase 4 retrieved evidence into a **deterministic financial investigation engine**.

### Guiding Axiom
> **Plausible ≠ Proven.**  
> A candidate transaction that happens to match a variance amount is never treated as proof. To close or resolve a variance, an explanation must pass independent financial, relational, temporal, state lifecycle, and provenance constraints.

Phase 5 establishes the deterministic investigation baseline **before** any AI or LLM components are introduced.

---

## 2. Investigator Architecture

```text
                   Target Variance / Case
                             │
                             ▼
                 Phase 4 Retrieval Layer
          (TemporalRelationship / UPI / DirectID)
                             │
                             ▼
                     Evidence Candidates
                             │
                             ▼
                   Hypothesis Generator
             • Single-Event Hypotheses
             • Multi-Event / Composite Hypotheses
             • Partial Hypotheses
             • Delayed Settlement Hypotheses
             • UPI Lifecycle Hypotheses
                             │
                             ▼
                Constraint Verification Engine
          ┌──────────────────┬──────────────────┐
          ▼                  ▼                  ▼
     Relationship        Temporal             State
      Constraint        Constraint          Constraint
          │                  │                  │
          ├──────────────────┼──────────────────┤
          ▼                  ▼                  ▼
      Provenance         Monetary        Counterfactual
      Constraint        Constraint          Residual
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                             ▼
                     Hypothesis Scorer
            (Interpretable Deterministic Ranking)
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
         Audit Record Builder
     (Full Provenance + Counterfactual Notes)
```

---

## 3. The Five Independent Constraints

| Constraint | Evaluation Target | Success Condition | Rejection Outcome |
|---|---|---|---|
| **`MonetaryConstraint`** | Signed financial effect sum in integer paise | $\sum \text{net\_financial\_effects} = \text{target\_variance}$ | Fails on amount overage; warns on valid partial residual |
| **`RelationshipConstraint`** | Foreign-key graph paths | Entity connected via `Settlement → Line → Event` or `Payment → Event` | **Fails on same-amount decoys** from other settlements / payments |
| **`TemporalConstraint`** | Timestamp vs cutoff window | $\text{timestamp} \le \text{cutoff} + \text{buffer}$ (2h for deductions, 48h for bank clearing) | **Fails on wrong-date decoys** occurring after batch cutoff |
| **`StateConstraint`** | Normalized lifecycle states | Refunds `PROCESSED`, Disputes active, UPI reconstructed state confirmed | Fails on `FAILED` refunds or failed un-reversed debits |
| **`ProvenanceConstraint`** | Dual-hash cell coordinate chain | Valid `source_file`, `source_row`, `source_hash`, `record_hash` | Fails to reach evidence level `L5` if provenance is incomplete |

---

## 4. Phase 5 Benchmark Scorecard

Evaluated against the 10 adversarial failure scenarios with ground truth isolation:

```text
================================================================================
PHASE 5 INVESTIGATION SCORECARD
================================================================================
Total Scenarios Evaluated:         10
Correct Outcomes:                 10 / 10
Root Cause Accuracy:              100.0%
False Closure Rate:               0.0% (0 false closures)
Partial Attribution Accuracy:     100.0%
Honest Exception Rate:            100.0%
Average Investigation Latency:    0.26 ms
Median Investigation Latency:     0.23 ms
Max Investigation Latency:        0.58 ms
================================================================================
```

---

## 5. Scenario Analysis (VAR-001 through VAR-010)

| Scenario ID | Name | Target Variance | Winning Hypothesis | Level | Observed Status | Expected Status | Match |
|---|---|:---:|---|:---:|:---:|:---:|:---:|
| **VAR-001** | `REFUND_VARIANCE` | -₹2,000.00 | Single Refund `rfnd_scen_001` | L5 | `RESOLVED` | `RESOLVED` | ✅ PASS |
| **VAR-002** | `SAME_AMOUNT_DECOY` | -₹2,500.00 | Real Refund `rfnd_scen_002_real` | L5 | `RESOLVED` | `RESOLVED` | ✅ PASS |
| **VAR-003** | `PARTIAL_EXPLANATION` | -₹5,000.00 | Refund `rfnd_scen_003` (₹3k) | L3 | `PARTIALLY_RESOLVED` | `PARTIALLY_RESOLVED` | ✅ PASS |
| **VAR-004** | `MULTIPLE_EVENT` | -₹1,000.00 | Composite (₹700 rfnd + ₹300 adj) | L5 | `RESOLVED` | `RESOLVED` | ✅ PASS |
| **VAR-005** | `UPI_LATE_SUCCESS` | ₹0.00 | UPI `LATE_SUCCESS` lifecycle | L5 | `RESOLVED` | `RESOLVED` | ✅ PASS |
| **VAR-006** | `UPI_DEBIT_REVERSAL` | ₹0.00 | UPI `DEBIT_REVERSED` (₹0 net) | L5 | `RESOLVED` | `RESOLVED` | ✅ PASS |
| **VAR-007** | `DELAYED_BANK_CREDIT` | ₹0.00 | Bank clearing window (36h) | L5 | `VALID_DELAYED_CREDIT` | `VALID_DELAYED_CREDIT` | ✅ PASS |
| **VAR-008** | `WRONG_DATE_DECOY` | ₹4,000.00 | *None (Decoy rejected by Temporal)* | N/A | `ESCALATE` | `ESCALATE` | ✅ PASS |
| **VAR-009** | `WRONG_PAYMENT_DECOY`| ₹3,500.00 | *None (Decoy rejected by Relational)*| N/A | `ESCALATE` | `ESCALATE` | ✅ PASS |
| **VAR-010** | `UNEXPLAINED` | ₹15,000.00 | *None (No candidate deductions)* | N/A | `ESCALATE` | `ESCALATE` | ✅ PASS |

---

## 6. Key Safety & Architectural Insights

1. **Zero False Closures (0.0% False Closure Rate):**  
   The system never closes an unresolved case on amount coincidence alone. When evidence belongs to an unrelated payment (`VAR-009`) or occurred after cutoff (`VAR-008`), it strictly escalates.
2. **Deterministic Partial Attribution:**  
   In `VAR-003`, the investigator attributes the valid ₹3,000 refund and explicitly retains the residual ₹2,000 variance as unexplained, refusing to falsely close the full ₹5,000 case.
3. **Multi-Event Subset Sum Attribution:**  
   In `VAR-004`, the investigator evaluates subset combinations of candidate deductions and successfully identifies the composite explanation (-₹700 refund + -₹300 adjustment = -₹1,000).
4. **Sub-Millisecond Investigation Latency:**  
   Average investigation latency is **0.26 ms**, enabling real-time reconciliation at enterprise scale.
5. **Counterfactual Validation:**  
   Every verified hypothesis includes counterfactual residual analysis, verifying that excluding any constituent evidence item restores the unexplained deficit.

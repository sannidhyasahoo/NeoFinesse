# NeoFinesse

> **Evidence-Constrained Financial Root Cause Analysis for Settlement Variances**

NeoFinesse is an experimental AI finance controller designed to investigate **settlement variances** by connecting financial events across payments, UPI transactions, refunds, disputes, adjustments, settlements, and bank transactions.

Instead of treating financial records as isolated rows, NeoFinesse builds a **relationship-aware financial evidence graph**, retrieves relevant evidence, applies deterministic financial and temporal constraints, and produces an auditable resolution or escalates the case when the available evidence is insufficient.

The core principle is:

> **Plausible ≠ Proven.**

A transaction that looks like it explains a variance is not considered a valid root cause unless its identity, relationship, timing, financial effect, and provenance can be verified.

---

## Table of Contents

* [1. Problem](#1-problem)
* [2. Scope](#2-scope)
* [3. Core Idea](#3-core-idea)
* [4. System Mental Model](#4-system-mental-model)
* [5. Architecture](#5-architecture)
* [6. Design Philosophy](#6-design-philosophy)
* [7. Investigation Flow](#7-investigation-flow)
* [8. Financial Data Model](#8-financial-data-model)
* [9. Entity Lifecycles](#9-entity-lifecycles)
* [10. Financial Provenance](#10-financial-provenance)
* [11. Reconciliation Engine](#11-reconciliation-engine)
* [12. Evidence Hierarchy](#12-evidence-hierarchy)
* [13. Retrieval Layer](#13-retrieval-layer)
* [14. Retrieval Strategies](#14-retrieval-strategies)
* [15. Phase 4 Benchmark](#15-phase-4-benchmark)
* [16. Synthetic Dataset](#16-synthetic-dataset)
* [17. Failure Scenarios](#17-failure-scenarios)
* [18. Ground Truth](#18-ground-truth)
* [19. Metrics](#19-metrics)
* [20. Current Benchmark Results](#20-current-benchmark-results)
* [21. Auditability](#21-auditability)
* [22. Repository Structure](#22-repository-structure)
* [23. Technology Stack](#23-technology-stack)
* [24. Running the Project](#24-running-the-project)
* [25. Test Suite](#25-test-suite)
* [26. Current Status](#26-current-status)
* [27. What Has Been Proven](#27-what-has-been-proven)
* [28. Current Limitations](#28-current-limitations)
* [29. Important Non-Goals](#29-important-non-goals)
* [30. Phase 5 — Next Step](#30-phase-5--next-step)
* [31. Development Principles](#31-development-principles)
* [32. Reproducibility](#32-reproducibility)
* [33. Final Product Vision](#33-final-product-vision)

---

# 1. Problem

Financial operations frequently require determining why an expected settlement amount differs from the amount actually credited to a bank account.

A simple reconciliation can identify:

```text
Expected Settlement
        ≠
Actual Bank Credit
```

But that only identifies the **variance**.

The harder question is:

> **Which financial event actually caused the variance?**

Possible causes include:

* refunds
* chargebacks
* disputes
* adjustments
* settlement timing
* UPI state transitions
* delayed bank credits
* partial financial events
* unrelated transactions that happen to have the same amount
* events belonging to another settlement
* genuinely unexplained differences

The challenge is therefore not just matching records.

It is **root-cause investigation under financial constraints**.

---

# 2. Scope

NeoFinesse currently focuses on:

## Primary scope

**Settlement Variance Investigation**

Given:

```text
Expected settlement amount
+
Actual bank credit
```

NeoFinesse investigates the resulting variance and determines whether it can be explained by valid financial events.

## Included

* Payment records
* UPI transactions
* UPI event histories
* Refunds
* Disputes / chargebacks
* Adjustments
* Settlement records
* Settlement lines
* Bank transactions
* Cross-entity relationships
* Temporal constraints
* Monetary consistency
* Source provenance
* Evidence retrieval
* Root-cause verification
* Honest escalation

## Explicitly excluded

* Cash forecasting
* EMI attribution
* Production payment processing
* Actual merchant financial accounts
* Live payment execution
* Autonomous money movement

NeoFinesse is currently a **student hackathon proof-of-concept**, not a production financial system.

---

# 3. Core Idea

Traditional reconciliation asks:

> "Can these records be matched?"

NeoFinesse asks:

> "Can this financial event be proven to explain this variance?"

This creates a distinction between:

```text
Candidate
   ↓
Plausible Explanation
   ↓
Verified Explanation
```

Only the final category can close a case.

A candidate may have:

* matching amount
* matching date
* matching merchant
* matching payment

and still be wrong.

For example:

```text
Settlement variance = ₹4,000

Refund A = ₹4,000
Refund B = ₹4,000
```

If Refund A belongs to the settlement and Refund B belongs to another payment, amount matching alone is insufficient.

NeoFinesse therefore combines:

```text
Monetary consistency
+
Entity relationship
+
Temporal consistency
+
State validity
+
Settlement relevance
+
Source provenance
```

---

# 4. System Mental Model

The complete system follows:

```text
INGEST
   ↓
NORMALIZE
   ↓
BUILD FINANCIAL RELATIONSHIPS
   ↓
RECONCILE
   ↓
IDENTIFY VARIANCE
   ↓
RETRIEVE EVIDENCE
   ↓
FORM HYPOTHESES
   ↓
VERIFY HYPOTHESES
   ↓
      ┌───────────────┐
      │               │
      ▼               ▼
   RESOLVED        ESCALATE
      │               │
      └───────┬───────┘
              ▼
         AUDIT TRAIL
```

The current implementation covers the pipeline through **evidence retrieval**.

The next major phase adds the actual AI-assisted investigator.

---

# 5. Architecture

Current conceptual architecture:

```text
┌─────────────────────────────────────────────────────────────┐
│                    SYNTHETIC FINANCIAL WORLD                │
│                                                             │
│ Payments / UPI / Refunds / Disputes / Adjustments           │
│ Settlements / Settlement Lines / Bank Transactions          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    SOURCE REGISTRY                           │
│                                                             │
│ File → Sheet → Row → Cell → Hash → Version                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION                                │
│                                                             │
│ Parse → Validate → Normalize → Preserve Provenance          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               FINANCIAL PROVENANCE GRAPH                    │
│                                                             │
│ Payment → UPI → UPI Events                                  │
│ Payment → Refund                                            │
│ Payment → Dispute                                           │
│ Payment → SettlementLine → Settlement → UTR → Bank          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                DETERMINISTIC RECONCILIATION                 │
│                                                             │
│ Expected vs Actual                                          │
│ Settlement composition                                      │
│ Bank UTR matching                                            │
│ Variance classification                                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
                  MATCHED             VARIANCE
                     │                   │
                     ▼                   ▼
                   CLOSE          EVIDENCE RETRIEVAL
                                         │
                                         ▼
                                Relationship / Temporal /
                                UPI State Evidence
                                         │
                                         ▼
                                ┌──────────────────┐
                                │   PHASE 5        │
                                │                  │
                                │ Hypothesis       │
                                │ Investigation    │
                                │ Verification     │
                                │ AI reasoning     │
                                └────────┬─────────┘
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                           RESOLVED             ESCALATE
                              │                     │
                              └──────────┬──────────┘
                                         ▼
                                  AUDIT / PROOF REPORT
```

---

# 6. Design Philosophy

## 6.1 Deterministic facts stay deterministic

The system should never ask an LLM to decide:

* whether ₹5,000 + ₹3,000 = ₹8,000
* whether two IDs are equal
* whether an event happened before a cutoff
* whether a UTR matches
* whether a settlement line belongs to a settlement
* whether a financial effect is mathematically valid

These are deterministic operations.

---

## 6.2 AI handles ambiguity

AI is intended for:

* hypothesis generation
* hypothesis ranking
* ambiguous evidence interpretation
* conflicting evidence analysis
* natural-language explanation
* investigation planning

AI does not become the source of truth.

---

## 6.3 Evidence must be traceable

Every important claim must be backed by evidence that can be traced to:

```text
Entity
→ Source ID
→ File
→ Sheet
→ Row
→ Column / Cell
→ Hash
```

---

## 6.4 No forced closure

If the available evidence cannot prove the cause:

```text
ESCALATE
```

is a valid result.

A finance controller that confidently invents explanations is worse than one that honestly reports an unresolved exception.

---

# 7. Investigation Flow

A settlement variance investigation conceptually follows:

```text
1. Identify settlement
        ↓
2. Calculate expected settlement amount
        ↓
3. Match settlement to bank transaction
        ↓
4. Calculate variance
        ↓
5. Determine investigation task
        ↓
6. Retrieve relevant evidence
        ↓
7. Generate candidate explanations
        ↓
8. Check relationships
        ↓
9. Check timestamps
        ↓
10. Check financial effects
        ↓
11. Check entity state
        ↓
12. Verify complete explanation
        ↓
13. Resolve or escalate
        ↓
14. Produce audit trail
```

---

# 8. Financial Data Model

NeoFinesse normalizes provider-specific data into common financial entities.

Core entities:

```text
Payment
Refund
Dispute / Chargeback
Adjustment
UPITransaction
UPIEvent
Settlement
SettlementLine
BankTransaction
VarianceCase
SourceRegistry
```

---

## Payment

Represents the original payment transaction.

Important fields include:

```text
id
provider_id
amount
currency
status
created_at
captured_at
provenance
```

Normalized payment states:

```text
INITIATED
PENDING
CAPTURED
FAILED
REFUNDED
```

---

## Refund

Represents money returned from a payment.

Normalized states:

```text
PENDING
PROCESSED
FAILED
```

A processed refund can create a negative settlement-side financial effect.

---

## Dispute / Chargeback

Represents a dispute or chargeback affecting settlement.

Provider-specific lifecycle information is normalized while preserving the original provider status.

Possible states include:

```text
OPEN
UNDER_REVIEW
WON
LOST
CLOSED
```

Financial effects are represented separately from lifecycle state.

---

## Adjustment

Represents a signed financial adjustment.

Examples:

```text
positive adjustment
negative adjustment
```

Adjustments are terminal financial events in the current synthetic model.

---

## Settlement

Represents the provider-side settlement batch.

Important fields:

```text
id
utr
created_at
settled_at
status
expected_amount
actual_bank_amount
```

Bank-side settlement states are modeled as:

```text
PENDING_BANK_CREDIT
BANK_CREDITED
BANK_REJECTED
```

---

## SettlementLine

SettlementLine is the canonical membership relationship between a settlement and an underlying financial event.

Conceptually:

```text
Settlement
    ↓
SettlementLine
    ↓
Payment / Refund / Adjustment / Dispute
```

Expected settlement amount is computed from signed settlement-line amounts.

---

## BankTransaction

Represents the actual bank-side transaction.

The primary settlement-to-bank identifier is:

```text
UTR
```

Exact UTR matches are treated as strong join evidence.

---

# 9. Entity Lifecycles

## Payment

```text
INITIATED
    ↓
PENDING
    ↓
CAPTURED
```

Possible failure/refund branches exist depending on provider lifecycle.

---

## Refund

```text
PENDING
   ↓
PROCESSED
```

or:

```text
PENDING
   ↓
FAILED
```

---

## Settlement

```text
CREATED
   ↓
PROCESSED
   ↓
PENDING_BANK_CREDIT
   ↓
BANK_CREDITED
```

A settlement can therefore be provider-processed while bank credit is delayed.

---

## UPI

NeoFinesse models UPI as an **event history**, not merely a final status.

Normal flow:

```text
INITIATED
   ↓
PENDING
   ↓
SUCCESS
```

Failure flow:

```text
INITIATED
   ↓
PENDING
   ↓
FAILED
```

Special investigations can include:

```text
FAILED
   ↓
late SUCCESS
```

or:

```text
FAILED
   ↓
DEBIT
   ↓
REVERSAL
```

The final financial effect must be determined from the event history.

---

# 10. Financial Provenance

Provenance is a first-class part of the data model.

Every ingested record preserves its source.

Example:

```json
{
  "source_id": "SRC-004",
  "file_name": "refunds.xlsx",
  "file_hash": "...",
  "version": 1,
  "sheet": "Refunds",
  "row": 193,
  "cell_range": "A193:J193",
  "relevant_cells": [
    "B193",
    "D193",
    "G193"
  ]
}
```

This allows an investigation result to say:

```text
₹4,000 refund explains variance

Source:
refunds.xlsx
Sheet: Refunds
Row: 193
Cells: B193, D193, G193
```

rather than simply:

```text
Refund ID = REF-123
```

---

## Dual hashing

NeoFinesse uses:

```text
Source file hash
+
Record hash
```

The file hash identifies the source version.

The record hash supports tamper detection at record level.

This prevents an investigation from silently becoming disconnected from the original source data.

---

# 11. Reconciliation Engine

The deterministic reconciliation layer is implemented in:

```text
src/neofinesse/reconciliation/
```

Pipeline:

```text
IngestedDataset
      ↓
BankJoinEngine
      ↓
UPIStateReconstructor
      ↓
SettlementCompositionReconciler
      ↓
CandidateRetriever
      ↓
TemporalConstraintFilter
      ↓
MultiConstraintAttributionSolver
      ↓
ReconciliationClassifier
      ↓
AuditRecordBuilder
```

---

## Bank matching

The primary join is:

```text
Settlement.UTR
        =
BankTransaction.UTR
```

Possible outcomes:

```text
EXACT_UTR_MATCH
DELAYED_BANK_CREDIT
MISSING_BANK_TRANSACTION
AMOUNT_MISMATCH
AMBIGUOUS_MATCH
```

---

## Settlement amount

The expected amount is computed as:

```text
Expected Settlement
=
Σ signed SettlementLine.net_amount
```

Settlement lines are not double-counted.

---

## Temporal constraint

Candidate events must satisfy the configured investigation window.

The current synthetic configuration uses a settlement-relative time buffer.

A candidate outside the permitted window is rejected for attribution even if its amount matches.

---

## Attribution solver

The solver applies constraints including:

1. settlement relevance
2. explicit entity relationship
3. temporal validity
4. non-zero financial effect
5. monetary consistency

For multiple events, a subset of candidate financial effects can be checked against the target variance.

Example:

```text
Variance = ₹1,000

Refund = ₹700
Adjustment = ₹300

700 + 300 = 1,000
```

This can constitute a complete financial explanation if all other constraints pass.

---

# 12. Evidence Hierarchy

NeoFinesse uses progressively stronger evidence.

| Level | Evidence                                         |
| ----- | ------------------------------------------------ |
| L0    | Amount coincidence                               |
| L1    | Entity relationship                              |
| L2    | Settlement association                           |
| L3    | Temporal consistency                             |
| L4    | Financially complete exact attribution           |
| L5    | Multi-source verified attribution + bank linkage |

Important:

**L0 is not proof.**

An exact amount match alone cannot close a case.

L4 requires more than amount equality:

```text
amount
+
entity relationship
+
settlement relevance
+
temporal validity
+
financial completeness
```

L5 additionally establishes the full provenance chain across relevant sources.

---

# 13. Retrieval Layer

Phase 4 investigates a specific question:

> **Given an unexplained variance, how effectively can NeoFinesse retrieve the correct evidence before using AI reasoning?**

The retrieval layer is intentionally separate from the final verification layer.

Retrieval answers:

```text
"What evidence might matter?"
```

Verification answers:

```text
"Does this evidence actually prove the cause?"
```

Ground truth is available only to the evaluator.

Retrievers never use ground truth to find their candidates.

---

# 14. Retrieval Strategies

Six strategies are currently benchmarked.

---

## 14.1 DIRECT_ID

Uses explicit identifiers.

Examples:

```text
payment_id
refund_id
settlement_id
UTR
```

Strength:

* precise identity lookup

Weakness:

* may retrieve many records connected to the identifier
* does not necessarily establish causal relevance

---

## 14.2 ATTRIBUTE

Uses attributes such as:

```text
amount
date
status
provider
event type
```

Example:

```text
variance = ₹4,000
```

Search for:

```text
records with amount = ₹4,000
```

Strength:

* extremely cheap
* useful candidate generation

Weakness:

* vulnerable to same-amount decoys
* cannot naturally explain multi-event combinations

---

## 14.3 RELATIONSHIP

Uses explicit financial relationships.

Example:

```text
Settlement
    ↓
SettlementLine
    ↓
Payment
    ↓
Refund
```

Strength:

* eliminates many unrelated records

Weakness:

* relationship alone does not guarantee temporal validity

---

## 14.4 TYPED_PROVENANCE

Extends relationship retrieval with typed financial entities and source provenance.

It preserves:

```text
entity type
relationship
source identity
source location
```

The current benchmark shows that its candidate set is similar to relationship retrieval.

Therefore, at the current stage its primary demonstrated advantage is **auditability/provenance**, rather than a large additional retrieval gain.

---

## 14.5 TEMPORAL_RELATIONSHIP

Combines:

```text
relationship
+
temporal constraint
```

This is currently the strongest settlement-RCA retrieval strategy on the synthetic benchmark.

It can reject cases such as:

```text
₹4,000 refund
```

that belongs to the correct type and may even be related to the merchant, but occurred outside the valid investigation window.

---

## 14.6 UPI_EVENT

Specialized retrieval for UPI lifecycle investigation.

Instead of treating UPI as a single status, NeoFinesse retrieves the complete transaction history:

```text
UPITransaction
    ↓
INITIATED
    ↓
PENDING
    ↓
FAILED
    ↓
SUCCESS
```

or:

```text
UPITransaction
    ↓
FAILED
    ↓
DEBIT
    ↓
REVERSAL
```

The strategy reconstructs the lifecycle and determines the resulting financial effect.

UPI event retrieval is evaluated only against UPI-specific investigation cases.

---

# 15. Phase 4 Benchmark

Phase 4 runs:

```text
10 scenarios
×
6 retrieval strategies
=
60 experiments
```

The benchmark explicitly distinguishes:

```text
APPLICABLE
NOT APPLICABLE
```

This prevents a settlement-RCA retrieval strategy from being penalized for not being designed to investigate a UPI lifecycle case.

---

# 16. Synthetic Dataset

NeoFinesse currently uses deterministic synthetic financial data.

The generator supports:

* configurable dataset generation
* deterministic seeds
* CSV export
* Excel export
* internally consistent relationships
* intentionally injected failure scenarios
* isolated ground truth

The default benchmark uses:

```text
seed = 42
```

---

## Dataset entities

The generated world contains records representing:

```text
Payments
UPI Transactions
UPI Events
Refunds
Disputes
Adjustments
Settlements
Settlement Lines
Bank Transactions
```

---

# 17. Failure Scenarios

The benchmark contains ten intentionally designed scenarios.

| ID      | Scenario                   | Intended result      |
| ------- | -------------------------- | -------------------- |
| VAR-001 | Refund variance            | RESOLVED             |
| VAR-002 | Same-amount decoy          | RESOLVED             |
| VAR-003 | Partial explanation        | PARTIALLY_RESOLVED   |
| VAR-004 | Multiple-event explanation | RESOLVED             |
| VAR-005 | UPI late success           | RESOLVED             |
| VAR-006 | UPI debit + reversal       | RESOLVED             |
| VAR-007 | Delayed bank credit        | VALID_DELAYED_CREDIT |
| VAR-008 | Wrong-date decoy           | ESCALATE             |
| VAR-009 | Wrong-payment decoy        | ESCALATE             |
| VAR-010 | Completely unexplained     | ESCALATE             |

These scenarios are intentionally designed to expose weaknesses in simplistic matching systems.

---

## VAR-001 — Refund Variance

A processed refund explains the settlement variance.

Tests:

```text
basic relationship retrieval
monetary consistency
provenance
```

---

## VAR-002 — Same Amount Decoy

A genuine refund and an unrelated refund have the same amount.

Tests whether:

```text
amount matching
```

can be distinguished from:

```text
entity relationship
```

---

## VAR-003 — Partial Explanation

Example:

```text
Variance = ₹5,000

Valid refund = ₹3,000

Unexplained = ₹2,000
```

The system must not falsely close the full ₹5,000 variance.

Expected result:

```text
PARTIALLY_RESOLVED
```

---

## VAR-004 — Multiple Event Explanation

Example:

```text
Refund      = ₹700
Adjustment  = ₹300
-------------------
Variance    = ₹1,000
```

Tests multi-event financial attribution.

---

## VAR-005 — UPI Late Success

A UPI transaction initially fails but receives a later successful authorization/callback.

Tests whether the system treats UPI as an event sequence rather than relying only on the first observed status.

---

## VAR-006 — UPI Debit + Reversal

Example lifecycle:

```text
FAILED
 ↓
DEBIT OBSERVED
 ↓
REVERSAL
```

The final net financial effect should be zero when the reversal fully offsets the debit.

Tests:

* UPI state reconstruction
* debit/reversal reasoning
* event chronology
* financial effect calculation

---

## VAR-007 — Delayed Bank Credit

A provider settlement has been processed, but bank credit occurs later within the permitted timing window.

The system should distinguish:

```text
missing funds
```

from:

```text
delayed but valid bank settlement
```

---

## VAR-008 — Wrong-Date Decoy

A candidate event has the right amount but occurs outside the valid investigation window.

Tests temporal reasoning.

Expected:

```text
ESCALATE
```

---

## VAR-009 — Wrong-Payment Decoy

A candidate financial event has a plausible amount but belongs to another payment/settlement relationship.

Tests relationship-aware retrieval.

Expected:

```text
ESCALATE
```

---

## VAR-010 — Completely Unexplained

A variance is intentionally introduced without a valid causal event.

The correct behavior is:

```text
ESCALATE
```

not hallucinate a cause.

---

# 18. Ground Truth

Ground truth is isolated from the runtime investigation pipeline.

It contains information such as:

```text
case
settlement
scenario
expected variance
true causes
decoys
explained amount
unexplained amount
expected outcome
```

Ground truth is used by:

```text
evaluation
benchmarking
testing
```

It is never exposed to retrieval logic as an oracle.

This prevents data leakage between the investigator and the evaluator.

---

# 19. Metrics

Phase 4 measures multiple dimensions.

## Evidence Recall

```text
true causal evidence retrieved
-------------------------------- × 100
total true causal evidence
```

If no true causes exist:

```text
N/A
```

rather than an artificial 100%.

---

## Candidate Precision

```text
true causal candidates
---------------------- × 100
all retrieved candidates
```

If no candidates and no causes exist:

```text
N/A
```

If causes were expected but nothing was retrieved:

```text
0%
```

---

## Decoy Rejection

```text
rejected known decoys
--------------------- × 100
known decoys
```

If no decoys exist:

```text
N/A
```

---

## Provenance Coverage

```text
provenance-complete candidates
------------------------------ × 100
all candidates
```

---

## Latency

Tracked as:

```text
average
median
maximum
```

Latency is measured only for retrieval execution.

---

## Applicability

Every benchmark result records whether the strategy is applicable to the investigation task.

This prevents invalid cross-task comparisons.

---

# 20. Current Benchmark Results

Current Phase 4 benchmark:

```text
Total experiments = 60
```

| Strategy              | Applicable | Recall | Precision | Decoy Rejection | Provenance |
| --------------------- | ---------: | -----: | --------: | --------------: | ---------: |
| DIRECT_ID             |       8/10 | 100.0% |     14.7% |          100.0% |     100.0% |
| ATTRIBUTE             |       8/10 |  40.0% |     25.0% |            0.0% |     100.0% |
| RELATIONSHIP          |       8/10 | 100.0% |     35.7% |           66.7% |     100.0% |
| TYPED_PROVENANCE      |       8/10 | 100.0% |     35.7% |           66.7% |     100.0% |
| TEMPORAL_RELATIONSHIP |       8/10 | 100.0% |     38.5% |          100.0% |     100.0% |
| UPI_EVENT             |       2/10 | 100.0% |     50.0% |            0.0% |     100.0% |

### Interpretation

The benchmark demonstrates a progression:

```text
ATTRIBUTE
    ↓
RELATIONSHIP
    ↓
TEMPORAL_RELATIONSHIP
```

Attribute matching is vulnerable to:

* same-amount decoys
* multi-event explanations
* partial explanations

Relationship retrieval substantially improves candidate quality.

Adding temporal constraints improves decoy rejection further.

On this synthetic benchmark, `TEMPORAL_RELATIONSHIP` has the highest precision and decoy rejection among the settlement-RCA retrieval strategies while retaining full recall on applicable cases.

`UPI_EVENT` is specialized for UPI lifecycle investigation and is therefore evaluated only on the two UPI scenarios.

These results should be interpreted as **benchmark results on the current synthetic dataset**, not as production accuracy claims.

---

# 21. Auditability

Every investigation should ultimately be able to answer:

```text
What happened?
Why does the system believe it happened?
Which records support that conclusion?
Where did those records come from?
What calculations were performed?
What constraints were satisfied?
Which alternatives were rejected?
```

A future audit record should conceptually look like:

```text
CASE: VAR-002

Variance:
₹4,000

Hypothesis:
Refund REF-001 caused the variance.

Evidence:
Payment PAY-001
Refund REF-001
SettlementLine SL-001
Settlement SET-001
BankTransaction BANK-001

Relationship:
Settlement
 → SettlementLine
 → Payment
 → Refund

Temporal:
Valid

Financial:
₹4,000 refund = ₹4,000 variance

Decoy:
Refund REF-002

Reason rejected:
Same amount, but unrelated payment.

Provenance:
refunds.xlsx
Refunds!B193:G193
source hash: ...

Decision:
RESOLVED
```

The exact final audit schema will be defined during the investigation phase.

---

# 22. Repository Structure

Current repository structure:

```text
NeoFinesse/
│
├── src/
│   └── neofinesse/
│       │
│       ├── models/
│       │   ├── base.py
│       │   ├── events.py
│       │   ├── upi.py
│       │   ├── settlement.py
│       │   ├── bank.py
│       │   └── ground_truth.py
│       │
│       ├── generator/
│       │   ├── config.py
│       │   ├── scenarios.py
│       │   ├── synthetic.py
│       │   └── exporter.py
│       │
│       ├── ingestion/
│       │   ├── registry.py
│       │   ├── parser.py
│       │   ├── validator.py
│       │   ├── normalizer.py
│       │   └── pipeline.py
│       │
│       ├── reconciliation/
│       │   ├── joins.py
│       │   ├── upi_state.py
│       │   ├── candidates.py
│       │   ├── temporal.py
│       │   ├── solver.py
│       │   ├── classifier.py
│       │   ├── audit.py
│       │   ├── engine.py
│       │   └── metrics.py
│       │
│       └── retrieval/
│           ├── __init__.py
│           ├── base.py
│           ├── direct_id.py
│           ├── attribute.py
│           ├── relationship.py
│           ├── provenance.py
│           ├── temporal.py
│           ├── upi_event.py
│           ├── result.py
│           ├── evaluator.py
│           └── benchmark.py
│
├── tests/
│   ├── test_generator.py
│   ├── test_ingestion.py
│   ├── test_reconciliation.py
│   ├── test_retrieval.py
│   ├── test_scenarios.py
│   └── test_end_to_end.py
│
├── docs/
│   ├── phase4-retrieval.md
│   └── ...
│
├── experiments/
│   └── phase4/
│       ├── results.json
│       └── results.csv
│
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# 23. Technology Stack

Current implementation:

| Component       | Technology                   |
| --------------- | ---------------------------- |
| Language        | Python                       |
| Package manager | uv                           |
| Data validation | Pydantic                     |
| Testing         | pytest                       |
| Coverage        | pytest-cov                   |
| Input           | CSV / Excel                  |
| Output          | CSV / Excel / JSON           |
| AI              | Not yet part of Phase 1–4    |
| Database        | Not required for current POC |
| Graph database  | Not required for current POC |

The architecture intentionally avoids unnecessary infrastructure during the experimental phases.

---

# 24. Running the Project

## Install dependencies

Using `uv`:

```bash
uv sync
```

---

## Run all tests

```bash
uv run pytest -v
```

---

## Run retrieval benchmark

```bash
uv run python -m neofinesse.retrieval.benchmark
```

Results are exported to:

```text
experiments/phase4/results.json
experiments/phase4/results.csv
```

---

## Run reconciliation tests

```bash
uv run pytest tests/test_reconciliation.py -v
```

---

## Run retrieval tests

```bash
uv run pytest tests/test_retrieval.py -v
```

---

# 25. Test Suite

Current test suite:

```text
27 tests
27 passed
```

Coverage includes:

### Generator

* reproducibility
* unique IDs
* relationship consistency
* settlement-line sums
* UPI event ordering

### Ingestion

* cell coordinate conversion
* file hashing
* record hashing
* provenance preservation
* ground-truth isolation

### Reconciliation

* UTR matching
* UPI state reconstruction
* temporal filtering
* end-to-end benchmark

### Retrieval

* N/A metric semantics
* precision edge cases
* decoy metrics
* aggregate metrics
* UPI late success
* UPI debit/reversal
* amount-only fallback confidence
* applicability
* complete benchmark matrix

### Scenarios

* all ten failure scenarios
* ground-truth outcomes

---

# 26. Current Status

## Phase 0 — Domain Reconnaissance

**Status: COMPLETE**

Defined:

* problem
* scope
* provider concepts
* settlement reconciliation model
* failure taxonomy
* evidence hierarchy
* architecture
* metrics

---

## Phase 1 — Financial Event + Provenance Model

**Status: COMPLETE / FROZEN**

Defined:

* normalized entities
* lifecycle states
* UPI event history
* financial effects
* relationships
* provenance
* source registry
* design decisions

---

## Phase 2 — Synthetic World + Ground Truth

**Status: COMPLETE / FROZEN**

Implemented:

* deterministic generator
* ten investigation scenarios
* CSV/Excel export
* isolated ground truth
* ingestion
* validation
* normalization
* provenance

---

## Phase 3 — Deterministic Reconciliation

**Status: COMPLETE / FROZEN**

Implemented:

* bank UTR matching
* settlement composition
* candidate generation
* temporal filtering
* UPI state reconstruction
* multi-event attribution
* reconciliation classification
* audit records

---

## Phase 4 — Evidence Retrieval Benchmark

**Status: COMPLETE / FROZEN**

Implemented:

* six retrieval strategies
* task applicability
* evidence metrics
* decoy evaluation
* provenance coverage
* latency measurement
* UPI-specific retrieval
* reproducible benchmark
* experiment exports

Current benchmark:

```text
60 experiments
27 automated tests
27 passing
```

---

# 27. What Has Been Proven

The current POC has established that:

### 1. Amount matching is insufficient

Same-amount decoys can defeat attribute-only retrieval.

---

### 2. Relationships improve evidence quality

Following explicit financial relationships removes unrelated records that may otherwise look plausible.

---

### 3. Temporal constraints matter

A related event can still be invalid if it occurs outside the relevant investigation window.

---

### 4. Multi-event explanations are necessary

A variance may require multiple financial events to explain it.

---

### 5. UPI needs event-level reasoning

A single final UPI status can hide important financial history.

The event sequence can determine whether:

```text
failed → late success
```

or:

```text
failed → debit → reversal
```

actually occurred.

---

### 6. Provenance should exist throughout the pipeline

Evidence is significantly more useful when it can be traced to the exact source record.

---

### 7. Honest escalation is necessary

Some synthetic cases intentionally have no valid explanation.

The correct behavior is to escalate rather than force a cause.

---

# 28. Current Limitations

NeoFinesse is currently a synthetic-data research POC.

Important limitations:

## Dataset size

The current benchmark contains only ten designed scenarios.

Therefore:

```text
100% recall
```

does not mean production-level 100% recall.

---

## Synthetic data

The generated data does not represent the full messiness of real merchant financial systems.

Real systems may contain:

* missing identifiers
* inconsistent schemas
* duplicate records
* malformed timestamps
* provider-specific semantics
* partial exports
* timezone issues
* manual adjustments
* delayed reporting
* inconsistent statuses

---

## Retrieval vs reasoning

Phase 4 measures:

```text
evidence retrieval
```

It does not yet provide the final AI-powered investigation layer.

---

## Provider differences

The current architecture is provider-aware and provider-agnostic at different layers, but real provider schemas and state semantics will require additional adapters.

---

# 29. Important Non-Goals

NeoFinesse is intentionally **not** trying to:

### Build a generic chatbot

The system is an investigation engine with a structured financial backend.

---

### Replace deterministic financial logic with an LLM

Financial calculations remain deterministic.

---

### Build a vector database simply because the project contains AI

The evidence relationships are structured and typed.

Semantic retrieval should only be introduced if experiments show that it provides value.

---

### Make every component an autonomous agent

Agents are not automatically useful.

The architecture should use AI where uncertainty actually exists.

---

### Hide uncertainty

The system must be able to say:

```text
INSUFFICIENT EVIDENCE
```

---

# 30. Phase 5 — Next Step

Phase 5 is the major transition from:

```text
retrieval system
```

to:

```text
financial investigator
```

The architecture should **not** become:

```text
Rules
  ↓
LLM fallback
```

Instead, AI should operate as an investigator under deterministic constraints.

Target architecture:

```text
                    VARIANCE
                       │
                       ▼
              Evidence Retrieval
                       │
                       ▼
                 Evidence Graph
                       │
                       ▼
              Hypothesis Generation
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Refund       Adjustment   Chargeback
      hypothesis    hypothesis    hypothesis
          │            │            │
          └────────────┼────────────┘
                       ▼
              Constraint Verification
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      Amount         Temporal      Relationship
      Check           Check           Check
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 Evidence Scoring
                       │
              ┌────────┴────────┐
              ▼                 ▼
            PROVEN           REJECTED
              │                 │
              └────────┬────────┘
                       ▼
                  FINAL VERIFIER
                       │
                ┌──────┴──────┐
                ▼             ▼
             RESOLVE        ESCALATE
```

---

## Phase 5 objectives

The investigator should be able to:

1. inspect retrieved evidence
2. generate competing hypotheses
3. rank hypotheses
4. retrieve additional evidence when necessary
5. reason over multiple records
6. identify conflicting evidence
7. calculate candidate financial effects
8. test temporal consistency
9. test relationship consistency
10. test UPI state consistency
11. reject unsupported hypotheses
12. produce a final explanation
13. identify unresolved amounts
14. escalate when proof is insufficient

---

## AI boundary

The LLM may propose:

```text
Hypothesis A:
Refund caused variance.

Hypothesis B:
Adjustment + refund caused variance.

Hypothesis C:
Bank settlement was delayed.
```

But the deterministic verifier decides whether each hypothesis actually satisfies the financial constraints.

The LLM cannot override:

```text
amount mismatch
invalid relationship
invalid timestamp
invalid UPI state
missing provenance
```

---

# 31. Development Principles

Every future feature should follow these principles.

## Principle 1 — Evidence before explanation

Never generate an explanation first and search for evidence afterward.

---

## Principle 2 — Relationships before semantics

When structured relationships exist, use them before semantic similarity.

---

## Principle 3 — Constraints before confidence

A model saying:

```text
confidence = 0.97
```

does not prove a financial event occurred.

---

## Principle 4 — Preserve provenance

Every piece of evidence must remain traceable.

---

## Principle 5 — Separate observed from inferred state

Example:

```text
Provider status:
FAILED

Observed event:
debit

Observed event:
reversal

Derived conclusion:
DEBIT_REVERSED
```

The system must distinguish source facts from system-derived conclusions.

---

## Principle 6 — Never assume missing evidence

If a reversal record is missing:

```text
FAILED + DEBIT
```

does not automatically imply:

```text
REVERSAL
```

The correct result may be:

```text
UNKNOWN
```

and therefore:

```text
ESCALATE
```

---

## Principle 7 — Measure every architectural improvement

Whenever a new retrieval or reasoning mechanism is introduced, compare it against the existing baseline.

Metrics should include:

```text
Recall
Precision
Decoy rejection
False closure
Exception rate
Latency
```

---

## Principle 8 — Adversarial cases matter

Future benchmarks should include:

```text
same amount
wrong date
wrong payment
wrong settlement
partial explanation
multiple explanations
missing evidence
conflicting evidence
duplicate records
zero-effect events
```

---

# 32. Reproducibility

The synthetic benchmark is deterministic.

Default seed:

```text
42
```

The benchmark should be reproducible with:

```bash
uv run python -m neofinesse.retrieval.benchmark
```

Experiment outputs are stored in:

```text
experiments/phase4/
```

The benchmark should not modify the ground truth during execution.

---

# 33. Final Product Vision

The final NeoFinesse system should answer a finance-operations question like:

> **"Why is this settlement ₹5,000 short?"**

with something substantially stronger than:

> "I found a ₹5,000 refund."

Instead:

```text
Settlement SET-123
Expected: ₹95,000
Bank Credit: ₹90,000
Variance: -₹5,000

Investigation:

₹3,000 refund
    ✓ belongs to settlement
    ✓ belongs to payment PAY-123
    ✓ occurred within valid window
    ✓ processed successfully
    ✓ provenance verified

₹2,000 adjustment
    ✓ belongs to settlement
    ✓ signed debit
    ✓ occurred within valid window
    ✓ provenance verified

Explained:
₹5,000 / ₹5,000

Alternative candidate:
₹5,000 refund REF-999
    ✗ belongs to different payment
    ✗ rejected

Conclusion:
RESOLVED

Proof:
Settlement
 → SettlementLine
 → Payment
 → Refund
 → Source record

Audit trail:
Available
```

For an unresolved case:

```text
Settlement variance:
₹5,000

Evidence found:
₹3,000 valid refund

Remaining:
₹2,000 unexplained

No valid evidence found for remaining ₹2,000.

Conclusion:
PARTIALLY_RESOLVED → ESCALATE
```

And for a completely unexplained case:

```text
Variance:
₹15,000

Valid causal evidence:
None

Candidate explanations:
Rejected

Conclusion:
UNRESOLVED

Reason:
Insufficient evidence to attribute variance.

Action:
Escalate to finance operations.
```

That is the intended end state of NeoFinesse:

> **A finance investigator that does not merely find plausible records, but constructs, verifies, and proves financial explanations — while knowing when it cannot prove one.**

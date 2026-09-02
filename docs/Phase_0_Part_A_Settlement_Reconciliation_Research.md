# Phase 0 — Part A: Settlement Reconciliation & Variance Investigation

**Project:** NeoFinX (AI Finance Controller — Razorpay Buildathon 2026)  
**Core Problem:** Settlement Variance Investigation (Reconciling Financial Events → Settlement Batches → Bank Credits)

---

## 1. Core Problem Definition & Scope

| Aspect | Specification |
|---|---|
| **Core Question** | When actual settled funds differ from expected amounts, which financial events provably caused the variance versus merely matching by coincidence? |
| **In Scope** | Settlement reconciliation, multi-event variance investigation, evidence-based root cause analysis, bank-credit timing verification. |
| **Out of Scope** | Cash-flow forecasting, EMI attribution, generic ledger/tax accounting, autonomous fund movement. |
| **Primary Principle** | **Plausible ≠ Proven.** A matching amount (e.g., ₹2,000 refund) is only a candidate until linked by identifier, status, lifecycle timing, and settlement batch inclusion. |

---

## 2. Multi-Stage Reconciliation & Identifier Chain

### Reconciliation Layers

| Layer | Question Answered | Primary Source / Artifact |
|---|---|---|
| **Transaction Reconciliation** | Did the transaction succeed and match internal order records? | Transaction reports, payment gateway logs |
| **Settlement Reconciliation** | Which transaction/event batch was settled, and what deductions were applied? | Settlement Recon reports, Settlement webhooks |
| **Bank / Account Reconciliation** | Did the net settlement amount credit the bank account with matching UTR? | Bank statements, account balance feeds |

### Identifier Linkage

```
[ Financial Events ] (Payment ID, Refund ARN, Dispute ID)
        │
        ▼ (Batch ID / Settlement ID)
[ Settlement Batch ] (Net Settlement Amount, Fees, Taxes, Adjustments)
        │
        ▼ (UTR / Bank Reference Number)
[ Bank Credit Record ] (Credit Amount, Value Date, Bank Statement Line)
```

---

## 3. Provider Data Sources & Field Schemas

### Razorpay

| Interface | Key Fields / Data Points | Purpose |
|---|---|---|
| **Settlement Dashboard / Details** | `settlement_id`, `payment_amount`, `adjustments`, `tax`, `fees`, `transfers`, `refunds`, `amount_settled` | Settlement breakdown & timeline tracking |
| **Settlement Recon API** | `payment_id`, `refund_id`, `transfer_id`, `adjustment_id`, `settled_at`, `amount` | Programmatic transaction-to-settlement mapping |
| **Settlement Webhook (`settlement.processed`)** | `entity.id`, `amount`, `status`, `fees`, `tax`, `utr` (e.g. `AXISCN1153863727`), `created_at` | Event-driven trigger indicating transfer initiation (not bank credit) |
| **Export Formats** | CSV, XLS, XLSX | Batch reporting |

### Cashfree

| Report / Component | Documented Fields | Key Utility |
|---|---|---|
| **Settlement Summary** | `Settlement ID`, `Total Txn Amount`, `Settlement Amount`, `Adjustment`, `Net Settlement Amount`, `UTR No.`, `Status`, `Settlement Charge`, `Settlement Tax`, `From`, `Till` | Batch-level reconciliation against bank statement |
| **Event-Level Detail** | `Event ID`, `Event Type`, `Sale Type` (`CREDIT`/`DEBIT`), `Event Amount`, `Event Settlement Amount`, `Event Time`, `Processed On`, `Settlement Date`, `UTR`, `Refund ARN`, `Adjustment Remarks`, `Merchant Reference ID`, `Txn Service Charge`, `Txn GST` | Fine-grained transaction/event causality attribution |
| **Documented Event Types** | `PAYMENT`, `REFUND`, `CHARGEBACK`, `CHARGEBACK_REVERSE`, `DISPUTE`, `DISPUTE_REVERSE`, `RISK`, `RISK_REVERSE`, `OTHER_ADJUSTMENT` | Event state & reversal tracking |

### Airwallex & Stripe

| Provider | Documented Reports | Key Fields / Concept |
|---|---|---|
| **Airwallex** | Settlement Report, Transaction Recon Report, Balance Activity Report | `Batch ID`, `Transaction ID`, `Financial Transaction Type` (Payment, Dispute, Refund Reversal, Fee, Reserve Hold/Release), `Exchange Rate`, `Net Amount` |
| **Stripe** | Payout Reconciliation Report | Reconciles bank payout amounts against aggregated payment/refund/fee batches |

---

## 4. Settlement Component Formula

```
Net Settlement = Gross Payments - (Fees + Taxes) - Refunds - Chargebacks - Hold Adjustments + Reversals
```

*Note: Component signs and timing cycles depend on provider batching schedules.*

---

## 5. Documented Exception & Failure Taxonomy

| Category | Exception / Event Type | Documented Mechanism | System Handling |
|---|---|---|---|
| **Deduction Events** | Refund | Deducted from settlement balance; may trigger partial settlement if funds insufficient. | Verify refund ARN, execution timestamp, and batch inclusion. |
| **Deduction Events** | Chargeback / Dispute | Disputed amount debited/held by processor. | Verify dispute ID, status (open/lost vs reversed). |
| **Correction Events** | Dispute/Chargeback Reversal | Reversed deduction credited back to merchant settlement. | Compute net effect of original + reversal pair. |
| **Adjustments** | Manual / Risk / Fee Adjustment | Specific debit/credit with remark/reference. | Parse adjustment type, amount, and reference remarks. |
| **Batch Dynamics** | Partial Settlement | Total eligible balance < pending deductions; surplus rolls to next batch. | Flag rollover; distinguish from lost funds. |
| **Lifecycle Timing** | Processor Settled / Bank Credit Pending | Gateway status is `processed`, but funds are in banking clearing window. | Check against expected clearance window; classify as `PENDING_BANK_CREDIT`. |
| **Failures** | Processor / Bank Settlement Failure | Beneficiary bank rejection, frozen account, invalid IFSC/account, gateway error. | Mark `SETTLEMENT_FAILED`, extract bank error reason code. |
| **Adversarial / Test** | Missing / Duplicate / Orphan Txn | Injected test cases (not native provider states). | Isolate into honest exception queue. |

---

## 6. Evidence Hierarchy for Variance Verification

To prove financial causality rather than inferring it naively:

| Level | Evidence State | Description | Action / System Status |
|:---:|---|---|---|
| **L0** | **Candidate (Amount Only)** | Event amount equals variance amount, but no relationship or batch association exists. | `UNRESOLVED` (Do not close) |
| **L1** | **Entity-Linked** | Event matches amount and references the relevant `payment_id` / `order_id`. | `CANDIDATE` (Insufficient causality) |
| **L2** | **Settlement-Associated** | Event explicitly appears within the target `settlement_id` or batch window. | `PLAUSIBLE` |
| **L3** | **Temporally Consistent** | Event `processed_on` timestamp precedes settlement cutoff; no subsequent reversal. | `HIGH_CONFIDENCE` |
| **L4** | **Financially Complete** | Single event or subset of verified events (`Σ amounts`) exactly matches variance. | `RESOLVED` |
| **L5** | **Multi-Source Verified** | Full audit chain verified: `Payment → Event → Settlement → UTR → Bank Credit`. | `FULLY_RECONCILED` |

---

## 7. System Architecture & Decision Flow

```
1. Ingest Batch Reports (Payments, Events, Settlements, Bank Feeds)
                   │
                   ▼
2. Deterministic Join Engine (Match Settlement ID ↔ UTR ↔ Bank Credit)
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    [Matched]           [Variance Detected]
         │                   │
  Mark RECONCILED            ▼
                   3. Candidate Event Retrieval (Filtered by batch, payment link, timerange)
                             │
                             ▼
                   4. Multi-Constraint Solver (Subset-sum over valid L2/L3 candidate events)
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    [Complete Match]    [Partial Match]    [No Candidate / Ambiguous]
         │                   │                   │
         │             Mark PARTIAL              │
         │             (Escalate residual)       │
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                             ▼
                   5. Selective LLM Explainer
                      • Generates auditable explanation
                      • Cites exact file, sheet, row, and column
                      • Does NOT perform raw arithmetic
                             │
                             ▼
                   6. Output Structured Audit Record & Exception Queue
```

---

## 8. Synthetic Dataset Specification

| File Name | Key Schema Fields |
|---|---|
| `payments.csv` | `payment_id`, `order_id`, `amount`, `currency`, `status`, `fee`, `tax`, `method`, `bank`, `created_at` |
| `settlements.csv` | `settlement_id`, `gross_amount`, `fee`, `tax`, `adjustment`, `net_amount`, `utr`, `status`, `settled_at` |
| `refunds.csv` | `refund_id`, `payment_id`, `amount`, `status`, `settlement_id`, `arn`, `created_at`, `processed_at` |
| `disputes.csv` | `dispute_id`, `payment_id`, `amount`, `status`, `reason`, `settlement_id`, `created_at` |
| `adjustments.csv` | `adjustment_id`, `settlement_id`, `type`, `amount`, `description`, `created_at` |
| `bank_transactions.csv` | `bank_txn_id`, `utr`, `credit_amount`, `debit_amount`, `value_date`, `raw_description` |

---

## 9. Evaluation Metrics & Audit Specifications

### Target Metrics

| Metric | Definition | Target Priority |
|---|---|:---:|
| **Root-Cause Accuracy** | Percentage of variances mapped to the true underlying event(s). | Priority 1 |
| **False Closure Rate** | Cases falsely marked resolved without provable L4/L5 evidence (Must approach 0%). | Priority 1 |
| **Monetary Coverage** | Total ₹ value of variance provably explained vs total unverified variance. | Priority 2 |
| **Honest Exception Rate** | Ambiguous/partial variances correctly routed to human review without guessing. | Priority 2 |
| **Throughput** | Records processed per second across synthetic batches. | Priority 3 |

### Audit Output Record Structure

Every investigated variance must produce a JSON/table record:

```json
{
  "case_id": "VAR-2026-0042",
  "settlement_id": "set_104289",
  "expected_amount": 124500.00,
  "actual_settled_amount": 119000.00,
  "variance_amount": 5500.00,
  "status": "PARTIALLY_RESOLVED",
  "explained_amount": 3000.00,
  "unexplained_amount": 2500.00,
  "verified_causes": [
    {
      "event_id": "rfnd_9021",
      "type": "REFUND",
      "amount": 3000.00,
      "evidence_level": "L4",
      "source_reference": "refunds.csv:Row_193"
    }
  ],
  "escalation_reason": "Remaining ₹2,500 has no matching transaction or event records.",
  "utr": "AXISCN1153863727"
}
```

---

## 10. Source Registry & Documentation Links

| Provider | Topic / Document | Canonical URL |
|---|---|---|
| **Razorpay** | Settlements Overview & Dashboard | `https://razorpay.com/docs/payments/settlements/` |
| **Razorpay** | Settlement Webhooks Reference | `https://razorpay.com/docs/webhooks/settlements/` |
| **Razorpay** | Settlement Reconciliation API | `https://razorpay.com/docs/api/payments/settlements/recon/` |
| **Cashfree** | Settlement Recon Report Specs | `https://www.cashfree.com/docs/partners/embedded/reports/settlement-recon-reports` |
| **Cashfree** | Settlement Failure Reasons | `https://www.cashfree.com/docs/payments/split/settlements/failure-reasons` |
| **Airwallex** | Transaction Recon Report | `https://www.airwallex.com/docs/banking-as-a-service/reporting/financial-reports/transaction-reconciliation-report` |
| **Stripe** | Payout Reconciliation | `https://docs.stripe.com/reports/payout-reconciliation` |

# Phase 1 — Entity Relationships

> **Standard:** Relationships marked `[SOURCE]` are documented by providers. Relationships marked `[DESIGN]` are NeoFinesse POC design.

---

## 1. Entity Relationship Diagram

```
                    ┌──────────┐
                    │  Order   │
                    │ order_XXX│
                    └────┬─────┘
                         │ 1:N
                         ▼
                    ┌──────────┐        ┌────────────┐
                    │ Payment  │───────►│ UPI Txn    │
                    │ pay_XXXX │ 1:0..1 │ upi_XXXX   │
                    └──┬──┬────┘        └─────┬──────┘
                       │  │                   │ 1:N
              1:N ─────┘  └───── 1:N          ▼
              ▼                  ▼       ┌────────────┐
         ┌──────────┐     ┌──────────┐   │ UPI Event  │
         │  Refund  │     │ Dispute  │   └────────────┘
         │ rfnd_XXX │     │ disp_XXX │
         └────┬─────┘     └────┬─────┘
              │                │
              │   ┌────────────┘
              │   │   ┌───────────────────────────┐
              │   │   │ Adjustment / Transfer /   │
              │   │   │ Fee / Tax Line            │
              │   │   └─────────────┬─────────────┘
              ▼   ▼                 ▼
         ┌───────────────────────────────┐
         │        SettlementLine         │
         │          line_XXXX            │
         └──────────────┬────────────────┘
                        │ N:1
                        ▼
         ┌───────────────────────────────┐
         │          Settlement           │
         │          setl_XXXX            │
         └──────────────┬────────────────┘
                        │ 1:0..1 (via UTR)
                        ▼
         ┌───────────────────────────────┐
         │        BankTransaction        │
         │         (UTR match)           │
         └──────────────┬────────────────┘
                        │ 1:0..1
                        ▼
         ┌───────────────────────────────┐
         │         VarianceCase          │
         │        VAR-YYYY-NNNN          │
         └───────────────────────────────┘
```

---

## 2. Canonical Settlement Composition Path

The canonical path for settlement membership in NeoFinesse is:

```text
Financial Event (Payment / Refund / Dispute / Adjustment / Transfer)
                 ↓
           SettlementLine
                 ↓
             Settlement
                 ↓
                UTR
                 ↓
          BankTransaction
```

> **Architecture Rule:** `Payment.settlement_id` and `Refund.settlement_id` in provider reports are treated as **provider-derived / denormalized convenience fields**, not the fundamental relational membership. All settlement aggregation, variance detection, and root-cause attribution operate via the `SettlementLine` entity.

---

## 3. Relationship Details

### Order → Payment `[SOURCE]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:N` — One order can have multiple payment attempts |
| Join Key | `payment.order_id = order.id` |
| Provider Source | Razorpay: `order_id` on payment object |
| Semantics | Only successful/captured payments in the attempt set are eligible for settlement |

### Payment → Refund `[SOURCE]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:N` — One payment can have multiple partial refunds |
| Join Key | `refund.payment_id = payment.id` |
| Provider Source | Razorpay: `payment_id` on refund object |
| Constraint | $\sum \text{refund.amount} \le \text{payment.amount}$ |
| Cross-Batch Impact | Refunds may be deducted from a different settlement batch than the original payment's batch |

### Payment → Dispute `[SOURCE]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:N` — Payment can have disputes across multiple phases |
| Join Key | `dispute.payment_id = payment.id` |
| Provider Source | Razorpay: `payment_id` on dispute object |
| Cross-Batch Impact | Dispute deduction occurs in one settlement; if won, reversal credit occurs in a subsequent settlement |

### Payment → UPI Transaction `[DESIGN]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:0..1` — Only UPI payments have a linked UPI transaction record |
| Join Key | `upi_transaction.payment_id = payment.id` |
| Condition | Only when `payment.method = "upi"` |
| Purpose | Enables state-history reconstruction per Phase 0 Part B |

### UPI Transaction → UPI Event `[DESIGN]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:N` — Each UPI transaction has an ordered sequence of state events |
| Join Key | `upi_event.upi_transaction_id = upi_transaction.upi_transaction_id` |
| Ordering | `ORDER BY upi_event.timestamp ASC` |
| Purpose | Temporal reconstruction: `INITIATED → PENDING → FAILED → SUCCESS (late auth)` |

### Financial Events → SettlementLine `[DESIGN]`

| Source Event | SettlementLine Join Key | Cardinality | Net Contribution |
|---|---|:---:|---|
| **Payment** | `line.source_event_id = payment.id AND line.source_event_type = 'PAYMENT'` | `1:0..1` | `+ (amount - fee - tax)` |
| **Refund** | `line.source_event_id = refund.id AND line.source_event_type = 'REFUND'` | `1:0..1` | `- amount` |
| **Dispute (Loss/Hold)** | `line.source_event_id = dispute.id AND line.source_event_type = 'DISPUTE'` | `1:0..1` | `- amount_deducted` |
| **Dispute (Reversal/Win)** | `line.source_event_id = dispute.id AND line.source_event_type = 'DISPUTE_REVERSAL'` | `1:0..1` | `+ amount_deducted` |
| **Adjustment** | `line.source_event_id = adjustment.id AND line.source_event_type = 'ADJUSTMENT'` | `1:1` | `+ amount` or `- amount` |
| **Transfer** | `line.source_event_id = transfer.id AND line.source_event_type = 'TRANSFER'` | `1:1` | `- amount` |

### Settlement → SettlementLine `[DESIGN]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:N` — One settlement batch contains multiple heterogeneous settlement lines |
| Join Key | `settlement_line.settlement_id = settlement.id` |
| Aggregation | $\text{Settlement.expected\_amount} = \sum \text{settlement\_line.net\_amount}$ |
| Multi-Batch Support | A single payment and its subsequent refund will attach to distinct settlement lines pointing to distinct settlement batches |

### Settlement → Bank Transaction `[DESIGN]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:0..1` — Matched via UTR |
| Join Key | `bank_transaction.utr = settlement.utr` |
| Join Quality | **Primary deterministic key** — UTR is the definitive bank credit reference |
| Fallback | If UTR is absent/unparseable, `(amount, date_range)` acts as **candidate evidence only** (L0) |

### Settlement → Variance Case `[DESIGN]`

| Aspect | Detail |
|---|---|
| Cardinality | `1:0..1` — A case is created if and only if variance exists |
| Join Key | `variance_case.settlement_id = settlement.id` |
| Trigger | $\text{variance\_amount} = \text{expected\_amount} - \text{actual\_amount} \ne 0$ |

---

## 4. Cross-Settlement Relationships

Real-world finance operations frequently span multiple settlement batches:

| Scenario | Cross-Batch Flow | Reconciliation Requirement |
|---|---|---|
| **Post-Settlement Refund** | Payment settled in Batch A (`setl_01`); Refund processed next week settled in Batch B (`setl_02`). | `refund.settlement_id = setl_02` must NOT be treated as a variance in `setl_01`. |
| **Dispute Reversal** | Chargeback debited in Batch A (`setl_01`); Dispute won 30 days later, credit line in Batch C (`setl_03`). | Both lines linked to same `dispute.id` but distinct `settlement_id`s. |
| **Partial Settlement Rollover** | Deductions exceed eligible gross balance in Batch A; residual deductions rollover to Batch B. | Rollover lines connect consecutive settlement batches. |

---

## 5. Join Key Priority & Verification Semantics

| Priority | Join Key | Relational Scope | Verification Quality | Rule |
|:---:|---|---|:---:|---|
| **1** | `settlement_id` | SettlementLine → Settlement | **Definitive** | Valid only when explicitly established in settlement recon report. |
| **2** | `utr` | Settlement → Bank Credit | **Definitive** | Valid exact-string match against bank statement UTR column or parsed narration. |
| **3** | `payment_id` | Refund/Dispute/UPI → Payment | **Definitive** | Valid only when foreign key is present on source object. |
| **4** | `rrn` / `arn` | UPI/Refund → Bank Clearing | **High Confidence** | Corroborates transaction identity across provider and banking rails. |
| **5** | `(amount, date_range)` | Orphan Event → Settlement | **Candidate Only (L0)** | **Never treated as proof on its own.** Generates candidate hypothesis for solver. |

---

## Source Discipline

- `[SOURCE]` relationships: Documented by Razorpay and Cashfree API schemas and recon export formats.
- `[DESIGN]` relationships: NeoFinesse `SettlementLine` architecture and multi-source audit join keys.

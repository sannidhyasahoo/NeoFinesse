# Phase 0 — Part B: UPI Transaction-State Investigation

> **Goal:** Identify only the UPI state behaviour that matters for the Settlement Variance Investigator.  
> **Scope:** Hackathon POC — not a full UPI implementation or infrastructure project.

---

## 1. Core Finding

A UPI/payment **status observed at one point in time is not always the final financial truth**.

Official/provider documentation shows cases involving pending transactions, failed-but-debited transactions, reversals, delayed confirmation/deemed approval, and late authorization.

**Design principle:**

```text
Observed Status
      ↓
State History
      ↓
Financial Effect
      ↓
Settlement Reconciliation
```

---

## 2. Important Real-World States / Scenarios

| Scenario | Evidence from sources | Reconciliation implication |
|---|---|---|
| `SUCCESS` | Cashfree documents SUCCESS as a successful payment; Razorpay captured payments become eligible for settlement | Candidate for settlement inclusion |
| `FAILED` | Cashfree/Razorpay document failed payments and failure reasons | Do not treat as received money automatically |
| `PENDING` | Cashfree defines PENDING as non-terminal; NPCI documents delayed-status cases | **Do not classify as success or failure yet** |
| Failed + customer debited | NPCI, Razorpay and Cashfree document this scenario | Debit does not prove merchant receipt; investigate reversal/final state |
| Debit reversal | NPCI documents debit reversals | Failed + successful reversal can have net financial effect of ₹0 |
| Delayed confirmation / deemed approval | NPCI documents missing beneficiary-bank confirmation and deemed-approved handling | Missing confirmation ≠ automatically failed |
| Late authorization | Razorpay documents payments initially treated as failed/uncertain that later become authorized | **State history/timestamps matter** |

Sources: [NPCI UPI FAQ](https://www.npci.org.in/what-we-do/upi/faqs), [NPCI UPI ecosystem statistics](https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics), [NPCI circular on deemed approval/reversals](https://www.npci.org.in/PDF/npci/upi/circular/2018/UPI%20OC%2045%20-%20Solutions%20to%20reduce%20deemed%20approved%20transaction.pdf), [Razorpay payment lifecycle](https://razorpay.com/docs/payments/payments/), [Razorpay late authorization](https://razorpay.com/docs/payments/payments/late-authorisation/), [Cashfree payment status enums](https://www.cashfree.com/docs/api-reference/payments/enums).

---

## 3. What We Should NOT Do

Do **not** create a fake "official UPI status enum".

Providers expose different merchant-facing states and fields.

Instead, create a **normalized investigation model** for the POC.

### Proposed normalized states

```text
INITIATED
PENDING
SUCCESS
FAILED
REVERSED
LATE_SUCCESS
```

> These are **our internal normalized states**, not NPCI's official universal enum.

---

## 4. Model State History, Not Just Current Status

### Bad

```text
payment_id = P123
status = FAILED
```

### Better

```text
10:00  INITIATED
10:01  PENDING
10:05  FAILED
10:27  SUCCESS
10:28  CAPTURED
```

This is necessary because Razorpay explicitly documents late authorization, while NPCI documents delayed confirmation/reversal scenarios.

---

## 5. Minimal UPI Data Model

### `upi_transactions.csv`

| Field | Purpose |
|---|---|
| `upi_transaction_id` | UPI transaction identifier |
| `payment_id` | Link to payment |
| `order_id` | Link to order |
| `rrn` | Correlation/reference identifier where available |
| `amount` | Transaction amount |
| `initiated_at` | Start time |
| `current_status` | Latest observed status |
| `final_status` | Final known state, if determinable |
| `debit_observed` | Whether payer debit is evidenced |
| `reversal_status` | Reversal evidence/status |
| `reversal_amount` | Reversed amount |
| `reversal_at` | Reversal time |
| `error_code` | Provider/bank error |
| `error_reason` | Human-readable failure reason |
| `settlement_id` | Link to settlement, if present |
| `settlement_utr` | Settlement/bank reference, if present |

### `upi_events.csv`

| Field | Purpose |
|---|---|
| `event_id` | Unique event |
| `upi_transaction_id` | Parent transaction |
| `timestamp` | Event time |
| `previous_state` | Previous state |
| `new_state` | New state |
| `event_type` | State/event type |
| `amount` | Amount |
| `rrn` | Reference where available |
| `source` | Evidence source |

> This is a **normalized POC schema**, derived from useful fields documented by providers/NPCI. It is not an official UPI file format.

---

## 6. Financial Effect — The Important Abstraction

Instead of asking only:

> "What is the status?"

the investigator asks:

> **"What financial effect can the evidence prove?"**

Examples:

| Evidence | Derived effect |
|---|---:|
| SUCCESS ₹3,000 | `+₹3,000` |
| FAILED + debit + successful reversal ₹3,000 | `₹0` |
| PENDING + debit | `UNKNOWN` |
| FAILED + debit + reversal not found | `UNKNOWN` |
| SUCCESS + captured | `+₹3,000` candidate for settlement |

**Important:** `financial_effect` is our derived investigation field, not an NPCI/provider field.

---

## 7. UPI Investigation Rules

1. **Do not use amount alone as proof.**
2. **Do not use the latest status alone as proof.**
3. Check **state history + timestamps**.
4. Check **debit/reversal evidence** for failed transactions.
5. Check **RRN/bank reference** where available.
6. Check whether the payment was **captured/settlement-eligible**.
7. Check whether the payment is actually **linked to the settlement**.
8. Only use UPI as the cause of a settlement variance when the evidence connects it to the variance.
9. If the financial effect cannot be established, **escalate instead of guessing**.

---

## 8. How UPI Fits Into Settlement Investigation

UPI is an **evidence layer**, not the entire reconciliation system.

```text
                 SETTLEMENT VARIANCE
                         │
                         ▼
                  EVIDENCE RETRIEVAL
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Payments           UPI          Refunds /
                       Events        Chargebacks /
                                      Adjustments
        └────────────────┼────────────────┘
                         ▼
                  STATE RECONSTRUCTION
                         │
                         ▼
                  FINANCIAL EFFECT
                         │
                         ▼
                 CONSTRAINT ENGINE
                         │
                 ┌───────┴───────┐
                 ▼               ▼
              PROVEN          UNKNOWN
                 │               │
                 ▼               ▼
               CLOSE          ESCALATE
```

---

## 9. High-Value Benchmark Cases

Do not create dozens of UPI edge cases. For the hackathon, prioritize:

| Case | Priority | Expected behaviour |
|---|---|---|
| Normal SUCCESS → settlement | Control | Resolve |
| FAILED, no debit | Control | Exclude |
| FAILED + debit + reversal | High | Financial effect = ₹0 |
| PENDING + debit | High | Do not prematurely resolve |
| PENDING → SUCCESS | High | Use final state/history |
| Late authorization | **Very High** | Temporal investigation |
| SUCCESS + captured but absent from settlement | **Very High** | Settlement investigation |
| SUCCESS + settlement processed but bank credit missing | **Very High** | Bank/settlement investigation |
| Technical failure | Medium | Use structured error evidence |
| Duplicate UPI QR payment | Medium | Provider-specific scenario; do not generalize |

---

## 10. Example That Demonstrates the Idea

### Settlement

```text
Expected = ₹1,00,000
Actual   = ₹95,000
Variance = ₹5,000
```

Evidence:

```text
Refund      = -₹3,000
Chargeback  = -₹2,000

UPI payment = ₹5,000
Status      = FAILED
Debit       = YES
Reversal    = SUCCESS
```

Naive AI:

```text
UPI ₹5,000 ≈ variance ₹5,000
→ "UPI caused the variance"
```

Our system:

```text
UPI FAILED
+ debit
+ successful reversal
→ financial effect = ₹0
→ REJECT UPI HYPOTHESIS

Refund      = -₹3,000
Chargeback  = -₹2,000
Total       = -₹5,000

→ RESOLVED
```

**This is the kind of adversarial example worth showing in the hackathon demo.**

---

## 11. LLM Boundary

### Deterministic / rules engine

The system determines:

- state history
- latest/final state
- amount
- RRN/reference
- debit/reversal
- timestamps
- payment/settlement relationship
- financial effect

### LLM

Use only for:

- interpreting messy error descriptions
- grouping similar failure reasons
- ranking competing hypotheses
- producing the human-readable investigation explanation

### Never allow the LLM to:

- invent missing reversal evidence
- decide that `PENDING` means `FAILED`
- calculate source-of-truth settlement totals
- override deterministic evidence
- close a case without verified evidence

---

## 12. Part B Conclusion

The useful insight is **not** "we support UPI."

It is:

> **We reconstruct the financial state of a UPI transaction from its event history and supporting evidence before allowing it to explain a settlement variance.**

The project therefore treats:

```text
LATEST STATUS
     ≠
FINANCIAL TRUTH
```

unless the evidence establishes that the state is final and financially meaningful.

### Hackathon scope decision

Build:

- UPI transaction records
- UPI state-history events
- RRN/reference correlation
- debit + reversal handling
- temporal state reconstruction
- financial-effect calculation
- connection to settlement investigation

Do **not** build:

- a full UPI simulator
- NPCI infrastructure
- a universal UPI state machine
- real-bank integration
- a huge UPI taxonomy

---

## Primary Sources

- NPCI — UPI FAQ: https://www.npci.org.in/what-we-do/upi/faqs
- NPCI — UPI ecosystem statistics: https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics
- NPCI — UPI product overview: https://www.npci.org.in/product/upi/about-upi
- NPCI — Deemed approval / reversal circular: https://www.npci.org.in/PDF/npci/upi/circular/2018/UPI%20OC%2045%20-%20Solutions%20to%20reduce%20deemed%20approved%20transaction.pdf
- Razorpay — Payment lifecycle: https://razorpay.com/docs/payments/payments/
- Razorpay — Late authorization: https://razorpay.com/docs/payments/payments/late-authorisation/
- Razorpay — UPI errors: https://razorpay.com/docs/errors/payments/upi/
- Razorpay — UPI QR FAQ: https://razorpay.com/docs/payments/payment-methods/upi-qr/faqs/
- Cashfree — Payment status enums: https://www.cashfree.com/docs/api-reference/payments/enums
- Cashfree — Transactions: https://www.cashfree.com/docs/payments/manage/transactions

---

**Source discipline:** Provider/NPCI facts above are cited. Normalized schemas, financial-effect logic, investigation rules, benchmark cases, and architecture are **our POC design**, not claims about how NPCI/Razorpay/Cashfree internally implement reconciliation.

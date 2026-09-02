# Phase 1 — Entity Lifecycles & State Machines

> **Standard:** States marked `[SOURCE]` are documented by providers. States marked `[DESIGN]` are NeoFinesse normalized states or derived conclusions.

---

## 1. Observed State vs Derived Conclusion Principle

A fundamental design requirement of NeoFinesse is preserving provider observations separately from internal conclusions:

```text
provider_status             (Raw string / enum from provider API/CSV)
       ↓
normalized_observed_status  (Standardized provider observation)
       ↓
final_determined_status     (NeoFinesse derived conclusion based on event history + evidence)
```

> **Core Rule:** `final_determined_status` (such as `LATE_SUCCESS` or `REVERSED`) is a **NeoFinesse conclusion** derived from evidence. It is never misrepresented as an official provider status.

---

## 2. Payment Lifecycle

### Razorpay Payment States `[SOURCE]`

```
created ──► authorized ──► captured ──► refunded
                │               │
                ▼               ▼
             failed          (settled)
```

| State | Settlement Eligible | Financial Effect |
|---|---|---|
| `created` | No | ₹0 — order intent only |
| `authorized` | No | Customer funds authorized/held, not captured |
| `captured` | **Yes** | `+amount` candidate for settlement line creation |
| `refunded` | Post-settlement | Payment itself was captured; refund line appears in subsequent settlement |
| `failed` | No | ₹0 unless late authorization occurs |

### Provider-Agnostic Normalized Observed States `[DESIGN]`

| Normalized State | Source State Mapping | Settlement Eligibility |
|---|---|---|
| `INITIATED` | `created`, `NOT_ATTEMPTED` | None |
| `PENDING` | `authorized`, `PENDING` | None (awaiting terminal confirmation) |
| `CAPTURED` | `captured`, `SUCCESS` | Eligible for settlement line inclusion |
| `FAILED` | `failed`, `FAILED`, `CANCELLED`, `VOID` | None |
| `REFUNDED` | `refunded` | Originally settled; refund line tracked separately |

---

## 3. Refund Lifecycle

### Razorpay Refund States `[SOURCE]`

```
pending ──► processed
    │
    ▼
  failed
```

| State | Description | Settlement Impact |
|---|---|---|
| `pending` | Refund initiated, in processing queue | No settlement line created yet |
| `processed` | Refund completed via banking rails | Generates a debit `SettlementLine` (`-amount`) |
| `failed` | Refund could not be processed | ₹0 — no deduction |

### Speed Variants `[SOURCE: Razorpay]`

| Type | Behaviour |
|---|---|
| `normal` | Standard processing via payment method rails (5–7 banking days) |
| `instant` | Source-agnostic immediate refund; processed instantly |

---

## 4. Settlement Lifecycle

### Gateway-Side States `[SOURCE: Razorpay]`

```
created ──► processed
    │
    ▼
  failed
```

| State | Description |
|---|---|
| `created` | Settlement batch assembled by gateway |
| `processed` | Payout initiated to merchant bank account; UTR assigned |
| `failed` | Gateway payout failed (bank rejection, frozen account, invalid IFSC) |

### Bank-Side Clearance States `[DESIGN]`

After gateway marks `processed`, bank clearing introduces explicit clearance states:

```
PROCESSED ──► PENDING_BANK_CREDIT ──► BANK_CREDITED
    │                                       │
    ▼                                       ▼
  FAILED                            VARIANCE_DETECTED
                                    (if expected ≠ actual)
```

| Bank Clearance State | Definition |
|---|---|
| `PENDING_BANK_CREDIT` | Gateway reports `processed` and provides UTR, but credit is not yet present in bank statement |
| `BANK_CREDITED` | Matching UTR and credit amount confirmed in bank statement |
| `BANK_REJECTED` | Beneficiary bank rejected/returned the settlement credit |

---

## 5. Settlement Composition & Expected Amount Semantics

### Provider-Reported Amount vs NeoFinesse Expected Amount

We strictly distinguish:

1. **Provider-Reported Settlement Amount (`Settlement.amount`):** The net amount the payment gateway claims to have settled.
2. **NeoFinesse Expected Settlement Amount (`Settlement.expected_amount`):** The mathematically verified sum of all constituent settlement lines:

$$\text{Expected Settlement Amount} = \sum_{i \in \text{SettlementLines}} \text{line}_i.\text{net\_amount}$$

Where each $\text{line}.\text{net\_amount}$ is signed:
- `+ (amount - fee - tax)` for `PAYMENT`
- `- amount` for `REFUND`
- `- amount_deducted` for `DISPUTE`
- `+ amount_deducted` for `DISPUTE_REVERSAL`
- `+ amount` or `- amount` for `ADJUSTMENT`
- `- amount` for `TRANSFER`

> **No Double Counting:** Fees, taxes, and refunds are **not** subtracted again at the batch level if they already exist as line items in `SettlementLine`.

---

## 6. Dispute / Chargeback Lifecycle

### Razorpay Dispute States `[SOURCE]`

```
open ──► under_review ──► won  (reversal credit line in future settlement)
                    │
                    ▼
                  lost (deduction line final)
                    │
                    ▼
                 closed
```

| State | Financial Effect |
|---|---|
| `open` | Disputed amount debited/held via debit `SettlementLine` |
| `under_review` | Held amount unchanged |
| `won` | Dispute resolved in merchant favor; reversal credit `SettlementLine` issued |
| `lost` | Deduction remains final |
| `closed` | Terminal state |

---

## 7. UPI Transaction State Machine & Financial Effect

### State Reconstruction Architecture `[DESIGN]`

```
[ Observed State Flow ]
INITIATED ──► PENDING ──► SUCCESS ──► (CAPTURED / Settlement-Eligible)
                │              ▲
                ▼              │
              FAILED ──────────┘ (Late Authorization Event)
                │
                ▼
         [ Debit Observed? ]
              │       │
              No      Yes
              │       │
              ▼       ▼
           [Done]   [ Reversal Observed? ]
                    │        │
                  SUCCESS   NONE / INCONCLUSIVE
                    │        │
                    ▼        ▼
               Effect: ₹0   Effect: UNKNOWN (Escalate)
```

### Type-Safe Financial Effect Semantics `[DESIGN]`

The financial effect of a UPI transaction is represented by two strongly-typed fields:

```python
financial_effect_status: FinancialEffectStatus  # DETERMINED | UNKNOWN
financial_effect_amount: Optional[int]          # Signed paise, null if UNKNOWN
```

### Financial Effect Determination Logic `[DESIGN]`

```python
def compute_upi_financial_effect(upi_txn: UPITransaction) -> tuple[str, Optional[int]]:
    # Case 1: Confirmed Success
    if upi_txn.final_determined_status in ("SUCCESS", "LATE_SUCCESS"):
        return ("DETERMINED", +upi_txn.amount)

    # Case 2: Clean Failure (no customer debit observed)
    if upi_txn.final_determined_status == "FAILED" and not upi_txn.debit_observed:
        return ("DETERMINED", 0)

    # Case 3: Failed + Debited + Confirmed Reversal
    if upi_txn.final_determined_status == "FAILED" and upi_txn.debit_observed:
        if upi_txn.reversal_status == "SUCCESS":
            return ("DETERMINED", 0)
        else:
            # "No reversal evidence found in the available dataset."
            # Do NOT assume reversal didn't happen, but cannot prove financial truth
            return ("UNKNOWN", None)

    # Case 4: Pending / In-flight
    if upi_txn.final_determined_status in ("PENDING", "INITIATED", None):
        return ("UNKNOWN", None)

    # Case 5: Full Reversal
    if upi_txn.final_determined_status == "REVERSED":
        return ("DETERMINED", 0)

    return ("UNKNOWN", None)
```

---

## 8. Settlement Timing Windows `[DESIGN]`

Timing windows are **plan and provider-dependent**, not universal financial laws:

| Phase | Provider-Documented Typical Schedule | NeoFinesse Investigation Window `[DESIGN]` |
|---|---|---|
| **Payment → Capture** | Instant (auto-capture) or up to 5 days (manual) | Verified per `payment.captured_at` timestamp |
| **Capture → Settlement Creation** | T+1 to T+3 depending on merchant plan & provider | Configurable parameter `SETTLEMENT_WINDOW_DAYS` (default: 3 days) |
| **Settlement → Payout Initiation** | Same day as batch cutoff | Gateway timestamp `settlement.created_at` |
| **Payout Initiation → Bank Credit** | 0 to 2 banking days (clearing rails: NEFT/RTGS/IMPS) | Bank statement window `[settled_at, settled_at + 2 days]` |

---

## 9. Evidence Hierarchy for Variance Verification

NeoFinesse strictly enforces: **Plausible ≠ Proven.** Amount matching alone is never proof.

```text
Amount Match (Candidate Only)
      ↓
Relationship Match (Entity Link)
      ↓
Settlement Relevance (Batch Membership)
      ↓
Temporal Validity (Cutoff & Ordering)
      ↓
Financial Completeness (Subset-Sum Exact Match)
      ↓
Multi-Source Confirmation (UTR Bank Credit Verified)
```

| Level | Evidence State | Description | Investigation Decision |
|:---:|---|---|---|
| **L0** | **Candidate (Amount Only)** | Event amount equals variance, but no relationship, batch, or temporal link exists. | `UNRESOLVED` (Never close) |
| **L1** | **Entity-Linked** | Event matches amount and references relevant `payment_id` / `order_id`. | `CANDIDATE` (Insufficient causality) |
| **L2** | **Settlement-Associated** | Event has explicit `SettlementLine` within the target `settlement_id`. | `PLAUSIBLE` |
| **L3** | **Temporally Consistent** | Event `processed_at` precedes batch cutoff; no subsequent conflicting reversal. | `HIGH_CONFIDENCE` |
| **L4** | **Financially Complete** | Single event or verified subset of `SettlementLine`s exactly explains variance. | `RESOLVED` |
| **L5** | **Multi-Source Verified** | Full audit chain verified: `Payment → Event → SettlementLine → Settlement → UTR → Bank Credit`. | `FULLY_RECONCILED` |

---

## Source Discipline

- `[SOURCE]` states: Razorpay API documentation (Payment, Refund, Settlement, Dispute), Cashfree status enums, NPCI UPI circulars.
- `[DESIGN]` states: NeoFinesse clearance states, normalized observed vs inferred status separation, type-safe financial effect determination, and L0–L5 evidence hierarchy.

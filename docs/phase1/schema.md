# Phase 1 — Financial Event Schema

> **Standard:** Fields marked `[SOURCE]` come from documented provider APIs. Fields marked `[DESIGN]` are NeoFinesse POC design decisions.

---

## 1. Core Entity Types

| Entity | Identity Pattern | Provider Source |
|---|---|---|
| Payment | `pay_XXXX` | Razorpay Payment API |
| Refund | `rfnd_XXXX` | Razorpay Refund API |
| Settlement | `setl_XXXX` | Razorpay Settlement API |
| Settlement Line | `line_XXXX` | `[DESIGN]` normalized settlement composition |
| Adjustment | `adj_XXXX` | Razorpay Settlement Recon |
| Transfer | `trf_XXXX` | Razorpay Transfer API |
| Dispute | `disp_XXXX` | Razorpay Dispute API |
| Order | `order_XXXX` | Razorpay Order API |
| UPI Transaction | `upi_XXXX` | `[DESIGN]` normalized |
| UPI Event | `upievt_XXXX` | `[DESIGN]` state history |
| Bank Transaction | `bank_XXXX` | `[DESIGN]` bank statement line |
| Variance Case | `VAR-YYYY-NNNN` | `[DESIGN]` investigation case |

---

## 2. Provenance Reference Structure `[DESIGN]`

Every entity in NeoFinesse includes a `_provenance` reference linking it directly to the exact source record:

| Field | Type | Description |
|---|---|---|
| `source_id` | `string` | Unique ingestion identifier (`SRC-2026-0001`) |
| `source_type` | `enum` | `CSV`, `XLSX`, `XLS`, `API_RESPONSE`, `WEBHOOK` |
| `source_file` | `string` | Original filename |
| `source_sheet` | `string?` | Sheet name for Excel files (`null` for CSV) |
| `source_row` | `integer` | 1-indexed row number (header = 1) |
| `source_columns` | `object?` | Cell mapping e.g. `{"payment_id": "A193", "amount": "D193"}` |
| `source_hash` | `string` | SHA-256 hash of entire source file |
| `record_hash` | `string` | SHA-256 hash of exact source row / payload |
| `provider` | `enum` | `razorpay`, `cashfree`, `stripe`, `airwallex`, `bank` |
| `ingested_at` | `datetime` | ISO-8601 ingestion timestamp |
| `ingested_by` | `string` | Ingestion pipeline / batch ID |

---

## 3. Payment

### Source Fields `[SOURCE: Razorpay]`

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `pay_XXXX` — Razorpay payment identifier |
| `entity` | `string` | Always `"payment"` |
| `amount` | `integer` | Amount in smallest currency unit (paise) |
| `currency` | `string` | ISO 4217 (`INR`) |
| `status` | `enum` | `created`, `authorized`, `captured`, `refunded`, `failed` |
| `order_id` | `string` | Linked order |
| `method` | `string` | `upi`, `card`, `netbanking`, `wallet`, `emandate`, `bank_transfer` |
| `description` | `string` | Payment description |
| `bank` | `string` | Issuing bank code |
| `wallet` | `string` | Wallet name if applicable |
| `vpa` | `string` | UPI VPA if applicable |
| `email` | `string` | Payer email |
| `contact` | `string` | Payer phone |
| `fee` | `integer` | Razorpay fee in paise |
| `tax` | `integer` | GST on fee in paise |
| `error_code` | `string` | Error code on failure |
| `error_description` | `string` | Failure reason |
| `error_source` | `string` | `gateway`, `bank`, `business` |
| `error_step` | `string` | Failure step |
| `error_reason` | `string` | Failure reason code |
| `acquirer_data` | `object` | `{ "rrn": "...", "auth_code": "..." }` |
| `created_at` | `integer` | Unix epoch |
| `captured_at` | `integer` | Capture timestamp (if captured) |
| `settled` | `boolean` | Whether settlement-eligible |

### POC Additions `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `settlement_id` | `string?` | *[Denormalized convenience field]* FK to settlement from provider report. Canonical settlement membership is via `SettlementLine`. |
| `net_amount` | `integer` | `amount - fee - tax` (computed) |
| `provider` | `enum` | `razorpay`, `cashfree`, `stripe`, `airwallex` |
| `_provenance` | `ProvenanceReference` | Complete audit backlink to source spreadsheet row |

---

## 4. Refund

### Source Fields `[SOURCE: Razorpay]`

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `rfnd_XXXX` |
| `entity` | `string` | Always `"refund"` |
| `amount` | `integer` | Refund amount in paise |
| `currency` | `string` | ISO 4217 |
| `payment_id` | `string` | Parent payment |
| `status` | `enum` | `pending`, `processed`, `failed` |
| `speed_requested` | `enum` | `normal`, `optimum` |
| `speed_processed` | `enum` | `instant`, `normal` |
| `receipt` | `string` | Merchant receipt number |
| `acquirer_data` | `object` | `{ "arn": "..." }` — Acquirer Reference Number |
| `created_at` | `integer` | Unix epoch |
| `processed_at` | `integer` | Processing timestamp |

### POC Additions `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `settlement_id` | `string?` | *[Denormalized convenience field]* Which settlement batch deducted this refund. Canonical membership is via `SettlementLine`. |
| `provider` | `enum` | Source provider |
| `_provenance` | `ProvenanceReference` | Complete audit backlink to source spreadsheet row |

---

## 5. Settlement Line `[DESIGN]`

> **Canonical Settlement Membership Entity:** Represents an atomic entry within a settlement batch. Heterogeneous financial events (payments, refunds, disputes, adjustments, transfers) participate in a settlement via dedicated settlement lines.

| Field | Type | Purpose |
|---|---|---|
| `settlement_line_id` | `string` | `line_XXXX` — Unique settlement line identifier |
| `settlement_id` | `string` | FK to `Settlement` |
| `source_event_id` | `string` | Identifies underlying event (`pay_XXXX`, `rfnd_XXXX`, `disp_XXXX`, `adj_XXXX`, `trf_XXXX`) |
| `source_event_type` | `enum` | `PAYMENT`, `REFUND`, `DISPUTE`, `DISPUTE_REVERSAL`, `ADJUSTMENT`, `TRANSFER`, `FEE_LINE`, `TAX_LINE` |
| `payment_id` | `string?` | Nullable FK to parent `Payment` if applicable |
| `amount` | `integer` | Gross amount of the line item in paise |
| `fee` | `integer?` | Fee attributed to this line in paise |
| `tax` | `integer?` | Tax on fee attributed to this line in paise |
| `net_amount` | `integer` | Signed net contribution to settlement batch (`+` for credit, `-` for debit) in paise |
| `currency` | `string` | ISO 4217 (`INR`) |
| `event_timestamp` | `datetime?` | When the source event occurred |
| `settlement_timestamp` | `datetime?` | When batch settlement was processed |
| `provider` | `enum` | Source provider |
| `_provenance` | `ProvenanceReference` | Complete audit backlink to source settlement recon row |

---

## 6. Settlement

### Source Fields `[SOURCE: Razorpay]`

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `setl_XXXX` |
| `entity` | `string` | Always `"settlement"` |
| `amount` | `integer` | Net settled amount in paise (provider-reported) |
| `status` | `enum` | `created`, `processed`, `failed` |
| `fees` | `integer` | Total fees deducted |
| `tax` | `integer` | Total tax deducted |
| `utr` | `string` | Bank Unique Transaction Reference (e.g. `AXISCN1153863727`) |
| `created_at` | `integer` | Unix epoch creation |

### POC Additions `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `gross_amount` | `integer` | Sum of gross payment amounts before deductions |
| `refund_total` | `integer` | Sum of refunds in this batch |
| `adjustment_total` | `integer` | Sum of adjustments in this batch |
| `dispute_total` | `integer` | Sum of disputes/chargebacks in this batch |
| `transfer_total` | `integer` | Sum of transfers in this batch |
| `expected_amount` | `integer` | NeoFinesse expected settlement amount: $\sum \text{signed SettlementLine.net\_amount}$ |
| `variance` | `integer` | `expected_amount - amount` (the delta investigated) |
| `bank_credit_amount` | `integer?` | Matched from bank statement |
| `bank_credit_date` | `date?` | Value date from bank statement |
| `bank_reference` | `string?` | Bank-side reference |
| `recon_status` | `enum` | `MATCHED`, `VARIANCE_DETECTED`, `PENDING_BANK_CREDIT`, `FAILED` |
| `provider` | `enum` | Source provider |
| `settled_at` | `integer` | Actual settlement timestamp |
| `_provenance` | `ProvenanceReference` | Complete audit backlink to source settlement summary row |

---

## 7. Adjustment

### Source Fields `[SOURCE: Razorpay/Cashfree]`

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `adj_XXXX` |
| `entity` | `string` | `"adjustment"` |
| `amount` | `integer` | Adjustment amount (positive=credit, negative=debit) |
| `currency` | `string` | ISO 4217 |
| `description` | `string` | Adjustment reason/remarks |
| `settlement_id` | `string` | *[Denormalized convenience field]* Settlement this adjustment applies to |
| `created_at` | `integer` | Unix epoch |

### Cashfree-Specific Event Types `[SOURCE: Cashfree]`

| Event Type | Sale Type | Description |
|---|---|---|
| `PAYMENT` | `CREDIT` | Standard payment credit |
| `REFUND` | `DEBIT` | Refund deduction |
| `CHARGEBACK` | `DEBIT` | Chargeback deduction |
| `CHARGEBACK_REVERSE` | `CREDIT` | Chargeback reversal |
| `DISPUTE` | `DEBIT` | Dispute deduction |
| `DISPUTE_REVERSE` | `CREDIT` | Dispute reversal |
| `RISK` | `DEBIT` | Risk-related hold |
| `RISK_REVERSE` | `CREDIT` | Risk hold release |
| `OTHER_ADJUSTMENT` | varies | Manual/fee adjustments |

### POC Additions `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `adjustment_type` | `enum` | Normalized: `FEE`, `TAX`, `RISK_HOLD`, `RISK_RELEASE`, `MANUAL_CREDIT`, `MANUAL_DEBIT`, `RESERVE_HOLD`, `RESERVE_RELEASE`, `OTHER` |
| `provider` | `enum` | Source provider |
| `_provenance` | `ProvenanceReference` | Complete audit backlink to source adjustment record |

---

## 8. Dispute

### Source Fields `[SOURCE: Razorpay]`

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `disp_XXXX` |
| `entity` | `string` | `"dispute"` |
| `payment_id` | `string` | Disputed payment |
| `amount` | `integer` | Dispute amount in paise |
| `currency` | `string` | ISO 4217 |
| `amount_deducted` | `integer` | Actually deducted amount |
| `reason_code` | `string` | Chargeback reason code |
| `respond_by` | `integer` | Response deadline |
| `status` | `enum` | `open`, `under_review`, `won`, `lost`, `closed` |
| `phase` | `enum` | `chargeback`, `pre_arbitration`, `arbitration` |
| `created_at` | `integer` | Unix epoch |

### POC Additions `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `settlement_id` | `string?` | *[Denormalized convenience field]* Settlement batch that deducted this |
| `reversal_settlement_id` | `string?` | *[Denormalized convenience field]* If won, settlement batch that credited back |
| `net_financial_effect` | `integer` | Computed: `-amount_deducted` if lost, `0` if won/reversed |
| `provider` | `enum` | Source provider |
| `_provenance` | `ProvenanceReference` | Complete audit backlink to source dispute record |

---

## 9. Transfer

### Source Fields `[SOURCE: Razorpay]`

| Field | Type | Description |
|---|---|---|
| `id` | `string` | `trf_XXXX` |
| `entity` | `string` | `"transfer"` |
| `amount` | `integer` | Transfer amount in paise |
| `currency` | `string` | ISO 4217 |
| `recipient` | `string` | Linked account identifier |
| `settlement_id` | `string?` | Linked settlement |
| `created_at` | `integer` | Unix epoch |

### POC Additions `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `provider` | `enum` | Source provider |
| `_provenance` | `ProvenanceReference` | Complete audit backlink |

---

## 10. UPI Transaction `[DESIGN]`

> Normalized from Razorpay/Cashfree/NPCI documentation patterns (see Phase 0 Part B).
> **Principle:** Observed status is strictly separated from inferred/derived final status.

| Field | Type | Purpose |
|---|---|---|
| `upi_transaction_id` | `string` | Internal identifier (`upi_XXXX`) |
| `payment_id` | `string` | FK to Payment |
| `order_id` | `string?` | FK to Order |
| `rrn` | `string?` | Retrieval Reference Number |
| `amount` | `integer` | Transaction amount (paise) |
| `vpa` | `string?` | UPI VPA |
| `initiated_at` | `datetime` | Initiation timestamp |
| `current_observed_status` | `enum` | **[Observed Fact]** Latest status reported by provider: `INITIATED`, `PENDING`, `SUCCESS`, `FAILED`, `REVERSED` |
| `final_determined_status` | `enum` | **[Inferred Conclusion]** Computed from event history: `INITIATED`, `PENDING`, `SUCCESS`, `FAILED`, `REVERSED`, `LATE_SUCCESS` |
| `debit_observed` | `boolean` | **[Observed Fact]** Whether customer debit evidence exists |
| `reversal_status` | `enum?` | **[Observed Fact]** `NONE`, `INITIATED`, `SUCCESS`, `FAILED` |
| `reversal_amount` | `integer?` | Reversed amount (paise) |
| `reversal_at` | `datetime?` | Reversal timestamp |
| `error_code` | `string?` | Provider/bank error code |
| `error_reason` | `string?` | Error description text |
| `financial_effect_status` | `enum` | **[Type-Safe Semantics]** `DETERMINED`, `UNKNOWN` |
| `financial_effect_amount` | `integer?` | **[Type-Safe Semantics]** Signed amount in paise, or `null` if status is `UNKNOWN` |
| `_provenance` | `ProvenanceReference` | Complete audit backlink |

---

## 11. UPI Event `[DESIGN]`

> State-history records for temporal reconstruction (see Phase 0 Part B §4).

| Field | Type | Purpose |
|---|---|---|
| `event_id` | `string` | Unique event identifier (`upievt_XXXX`) |
| `upi_transaction_id` | `string` | FK to UPI Transaction |
| `timestamp` | `datetime` | Event time |
| `previous_state` | `enum` | State before this event |
| `new_state` | `enum` | State after this event |
| `event_type` | `string` | Type description (e.g. `WEBHOOK_CAPTURE`, `LATE_AUTH_CALLBACK`, `REVERSAL_CONFIRMATION`) |
| `amount` | `integer?` | Amount if relevant |
| `rrn` | `string?` | Reference if available |
| `source` | `string` | Evidence source (webhook, API, recon report) |
| `_provenance` | `ProvenanceReference` | Complete audit backlink |

---

## 12. Bank Transaction `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `bank_txn_id` | `string` | Bank-side transaction ID (`bank_XXXX`) |
| `utr` | `string` | UTR — primary deterministic join key to settlement |
| `credit_amount` | `integer?` | Credit amount (paise) |
| `debit_amount` | `integer?` | Debit amount (paise) |
| `balance` | `integer?` | Running balance if available |
| `value_date` | `date` | Value/settlement date |
| `transaction_date` | `date` | Posting date |
| `raw_description` | `string` | Raw bank narration text |
| `parsed_utr` | `string?` | UTR extracted from narration |
| `account_number` | `string` | Bank account |
| `_provenance` | `ProvenanceReference` | Complete audit backlink to bank statement line |

---

## 13. Variance Investigation Record `[DESIGN]`

| Field | Type | Purpose |
|---|---|---|
| `case_id` | `string` | `VAR-YYYY-NNNN` |
| `settlement_id` | `string` | Subject settlement |
| `expected_amount` | `integer` | Computed expected amount ($\sum \text{SettlementLine.net\_amount}$) |
| `actual_amount` | `integer` | Actual provider-settled amount |
| `variance_amount` | `integer` | Delta (`expected_amount - actual_amount`) |
| `status` | `enum` | `OPEN`, `INVESTIGATING`, `PARTIALLY_RESOLVED`, `RESOLVED`, `ESCALATED` |
| `explained_amount` | `integer` | Verified portion |
| `unexplained_amount` | `integer` | Remaining unverified portion |
| `verified_causes` | `array` | List of `{ event_id, settlement_line_id, type, amount, evidence_level, source_reference }` |
| `evidence_level` | `enum` | Overall case evidence level: `L0`–`L5` |
| `escalation_reason` | `string?` | Why escalated |
| `investigator_notes` | `string?` | LLM-generated explanation |
| `created_at` | `datetime` | Case opened |
| `resolved_at` | `datetime?` | Case closed |

---

## Source Discipline

- `[SOURCE]` fields: Razorpay API docs (Payments, Refunds, Settlements, Disputes, Transfers), Cashfree settlement recon docs, Stripe payout recon docs.
- `[DESIGN]` fields: NeoFinesse POC decisions for reconciliation, provenance, and variance investigation.
- No field is invented and attributed to a provider.

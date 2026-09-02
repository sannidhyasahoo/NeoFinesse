# Phase 1 — Design Decisions Register

> **Purpose:** Record every non-obvious design decision with rationale, alternatives considered, and source basis.

---

## Decision Format

Each decision follows:

| Field | Purpose |
|---|---|
| **ID** | `PD-NNN` (Phase Decision) |
| **Decision** | What was decided |
| **Rationale** | Why |
| **Alternatives Rejected** | What else was considered |
| **Source Basis** | `[SOURCE]` fact or `[DESIGN]` judgment |
| **Revisit Trigger** | When to reconsider |

---

## PD-001: Amounts Stored in Paise (Smallest Currency Unit)

| Aspect | Detail |
|---|---|
| **Decision** | All monetary amounts stored as integers in paise (1/100 INR) |
| **Rationale** | Razorpay API returns amounts in paise. Integer arithmetic avoids floating-point rounding errors in reconciliation (₹100.00 = 10000 paise). Rounding errors in settlement reconciliation are unacceptable. |
| **Alternatives Rejected** | Decimal (float) storage — rejected due to floating-point precision issues in subset-sum operations |
| **Source Basis** | `[SOURCE]` Razorpay API documentation: "amount is in paise" |
| **Revisit Trigger** | Multi-currency support (USD cents, etc.) |

---

## PD-002: Embedded Provenance References for POC

| Aspect | Detail |
|---|---|
| **Decision** | NeoFinesse entities carry embedded `ProvenanceReference` objects (`source_id`, `source_file`, `source_sheet`, `source_row`, `source_columns`, `source_hash`, `record_hash`) linking directly to the Source File Registry. |
| **Rationale** | Avoids heavy join overhead during multi-constraint solving and LLM explanation generation. Every entity in memory is self-contained with its exact spreadsheet backlink (`File → Sheet → Row → Cell`). |
| **Alternatives Rejected** | Fully normalized separate provenance table with foreign keys — rejected for POC simplicity and query performance; Shallow provenance (file + row only without hashes/cells) — rejected because it fails exact cell-level audit requirements. |
| **Source Basis** | `[DESIGN]` — architecture design for Track 04 auditability requirement |
| **Revisit Trigger** | If database storage footprint becomes a bottleneck at high scale |

---

## PD-003: Normalized Provider-Agnostic Status Enums

| Aspect | Detail |
|---|---|
| **Decision** | Create NeoFinesse-internal normalized states (e.g., `CAPTURED`, `PENDING`, `FAILED`) mapped from provider-specific enums |
| **Rationale** | Razorpay uses `captured`/`authorized`; Cashfree uses `SUCCESS`/`PENDING`. Investigation rules must work across providers without per-provider branching. |
| **Alternatives Rejected** | Raw provider states only — rejected because investigation rules would need N×M provider-specific branches |
| **Source Basis** | `[DESIGN]` — normalization layer is our design; individual enum values are `[SOURCE]` from each provider |
| **Revisit Trigger** | New provider with states that don't map cleanly |

---

## PD-004: UPI State History as Separate Event Table

| Aspect | Detail |
|---|---|
| **Decision** | UPI transactions have both a current-state record AND a separate `upi_events` table recording state transitions |
| **Rationale** | Phase 0 Part B established that current status ≠ financial truth. Late authorization (FAILED→SUCCESS) requires temporal reconstruction. A single `status` field cannot represent this. |
| **Alternatives Rejected** | Single status field — rejected per Phase 0 Part B finding that late auth, debit+reversal require history |
| **Source Basis** | `[SOURCE]` Razorpay late authorization docs; `[SOURCE]` NPCI deemed-approval circulars; `[DESIGN]` event-sourcing pattern |
| **Revisit Trigger** | If non-UPI methods also need state history (cards, netbanking) |

---

## PD-005: Type-Safe Financial Effect Semantics

| Aspect | Detail |
|---|---|
| **Decision** | Financial effect is represented by two strongly-typed fields: `financial_effect_status` (`DETERMINED` or `UNKNOWN`) and `financial_effect_amount` (signed integer in paise or `null` if unknown). |
| **Rationale** | Prevents type inconsistencies and eliminates unsafe magic numbers (like `-1` or `999999` for unknown). When reversal evidence is absent in a failed transaction with debit, the status is explicitly `UNKNOWN` with `amount = null` and routed for human escalation. |
| **Alternatives Rejected** | Storing `financial_effect: integer` with magic numbers — rejected as type-unsafe; Overwriting transaction status with derived effect — rejected because observed facts must be preserved. |
| **Source Basis** | `[DESIGN]` — Phase 0 Part B §6 financial effect matrix |
| **Revisit Trigger** | If additional financial effect categories (e.g. `PROVISIONAL`) are required |

---

## PD-006: UTR as Primary Settlement→Bank Join Key

| Aspect | Detail |
|---|---|
| **Decision** | The UTR (Unique Transaction Reference) is the primary deterministic key for matching settlements to bank credits |
| **Rationale** | UTR is documented by Razorpay in settlement webhooks and is the standard Indian banking reference. It is the only reliable exact-match key between gateway and bank worlds. |
| **Alternatives Rejected** | Amount+date fuzzy matching — rejected as primary (kept as fallback candidate only, per evidence hierarchy L0) |
| **Source Basis** | `[SOURCE]` Razorpay settlement webhook: `utr` field (e.g., `AXISCN1153863727`); `[SOURCE]` Cashfree: `UTR No.` in settlement summary |
| **Revisit Trigger** | International settlements without UTR format |

---

## PD-007: Evidence Level Hierarchy (L0–L5)

| Aspect | Detail |
|---|---|
| **Decision** | Six-level evidence hierarchy from L0 (amount-only candidate) to L5 (full multi-source verification) |
| **Rationale** | Core project principle: "Plausible ≠ Proven." Matching amounts are necessary but insufficient. Each level adds a verification constraint (entity link, batch membership, temporal consistency, financial completeness, bank confirmation). |
| **Alternatives Rejected** | Binary resolved/unresolved — rejected because partial evidence is common and must be tracked; Three-level (low/medium/high) — rejected as too coarse for the audit trail |
| **Source Basis** | `[DESIGN]` — Phase 0 Part A §6 evidence hierarchy |
| **Revisit Trigger** | If hackathon judges find 6 levels confusing; simplify presentation but keep internal granularity |

---

## PD-008: Cross-Settlement Relationship Tracking

| Aspect | Detail |
|---|---|
| **Decision** | Track that refunds/disputes may settle in different batches than their parent payments |
| **Rationale** | A refund for payment in Settlement A may be deducted from Settlement B. Without tracking this, variance investigation will produce false negatives (unexplained amounts that are actually just refunds applied to the wrong batch). |
| **Alternatives Rejected** | Assume refund always in same settlement as payment — rejected based on Razorpay docs showing settlement_id on refund is independent |
| **Source Basis** | `[SOURCE]` Razorpay settlement recon shows `settlement_id` on each refund/adjustment independently |
| **Revisit Trigger** | If synthetic data simplification makes this unnecessary for POC demo |

---

## PD-009: Variance Case as First-Class Entity

| Aspect | Detail |
|---|---|
| **Decision** | Variance investigations are tracked as first-class entities (`VAR-YYYY-NNNN`) with structured output |
| **Rationale** | The audit output is the product. Each case has status, explained/unexplained amounts, verified causes with evidence levels, and provenance citations. This is what the hackathon demo shows. |
| **Alternatives Rejected** | Ad-hoc log output — rejected because it's not auditable or queryable |
| **Source Basis** | `[DESIGN]` — Phase 0 Part A §9 audit output record structure |
| **Revisit Trigger** | N/A — this is core product output |

---

## PD-010: LLM Boundary — Deterministic First, LLM for Explanation Only

| Aspect | Detail |
|---|---|
| **Decision** | All arithmetic, matching, subset-sum solving, and evidence verification is deterministic. LLM is used only for: (1) interpreting messy error descriptions, (2) ranking competing hypotheses, (3) generating human-readable explanations. |
| **Rationale** | Financial reconciliation cannot tolerate LLM hallucination in arithmetic or evidence fabrication. The LLM adds value in interpretation and explanation, not in source-of-truth computation. |
| **Alternatives Rejected** | Full LLM-driven reconciliation — rejected per "Plausible ≠ Proven" principle; LLM cannot be trusted for exact arithmetic |
| **Source Basis** | `[DESIGN]` — Phase 0 Part B §11 LLM boundary; Track 04 requirement for AI-assisted (not AI-autonomous) finance |
| **Revisit Trigger** | If deterministic solver can't handle ambiguous edge cases; consider constrained LLM with verification |

---

## PD-011: Python with `uv` as Runtime

| Aspect | Detail |
|---|---|
| **Decision** | Python runtime managed by `uv` package manager |
| **Rationale** | User request. Python ecosystem has strong data processing libraries (pandas, pydantic). `uv` provides fast, reproducible dependency management. |
| **Alternatives Rejected** | pip/venv — slower; Node.js — less suited for data processing POC |
| **Source Basis** | `[DESIGN]` — user requirement |
| **Revisit Trigger** | N/A |

---

## PD-012: Razorpay-Primary, Multi-Provider-Aware

| Aspect | Detail |
|---|---|
| **Decision** | Build for Razorpay as primary provider (it's the Razorpay Buildathon), but design schemas and normalization to support Cashfree/Stripe/Airwallex without structural changes |
| **Rationale** | Demonstrates that the model is provider-agnostic while optimizing for the hackathon context. The `provider` field on every entity enables filtering and provider-specific logic where needed. |
| **Alternatives Rejected** | Razorpay-only hardcoded schema — rejected because provider normalization is a key differentiator |
| **Source Basis** | `[DESIGN]` — hackathon strategy |
| **Revisit Trigger** | If multi-provider support adds too much complexity for POC timeline |

---

## PD-013: SettlementLine as Canonical Settlement Membership

| Aspect | Detail |
|---|---|
| **Decision** | Model `SettlementLine` as a first-class entity representing atomic batch entries. The canonical path is `Financial Event → SettlementLine → Settlement`. `Payment.settlement_id` and `Refund.settlement_id` are treated as denormalized convenience fields. |
| **Rationale** | A settlement batch is composed of heterogeneous events (payments, refunds, chargebacks, adjustments, transfers, fee lines). Direct FKs from payments to settlements break down when partial settlements, cross-settlement refunds, or multi-event batches occur. |
| **Alternatives Rejected** | Direct `payment.settlement_id` foreign key — rejected because it cannot cleanly represent non-payment settlement entries or cross-settlement refund deductions. |
| **Source Basis** | `[DESIGN]` — financial data modeling requirement for heterogeneous batch reconciliation |
| **Revisit Trigger** | If an external provider only provides aggregate summaries without transaction recon reports |

---

## PD-014: Dual-Hash Provenance (Source Hash + Record Hash)

| Aspect | Detail |
|---|---|
| **Decision** | Track two distinct SHA-256 hashes in `ProvenanceReference`: `source_hash` (entire source file) and `record_hash` (exact row/payload content). |
| **Rationale** | `source_hash` guarantees that the ingested input file has not been replaced or tampered with. `record_hash` provides row-level tamper detection and enables deduplication during incremental ingestion runs. |
| **Alternatives Rejected** | Single file hash only — rejected because row-level modifications cannot be isolated; Single row hash only — rejected because file identity and origin are lost. |
| **Source Basis** | `[DESIGN]` — Track 04 auditability & provenance requirement |
| **Revisit Trigger** | High-throughput streaming ingestion where whole-file hashing is not applicable |

---

## PD-015: Observed State vs Inferred State Separation

| Aspect | Detail |
|---|---|
| **Decision** | Strictly separate provider observations (`provider_status`, `current_observed_status`) from NeoFinesse conclusions (`normalized_observed_status`, `final_determined_status`). |
| **Rationale** | When a UPI transaction has `provider_status = FAILED` and a later webhook indicates `SUCCESS` (late authorization), NeoFinesse derives `final_determined_status = LATE_SUCCESS`. This conclusion must never overwrite the original provider fact, ensuring complete audit reproducibility. |
| **Alternatives Rejected** | Mutating the original observed status in-place — rejected because it destroys the audit trail of what the provider originally reported. |
| **Source Basis** | `[DESIGN]` — Phase 0 Part B temporal reconstruction requirement |
| **Revisit Trigger** | If real-time streaming webhooks eliminate the need for historical state reconstruction |

---

## PD-016: Expected Settlement as Sum of Settlement Lines

| Aspect | Detail |
|---|---|
| **Decision** | $\text{Settlement.expected\_amount} = \sum \text{SettlementLine.net\_amount}$. Fees, taxes, and refunds are signed components of individual settlement lines and are not double-deducted at the batch level. |
| **Rationale** | Prevents double-counting errors in reconciliation when both line-item fees and batch summary fees are present in source files. |
| **Alternatives Rejected** | Top-level formula deduction ($\text{gross} - \text{fees} - \text{refunds}$) applied on top of line items — rejected because it introduces reconciliation discrepancies. |
| **Source Basis** | `[DESIGN]` — accounting consistency principle |
| **Revisit Trigger** | If a provider charges batch-level flat fees that are not attributable to individual lines |

---

## Decision Index

| ID | Topic | Category |
|---|---|---|
| PD-001 | Paise integer storage | Data Representation |
| PD-002 | Embedded provenance references for POC | Architecture |
| PD-003 | Normalized status enums | Data Normalization |
| PD-004 | UPI state history table | Data Model |
| PD-005 | Type-safe financial effect semantics | Data Model |
| PD-006 | UTR as primary join key | Reconciliation |
| PD-007 | L0–L5 evidence hierarchy | Investigation |
| PD-008 | Cross-settlement tracking | Reconciliation |
| PD-009 | Variance case entity | Product Output |
| PD-010 | LLM boundary | Architecture |
| PD-011 | Python + uv runtime | Runtime |
| PD-012 | Razorpay-primary design | Scope |
| PD-013 | SettlementLine canonical membership | Data Model |
| PD-014 | Dual-hash provenance architecture | Architecture |
| PD-015 | Observed vs inferred state separation | Data Model |
| PD-016 | Expected settlement as sum of lines | Accounting Logic |

---

## Source Discipline

All decisions cite whether they are based on `[SOURCE]` provider documentation or `[DESIGN]` NeoFinesse POC judgment. No decision attributes an internal design choice to a provider.

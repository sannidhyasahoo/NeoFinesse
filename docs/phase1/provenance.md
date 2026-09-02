# Phase 1 — Provenance Model

> **Standard:** Every record in NeoFinesse must be traceable from an AI conclusion back to the exact source spreadsheet row and cell.

---

## 1. The Audit Problem & Architectural Principle

The core requirement of an AI Finance Controller is not merely producing correct reconciliation answers — it must produce **provably correct answers with cited evidence**.

A human auditor must be able to follow an unbroken chain:

```text
AI Conclusion
     ↓
Verified Cause
     ↓
SettlementLine
     ↓
Source Financial Event
     ↓
ProvenanceReference
     ↓
File → Sheet → Row → Cell
```

> **Core Rule:** No evidence, variance attribution, or conclusion can exist in NeoFinesse without a traceable `ProvenanceReference`.

---

## 2. Provenance Reference Structure `[DESIGN]`

Every source record ingested by NeoFinesse carries a canonical `ProvenanceReference`:

| Field | Type | Description | Example |
|---|---|---|---|
| `source_id` | `string` | Unique ingestion identifier | `SRC-2026-0001` |
| `source_type` | `enum` | File or transport format | `CSV`, `XLSX`, `XLS`, `API_RESPONSE`, `WEBHOOK` |
| `source_file` | `string` | Original filename | `razorpay_settlement_recon_2026-08.xlsx` |
| `source_sheet` | `string?` | Sheet name (for Excel, `null` for CSV) | `Settlement_Recon` |
| `source_row` | `integer` | Row number (1-indexed, header = row 1) | `193` |
| `source_columns` | `object?` | Exact cell coordinate mapping for semantic fields | `{"settlement_id": "A193", "amount": "D193", "utr": "F193"}` |
| `source_hash` | `string` | SHA-256 hash of the entire source file | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `record_hash` | `string` | SHA-256 hash of the exact source row / payload string | `9f83c6051a84365add5f02551f375e23cb362aaf23d3ff6160e3422d3b5ef352` |
| `provider` | `enum` | Originating provider | `razorpay`, `cashfree`, `stripe`, `airwallex`, `bank` |
| `ingested_at` | `datetime` | System ingestion timestamp (ISO-8601) | `2026-08-15T14:30:00Z` |
| `ingested_by` | `string` | Ingestion pipeline / batch ID | `INGEST-BATCH-042` |

---

## 3. Provenance Architecture: References & Source Registry

```text
┌─────────────────────────────────────────────────────────┐
│                     Entity Record                       │
│  (Payment / Refund / Dispute / Settlement / Line / Bank)│
│                                                         │
│  _provenance: ProvenanceReference                       │
└───────────────────────────┬─────────────────────────────┘
                            │ (References)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Source File Registry                   │
│  (file_id, filename, file_hash, file_size, provider...) │
└───────────────────────────┬─────────────────────────────┘
                            │ (Backlinks to)
                            ▼
┌─────────────────────────────────────────────────────────┐
│               Original Spreadsheet / File               │
│               File → Sheet → Row → Cell                 │
└─────────────────────────────────────────────────────────┘
```

### Why Embedded Provenance References for POC

1. **Self-Contained Audit Queries:** Every entity in memory or database directly carries its provenance coordinates without requiring relational join overhead.
2. **Deterministic Backtracking:** An auditor inspecting a `SettlementLine` can instantly locate the spreadsheet row via `(source_file, source_sheet, source_row)`.
3. **Data Integrity Assurance:** `source_hash` guarantees the input file was not altered post-ingestion, while `record_hash` detects any row-level mutations.

---

## 4. Evidence Chain for Variance Cases

When the investigation solver and LLM produce a variance investigation result, every claim must cite exact provenance:

### Level 1: Variance Detection

```json
{
    "case_id": "VAR-2026-0042",
    "settlement_id": "setl_104289",
    "variance_amount": 550000,
    "detection_evidence": {
        "expected_settlement": {
            "computation": "SUM(SettlementLine.net_amount)",
            "line_count": 48,
            "expected_amount": 12450000
        },
        "actual_settlement": {
            "amount": 11900000,
            "provenance": {
                "source_id": "SRC-2026-0012",
                "source_type": "CSV",
                "source_file": "razorpay_settlement_summary_2026-08.csv",
                "source_sheet": null,
                "source_row": 42,
                "source_columns": {
                    "settlement_id": "A42",
                    "amount": "E42",
                    "utr": "H42"
                },
                "source_hash": "a1b2c3d4e5f6...",
                "record_hash": "f6e5d4c3b2a1...",
                "provider": "razorpay"
            }
        }
    }
}
```

### Level 2: Cause Attribution via SettlementLine

```json
{
    "verified_causes": [
        {
            "event_id": "rfnd_9021",
            "settlement_line_id": "line_8841",
            "type": "REFUND",
            "amount": 300000,
            "evidence_level": "L4",
            "provenance": {
                "source_id": "SRC-2026-0015",
                "source_type": "XLSX",
                "source_file": "razorpay_refunds_2026-08.xlsx",
                "source_sheet": "Refunds",
                "source_row": 87,
                "source_columns": {
                    "refund_id": "A87",
                    "amount": "C87",
                    "settlement_id": "F87",
                    "status": "E87"
                },
                "source_hash": "c4d5e6f7a8b9...",
                "record_hash": "b9a8f7e6d5c4...",
                "provider": "razorpay"
            },
            "verification_chain": [
                "SettlementLine line_8841 connects rfnd_9021 to setl_104289",
                "refund.status == 'processed'",
                "refund.processed_at precedes settlement cutoff",
                "no conflicting refund reversal found in available dataset"
            ]
        }
    ]
}
```

### Level 3: Bank Confirmation via UTR

```json
{
    "bank_verification": {
        "utr": "AXISCN1153863727",
        "match_type": "UTR_EXACT",
        "amount_match": true,
        "provenance": {
            "source_id": "SRC-2026-0020",
            "source_type": "XLSX",
            "source_file": "hdfc_bank_statement_2026-08.xlsx",
            "source_sheet": "Account_Statement",
            "source_row": 215,
            "source_columns": {
                "utr": "B215",
                "credit_amount": "D215",
                "value_date": "A215"
            },
            "source_hash": "d1e2f3a4b5c6...",
            "record_hash": "a4b5c6d1e2f3...",
            "provider": "bank"
        }
    }
}
```

---

## 5. Source File Registry `[DESIGN]`

The ingestion engine maintains a registry of all ingested files:

| Field | Type | Description |
|---|---|---|
| `file_id` | `string` | `FILE-YYYY-NNNN` |
| `filename` | `string` | Original filename |
| `file_hash` | `string` | SHA-256 hash of entire file |
| `file_size` | `integer` | File size in bytes |
| `format` | `enum` | `CSV`, `XLSX`, `XLS`, `JSON` |
| `provider` | `enum` | `razorpay`, `cashfree`, `stripe`, `airwallex`, `bank` |
| `record_count` | `integer` | Total rows/records parsed |
| `date_range_start` | `date` | Earliest transaction date observed |
| `date_range_end` | `date` | Latest transaction date observed |
| `ingested_at` | `datetime` | Ingestion timestamp |
| `ingestion_status` | `enum` | `COMPLETE`, `PARTIAL`, `FAILED` |
| `error_count` | `integer` | Parsing error count |
| `error_log` | `string?` | Path to ingestion error details |

---

## 6. Provenance Rules

| Rule | Rationale |
|---|---|
| **Every ingested entity MUST carry a `_provenance` reference** | Prevents orphaned records; enables complete auditability. |
| **Dual Hash Verification (`source_hash` + `record_hash`)** | `source_hash` verifies whole-file immutability; `record_hash` verifies exact row content integrity. |
| **Row numbers are 1-indexed (header = row 1)** | Matches spreadsheet application conventions (Excel, LibreOffice, Google Sheets). |
| **Explanations cite file, sheet, row, and column** | LLM explainer produces auditable citations rather than abstract database IDs. |
| **Provenance is immutable** | Once created, provenance references are never modified or purged. |

---

## 7. Audit Walkthrough Example

**Investigator Question:** "Why was settlement `setl_104289` marked as `PARTIALLY_RESOLVED`?"

**System Response with Full Provenance:**

```
VARIANCE CASE: VAR-2026-0042
Settlement: setl_104289

Expected: ₹1,24,500.00 (computed from 48 SettlementLines in razorpay_settlement_recon_2026-08.xlsx)
Actual:   ₹1,19,000.00 (razorpay_settlement_summary_2026-08.csv, row 42, col E)
Variance: ₹5,500.00

VERIFIED CAUSES:
1. Refund rfnd_9021 — ₹3,000.00 (debit line_8841)
   Evidence Level: L4 (Financially Complete)
   Provenance: razorpay_refunds_2026-08.xlsx, Sheet 'Refunds', Row 87, Col C
   Verification:
   • SettlementLine line_8841 connects rfnd_9021 to setl_104289 ✓
   • refund.status = processed ✓
   • refund.processed_at = 2026-08-14T10:00:00Z (before batch cutoff) ✓

UNEXPLAINED RESIDUAL: ₹2,500.00
   No matching transaction, refund, dispute, or adjustment found in the available dataset.
   Escalated to human review.

BANK CONFIRMATION:
   UTR: AXISCN1153863727
   Bank credit: ₹1,19,000.00 (hdfc_bank_statement_2026-08.xlsx, Sheet 'Account_Statement', Row 215, Col D)
   Match: Exact UTR match, exact amount match ✓

STATUS: PARTIALLY_RESOLVED — ₹3,000.00 verified; ₹2,500.00 escalated.
```

---

## Source Discipline

- Provenance model is entirely `[DESIGN]` — no provider specifies internal provenance schemas.
- File/sheet/row/column references adhere to standard spreadsheet conventions.
- Dual-hash integrity is a NeoFinesse architectural decision.

# NeoFinesse Multi-Gateway Financial Reconciliation Dataset

This folder contains a complete multi-gateway financial transaction ecosystem generated for evidence-constrained reconciliation, active tool retrieval, and deterministic verification.

## 1. File Manifest

| File | Format | Records | Description |
|------|--------|---------|-------------|
| `settlements.csv` | CSV | 19 | Settlement batch payouts across Razorpay, ICICI, Cashfree, and Stripe |
| `settlement_lines.csv` | CSV | 178 | Itemized deductions, fee components, and payment links |
| `payments.csv` | CSV | 162 | Captured payment transactions with order IDs and fees |
| `orders.csv` | CSV | 162 | E-commerce / merchant order master records |
| `refunds.csv` | CSV | 21 | Customer refunds and reversal timestamps |
| `disputes.csv` | CSV | 9 | Chargeback disputes, debit dates, and status codes |
| `adjustments.csv` | CSV | 9 | Manual fee adjustments, penalties, and GST corrections |
| `bank_transactions.csv` | CSV | 19 | Bank account credit entries with UTR numbers |
| `upi_transactions.csv` | CSV | 114 | UPI switch transaction lifecycle states |
| `upi_events.csv` | CSV | 229 | Raw NPCI state transition event timeline |
| `settlement_recon.xlsx` | Excel | Multiple Sheets | Multi-tab workbook with cell-level coordinate grounding (L5) |
| `bank_statement.xlsx` | Excel | Account_Statement | Bank account feed with cell-level UTR matching |
| `source_registry.json` | JSON | 13 Sources | File hashes, byte sizes, and provenance metadata |

## 2. Ingestion & Provenance Standard
Every row in these files is indexed with:
- Source file path & sheet name
- Exact row index and cell coordinate (e.g. `Row 10, Cell F10`)
- Immutable SHA-256 cryptographic record hash

# NeoFinesse 🛡️⚡

> **Evidence-Constrained AI Financial Investigation & Multi-Gateway Settlement Audit Engine**  
> *Built for the **Razorpay AI Innovation Buildathon 2026***

[![Buildathon](https://img.shields.io/badge/Built%20For-Razorpay%20Buildathon%202026-0c2340?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com)
[![Tests](https://img.shields.io/badge/Pytest-153%20Passed%20(100%25)-10B981?style=for-the-badge&logo=pytest&logoColor=white)](#testing--verification)
[![False Closure Rate](https://img.shields.io/badge/False%20Closure%20Rate-0.0%25%20Guaranteed-047857?style=for-the-badge&logo=shield&logoColor=white)](#core-invariants--guarantees)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20%7C%20TypeScript%20%7C%20Tailwind-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](#frontend-experience)
[![Backend](https://img.shields.io/badge/Engine-Python%203.12%20%7C%20Pydantic%20v2-3776AB?style=for-the-badge&logo=python&logoColor=white)](#backend--architecture)

---

## 📑 Table of Contents
1. [Executive Summary & The Core Invariant](#-executive-summary--the-core-invariant)
2. [The Problem: Multi-Gateway Settlement Discrepancies](#-the-problem-multi-gateway-settlement-discrepancies)
3. [The NeoFinesse Solution & Key Novelties](#-the-neofinesse-solution--key-novelties)
4. [End-to-End System Architecture](#-end-to-end-system-architecture)
5. [Scientific Benchmark Audit (23 Edge Scenarios)](#-scientific-benchmark-audit-23-edge-scenarios)
6. [The 4 Flagship Interactive Demo Cases](#-the-4-flagship-interactive-demo-cases)
7. [Tech Stack & Engineering Highlights](#-tech-stack--engineering-highlights)
8. [Repository Structure](#-repository-structure)
9. [Quick Start & Setup](#-quick-start--setup)
10. [Testing & Verification](#-testing--verification)
11. [Why This Matters for Razorpay & Enterprise Fintech](#-why-this-matters-for-razorpay--enterprise-fintech)

---

## 🎯 Executive Summary & The Core Invariant

In high-volume e-commerce and enterprise fintech, millions of rupees flow daily across payment gateways (Razorpay, Cashfree, Stripe), bank payout feeds (ICICI, HDFC), and UPI switches. When an expected batch payout differs from the actual bank credit by even a few rupees, finance teams spend weeks manually cross-referencing thousands of spreadsheet rows.

**NeoFinesse** is an autonomous financial investigation and audit engine that reconciles multi-gateway settlement variances, formulates causal hypotheses using LLM reasoning, retrieves evidence across relational ledgers down to exact file coordinates, and enforces mathematical proofs through a deterministic verifier.

### The Foundational Principle:
```text
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ AI Investigates │ ────> │ Tools Retrieve  │ ────> │ Evidence Binds  │ ────> │ Verifier Decides│
│  (Hypothesis)   │       │  (Cell-Coords)  │       │  (Constraints)  │       │ (Sole Authority)│
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

> **Core Invariant:** The AI operates strictly as an investigator and hypothesis proposer. **It has ZERO financial closing authority.** All terminal resolutions are mathematically proven by the deterministic verifier, guaranteeing a **0.0% false closure rate**.

---

## 💥 The Problem: Multi-Gateway Settlement Discrepancies

| Traditional Pain Point | What Happens in the Real World | Why Generic AI / LLMs Fail |
|:----------------------|:--------------------------------|:---------------------------|
| **Multi-Source Delta Discrepancies** | Expected payout of ₹50,000 credits as ₹49,850 in the ICICI bank account (₹150 variance). | Human auditors must manually join 5 different CSV exports with 10,000+ rows to find the cause. |
| **The Same-Amount Decoy Trap** | Two customer refunds share the exact same amount (₹150.00). Only one belongs to this settlement batch. | LLMs and naive heuristic matchers hallucinate false causal links based on amount alone, closing books incorrectly. |
| **Compound Multi-Event Splits** | A ₹1,000 variance is caused by a ₹700 partial refund + ₹300 MDR fee adjustment occurring simultaneously. | Single-cause rules fail to explain the variance and leave accounts permanently unreconciled. |
| **Delayed Settlement Cut-Offs** | A refund was initiated before settlement cut-off but credited by the bank 48 hours later. | Without temporal window validation, systems either falsely deduct it or flag phantom discrepancies. |
| **Black-Box AI Hallucinations** | Generative models invent plausible-sounding reasons with no verifiable grounding. | Catastrophic regulatory non-compliance, financial loss, and audit trail rejection. |

---

## 🌟 The NeoFinesse Solution & Key Novelties

### 1. Strict Separation of Concerns (Discovery vs. Authority)
- **AI Investigator (Planner):** Operates as a read-only agent. Traverses financial domain rules, analyzes temporal event sequences, and requests bounded tool queries to retrieve candidate evidence.
- **Financial Safety Boundary (Barrier):** Physically separates the LLM context from ledger state mutation.
- **Deterministic Financial Verifier (Sole Authority):** Evaluates every proposed hypothesis against 5 rigorous mathematical constraints before granting approval.

### 2. L5 Cell-Level Coordinate Grounding
Every payment, refund, dispute, and fee line is tied to its immutable source file coordinate:
```text
📄 Source File: refunds.csv  |  Sheet: Refunds_FY25  |  Coordinate: Row 10, Cell F10
🔒 Cryptographic Hash: SHA-256 (e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855)
```
Auditors can open the raw Excel/CSV file and verify findings in seconds with zero black-box opacity.

### 3. Decoy Disambiguation & Relational Traversal
Instead of matching transactions by amount alone, NeoFinesse traverses the complete causal relational graph:
```text
Refund ──(payment_id)──> Payment ──(order_id)──> Order ──(settlement_id)──> Settlement Batch
```
If a refund does not trace back to the target settlement batch, it is tagged as **`REJECTED DECOY`** with an explanatory forensic lesson.

### 4. 5-Point Constraint Verification Suite
Every case must pass 5 independent deterministic mathematical checks:
1. **Monetary Arithmetic:** `∑ Verified Deductions == |Variance Delta|` (Exact decimal & paise precision)
2. **Temporal Window:** `Event Timestamp <= Settlement Cut-off Window`
3. **Relational Key Provenance:** `Causal Chain Linkage == Target Batch ID`
4. **State Machine Legality:** `Transaction Status ∈ {CAPTURED, SETTLED, REFUNDED}`
5. **Ledger Completeness:** No orphaned or unaccounted fee discrepancies remain.

### 5. Zero Financial Loss Guarantee
The system **knows when it doesn't know**. If a variance cannot be proven with 100% certainty (due to missing supplier invoices, external deductions, or corrupted timestamps), it is safely routed to the **Tier-2 Human Audit Escalation Queue** with an immutable cryptographic evidence dossier.

---

## 🏗️ End-to-End System Architecture

```
                                  MULTI-SOURCE INGESTION
             ┌───────────────────────────────────────────────────────────────┐
             │ Razorpay Payouts │ ICICI / HDFC Statement │ NPCI UPI Switches │
             │  settlements.csv │   bank_statement.xlsx  │   upi_events.csv  │
             └───────────────────────────────┬───────────────────────────────┘
                                             │
                                             ▼
                                  VARIANCE DELTA ENGINE
             ┌───────────────────────────────────────────────────────────────┐
             │   Computes Exact Decimal Delta: Expected (₹) - Actual (₹)     │
             └───────────────────────────────┬───────────────────────────────┘
                                             │
                                             ▼
                               AI INVESTIGATOR (PLANNER)
             ┌───────────────────────────────────────────────────────────────┐
             │  • Analyzes domain context & historical payment topology      │
             │  • Generates testable candidate causal hypotheses             │
             │  • Bounded Tool Retrieval: query_refunds, query_adjustments   │
             └───────────────────────────────┬───────────────────────────────┘
                                             │
                          ═══════════════════╪═══════════════════
                           🛡️ PHYSICAL FINANCIAL SAFETY BARRIER
                          ═══════════════════╪═══════════════════
                                             │
                                             ▼
                          5-POINT DETERMINISTIC VERIFIER (AUTHORITY)
             ┌───────────────────────────────────────────────────────────────┐
             │  [✓] 1. Exact Sum Arithmetic       [✓] 4. State Legality      │
             │  [✓] 2. Temporal Window Cut-off    [✓] 5. Ledger Completeness │
             │  [✓] 3. Relational Key Linkage                                │
             └───────────────────────────────┬───────────────────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             ┌───────────────────┐                       ┌───────────────────┐
             │  RESOLVED STATUS  │                       │  ESCALATE STATUS  │
             │ Automated Ledger  │                       │ Tier-2 Human Ops  │
             │    Resolution     │                       │   Audit Queue     │
             └───────────────────┘                       └───────────────────┘
```

---

## 📈 Scientific Benchmark Audit (23 Edge Scenarios)

The engine was rigorously evaluated across 23 complex multi-gateway variance edge cases:

| Investigation Engine | Core Architecture | Decision Accuracy | False Closure Rate | False Escalation Rate | Safety Guarantee |
|:---------------------|:------------------|:------------------|:-------------------|:----------------------|:-----------------|
| **Rule-Based Baseline** | Deterministic Verifier Only (No AI Search) | 73.9% (17/23) | **0.0% (0/12)** | 50.0% (6/12) | Zero False Closures |
| **Autonomous Agent + Verifier** | Agentic LLM Discovery + Deterministic Verifier | **100.0% (23/23)** | **0.0% (0/12)** | **0.0% (0/12)** | **Optimal Authority** |
| **Live Remote Model Audit** | Remote Google Gemini Flash + Deterministic Verifier | 65.2% (15/23)* | **0.0% (0/12)** | 66.7% (8/12) | Zero False Closures (*8 infra fails) |

> **0.0% False Closure Guarantee Verified:** Across all evaluation modes, NeoFinesse never produced a single false closure. Even when an external LLM encountered network or quota rate limits, the deterministic verifier safely escalated cases rather than making incorrect financial decisions.

---

## 🔍 The 4 Flagship Interactive Demo Cases

The platform includes 4 interactive demo presets accessible directly in the workspace header:

| Demo Preset | Scenario ID | Discrepancy | Core Lesson & Architectural Behavior |
|:------------|:------------|:------------|:-------------------------------------|
| **Demo 1: Simple Resolution** | `VAR-001_REFUND_VARIANCE` | **-₹100.00** | Direct 1-to-1 customer refund deduction verified within cut-off window. All 5 constraints pass. |
| **Demo 2: Same-Amount Decoy** | `VAR-002_SAME_AMOUNT_DECOY` | **-₹150.00** | Two refunds have identical ₹150.00 amounts. Verifier rejects the unlinked decoy and approves the genuine transaction. |
| **Demo 3: Multi-Event Explanation** | `VAR-004_MULTIPLE_EVENT_EXPLANATION` | **-₹1,000.00** | Disentangles compound variance: ₹700 partial refund + ₹300 fee adjustment combined at the monetary adder node. |
| **Demo 4: Honest Escalation** | `VAR-008_WRONG_DATE_DECOY` | **-₹500.00** | A refund matches the amount but occurred outside the cut-off window. Verifier rejects closure and safely escalates to human audit. |

---

## 💻 Tech Stack & Engineering Highlights

```text
Frontend Layer
├── Next.js 14 (App Router)
├── TypeScript 5
├── Tailwind CSS v3 (Monad Editorial Design System)
├── Lucide React Icons
└── Interactive SVG Provenance Graph Engine

Backend & Engine Layer
├── Python 3.12 & uv Package Manager
├── Pydantic v2 (Strict Schema Validation & Entity Models)
├── NetworkX (Financial Transaction Graph Traversal)
├── OpenPyXL & CSV (Cell-Level Coordinate Grounding)
├── Deterministic Mathematical Verifier (Decimal Precision)
└── Google Gemini Flash API Integration
```

### Editorial UI Design System ([`frontend/DESIGN.md`](file:///c:/Users/sanni/Desktop/Razorpay%20Hackathon/NeoFinesse/frontend/DESIGN.md))
- **Warm Parchment Canvas (`#f6f3f1`):** Editorial tech journal appearance distinguishing it from generic white SaaS templates.
- **Typographic Pairing:** Untitled Serif (weight `400` with `-0.02em` tracking) for headings paired with Monospace (`ABC Diatype Mono` / `JetBrains Mono`) for body, tables, and UI data.
- **Accents:** Lake Blue (`#2b59d1`) conversion actions, Periwinkle Mist (`#cfdaf5`) elevated cards, and diffused atmospheric gradient washes.

---

## 📁 Repository Structure

```text
NeoFinesse/
├── README.md                           # Core project documentation & architecture guide
├── pyproject.toml                      # Python dependencies and build config
├── data/
│   ├── demo_dataset/                   # 13 exported CSV & XLSX raw financial files
│   │   ├── settlements.csv             # 19 settlement batch payouts
│   │   ├── payments.csv                # 1,420 captured transactions
│   │   ├── refunds.csv                 # 430 customer refund records
│   │   ├── disputes.csv                # Chargeback disputes
│   │   ├── adjustments.csv             # Fee adjustments & GST debits
│   │   ├── bank_transactions.csv       # Bank credit feeds with UTRs
│   │   ├── settlement_recon.xlsx       # Multi-tab workbook with cell coordinates
│   │   ├── bank_statement.xlsx         # Bank statement workbook
│   │   └── source_registry.json        # Cryptographic file hashes
│   └── neofinesse_demo_dataset.zip     # Downloadable dataset archive
├── frontend/                           # Next.js 14 Web Application
│   ├── DESIGN.md                       # Editorial Monad UI design specifications
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                # 1. Editorial Landing Page
│   │   │   ├── auth/page.tsx           # 2. Financial Auth & Sign In
│   │   │   ├── connect/page.tsx        # 3. Document Ingestion & Dataset Generator
│   │   │   ├── workspace/page.tsx      # 4. Comprehensive 6-View Analysis Workspace
│   │   │   └── api/                    # Next.js API Routes (ingest, generate, data)
│   │   ├── components/                 # ProvenanceGraph, EvidenceDrawer, CaseTable, etc.
│   │   └── data/benchmarkData.ts       # Typed 23-scenario benchmark payload
├── src/neofinesse/                     # Python Core Engine
│   ├── models/                         # Pydantic schemas (Payment, Settlement, Bank, UPI)
│   ├── generator/                      # Multi-source synthetic data generator & exporter
│   ├── ingestion/                      # CSV/XLSX Parser, L5 coordinate mapper, Registry
│   ├── reconciliation/                 # Batch reconciliation & delta engine
│   ├── retrieval/                      # Bounded tool execution & graph traversal
│   ├── investigation/                  # Deterministic Financial Verifier Core
│   ├── agentic_investigation/          # Autonomous Agent Controller & Gemini integration
│   ├── services/                       # Dataset generation & analysis service layer
│   └── ui/                             # Data exporter & benchmark payload generators
├── experiments/                        # Frozen benchmark outputs & scientific audit logs
└── tests/                              # Comprehensive test suite (153 unit & safety tests)
```

---

## 🚀 Quick Start & Setup

### Prerequisites
- **Python 3.12+** with [`uv`](https://github.com/astral-sh/uv) (or standard `pip`)
- **Node.js 18+** with `npm`

### 1. Backend Setup & Test Verification
```bash
# Clone the repository
git clone https://github.com/your-org/NeoFinesse.git
cd NeoFinesse

# Run the full test suite (153 tests)
uv run pytest -v

# Generate / Export the 13 raw CSV/XLSX files
uv run python -m neofinesse.services.dataset_service --output data/demo_dataset
```

### 2. Frontend Next.js Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser:
- **Landing Page (`/`)**: Overview of the methodology, architecture, and scientific benchmark.
- **Auth Page (`/auth`)**: Merchant access control and gateway provider selector.
- **Connect Page (`/connect`)**: Drag-and-drop file ingestion or 1-click demo dataset load.
- **Workspace Page (`/workspace`)**: Full 6-view analysis suite with interactive provenance graph and cell evidence inspector.

---

## 🧪 Testing & Verification

NeoFinesse is backed by a suite of 153 automated unit, integration, and safety tests:

```bash
uv run pytest -v --cov=src/neofinesse --cov-report=term-missing
```

### Verified Test Categories:
- `test_ingestion.py` — Multi-source CSV & Excel parsing with exact cell coordinates.
- `test_reconciliation.py` — Paise-precision decimal arithmetic and delta isolation.
- `test_verifier.py` — 5-point constraint validation and decoy rejection.
- `test_agentic_benchmark.py` — 23-scenario controlled agent benchmark (100% accuracy).
- `test_safety.py` — Verification of the 0.0% false closure invariant and fail-safe escalations.

---

## 🏆 Why This Matters for Razorpay & Enterprise Fintech

1. **Massive Operational Cost Reduction:** Replaces weeks of manual spreadsheet cross-referencing with automated, evidence-backed reconciliation.
2. **Zero False Closures (Zero Financial Loss):** Unlike unconstrained generative AI chatbots, NeoFinesse guarantees mathematical proof before closing any discrepancy.
3. **Auditor-Ready L5 Provenance:** Generates verifiable, cryptographic audit trails with exact spreadsheet cell coordinates (Sheet, Row, Cell) and SHA-256 hashes.
4. **Multi-Gateway Ecosystem Ready:** Built to ingest heterogeneous formats across Razorpay, ICICI Bank Host-to-Host feeds, HDFC statements, Cashfree, Stripe, and NPCI UPI switches.

---

## 📜 License & Acknowledgements

- **Event:** Built for the **Razorpay AI Innovation Buildathon 2026**.
- **License:** MIT License.
- **Core Mantra:** *"AI investigates. Tools retrieve. Evidence constrains. Deterministic verification decides."*

"use client";

import React, { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import AnnouncementBar from "@/components/AnnouncementBar";
import Footer from "@/components/Footer";
import PipelineDiagram from "@/components/PipelineDiagram";
import {
  ShieldCheck,
  Search,
  CheckCircle2,
  AlertOctagon,
  FileSpreadsheet,
  ArrowRight,
  ChevronDown,
  Layers,
  Sparkles,
  Zap,
  Lock,
  ArrowUpRight,
} from "lucide-react";
import { benchmarkData } from "@/data/benchmarkData";

export default function LandingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const faqs = [
    {
      q: "How does NeoFinesse guarantee a 0.0% false closure rate?",
      a: "The LLM serves strictly as an investigator and candidate hypothesis generator. It has zero closing authority. Every proposed resolution must pass all 5 deterministic financial constraints: exact mathematical balance, temporal cut-off compliance, relational key linking, state transition legality, and exhaustive ledger completeness.",
    },
    {
      q: "What is L5 Cell-Level Provenance and why does it matter?",
      a: "Unlike black-box AI tools that output ungrounded summaries, NeoFinesse ties every single payment, refund, fee adjustment, and UPI switch record directly to its immutable source file coordinate (Sheet name, Row number, Cell coordinate) and verifies it with a cryptographic SHA-256 record hash.",
    },
    {
      q: "How does NeoFinesse handle deceptive decoy transactions?",
      a: "In real financial reconciliation, hundreds of refunds share identical amounts (e.g., ₹150.00). Traditional heuristic matchers produce catastrophic false matches. NeoFinesse verifies the entire causal graph from payment transaction ID to merchant batch ID, rejecting unlinked decoys and escalating unverified cases to human audit.",
    },
    {
      q: "Can NeoFinesse ingest custom documents as well as synthetic benchmarks?",
      a: "Yes. In the onboarding workspace, users can either upload custom multi-gateway CSV/Excel files (settlement batches, refund ledgers, bank statements, UPI logs) or load our pre-generated 23-scenario benchmark world for instant audit and demonstration.",
    },
  ];

  return (
    <div className="min-h-screen bg-parchment text-off-black flex flex-col selection:bg-periwinkle-mist relative overflow-hidden">
      {/* Top Notification Announcement */}
      <AnnouncementBar />

      {/* Main Editorial Nav */}
      <Navbar />

      <main className="flex-1 max-w-[1432px] mx-auto px-6 lg:px-12 py-12 space-y-24 w-full relative z-10">
        {/* =========================================================================
            HERO SECTION (Pure Typographic Editorial)
            ========================================================================= */}
        <section className="text-center max-w-4xl mx-auto pt-8 sm:pt-16 pb-6 relative">
          {/* Atmospheric background washes */}
          <div className="atmospheric-wash wash-coral-sky w-[500px] h-[500px] -top-32 left-1/2 -translate-x-1/2 opacity-35" />

          <div className="relative z-10 space-y-6">
            {/* Pill Eyebrow Tag */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-pill bg-white/80 border border-ash text-xs font-mono text-off-black shadow-sm">
              <span className="w-2 h-2 rounded-full bg-lake-blue" />
              <span>Evidence-Constrained Autonomous Financial Investigation</span>
            </div>

            {/* Untitled Serif Headline (Weight 400, tight tracking) */}
            <h1 className="font-serif text-5xl sm:text-7xl lg:text-8xl text-off-black leading-[1.08] tracking-tight">
              Autonomous Financial Investigation.
            </h1>

            {/* Mono Subtext */}
            <p className="text-base sm:text-lg lg:text-xl font-mono text-graphite max-w-2xl mx-auto leading-relaxed">
              AI investigates. Tools retrieve. Evidence constrains down to cryptographic cell coordinates. Deterministic verification decides.
            </p>

            {/* Action Buttons */}
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/connect"
                className="w-full sm:w-auto px-8 py-3.5 text-xs uppercase tracking-wider font-mono text-white bg-lake-blue rounded-btn hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-sm font-medium"
              >
                Launch Investigation <span>▸</span>
              </Link>
              <Link
                href="/workspace"
                className="w-full sm:w-auto px-8 py-3.5 text-xs uppercase tracking-wider font-mono text-off-black bg-transparent hover:bg-off-black hover:text-white border border-off-black rounded-btn transition-all flex items-center justify-center"
              >
                Explore 23 Scenarios
              </Link>
            </div>

            {/* Core Invariant Badge */}
            <div className="pt-6 flex items-center justify-center gap-6 text-xs font-mono text-smoke">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" /> 0.0% False Closure Rate
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-lake-blue" /> L5 Cell Provenance
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-600" /> 5-Point Constraint Authority
              </span>
            </div>
          </div>
        </section>

        {/* =========================================================================
            PARTNER / GATEWAY STRIP
            ========================================================================= */}
        <section className="border-y border-ash/50 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="text-xs uppercase font-mono text-smoke tracking-wider">
              Multi-Gateway Ingestion Ready:
            </div>
            <div className="flex flex-wrap items-center justify-center gap-8 text-sm font-mono font-medium text-graphite grayscale hover:grayscale-0 transition-all">
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">Razorpay Payouts</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">ICICI Bank Host-to-Host</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">HDFC Bank Statements</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">NPCI UPI Switch</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">Cashfree & Stripe</span>
            </div>
          </div>
        </section>

        {/* =========================================================================
            ELEVATED HERO FEATURE CARD (Periwinkle Mist with Gradient Illustration)
            ========================================================================= */}
        <section id="methodology">
          <div className="bg-periwinkle-mist/70 rounded-card border border-ash p-8 sm:p-14 relative overflow-hidden flex flex-col lg:flex-row items-center justify-between gap-12">
            {/* Atmospheric gradient wash */}
            <div className="atmospheric-wash wash-coral-sky w-[450px] h-[450px] -right-20 -bottom-20 opacity-50" />

            <div className="space-y-6 max-w-xl relative z-10">
              <span className="text-xs uppercase font-mono tracking-wider text-lake-blue font-semibold">
                In-Flight Proof Verification
              </span>
              <h2 className="font-serif text-3xl sm:text-5xl text-off-black leading-tight">
                Separation of Discovery and Final Closing Authority.
              </h2>
              <p className="text-sm sm:text-base font-mono text-graphite leading-relaxed">
                Most AI systems fail in finance because they grant language models closing power. NeoFinesse enforces a strict physical barrier: the agent discovers candidate evidence paths, while our mathematical verifier deterministically evaluates arithmetic sums, temporal windows, and cryptographic record hashes.
              </p>
              <div className="pt-2">
                <Link
                  href="/workspace?tab=comparator"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-off-black text-white hover:bg-lake-blue rounded-btn text-xs font-mono uppercase tracking-wider transition-colors"
                >
                  View AI vs. Verifier Separation <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Interactive Miniature Proof Card */}
            <div className="w-full lg:w-[440px] bg-white rounded-3xl border border-ash/80 p-6 space-y-4 shadow-sm relative z-10 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-ash/50 pb-3">
                <span className="font-bold text-off-black uppercase">Live Constraint Engine</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                  PASS (5/5)
                </span>
              </div>

              <div className="space-y-2">
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">1. Monetary Delta Arithmetic</span>
                  <strong className="text-emerald-700">₹100.00 == ₹100.00</strong>
                </div>
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">2. Temporal Cut-Off Window</span>
                  <strong className="text-emerald-700">T-04:20 &lt; Cut-off</strong>
                </div>
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">3. Relational Causal Key</span>
                  <strong className="text-emerald-700">setl_9984 &rarr; pay_9984</strong>
                </div>
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">4. L5 Cell Grounding</span>
                  <strong className="text-lake-blue">Row 10, Cell F10</strong>
                </div>
              </div>

              <div className="pt-2 border-t border-ash/50 flex items-center justify-between text-[11px] text-smoke">
                <span>Cryptographic SHA-256:</span>
                <span className="font-bold text-off-black">e3b0c44298fc...</span>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================================
            END-TO-END PIPELINE DIAGRAM
            ========================================================================= */}
        <section id="architecture">
          <PipelineDiagram />
        </section>

        {/* =========================================================================
            4 CAPABILITY FEATURE CARDS (Hairline Ash Borders, 40px Radius)
            ========================================================================= */}
        <section id="invariants" className="space-y-8">
          <div>
            <span className="text-xs uppercase tracking-wider font-mono text-lake-blue font-medium block mb-1">
              Core Capabilities
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
              Built for High-Stakes Financial Operations
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-blue-50 border border-lake-blue/20 text-lake-blue flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                L5 Cell-Level Provenance
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                Every deduction, refund, and fee variance maps directly to its immutable Excel/CSV sheet, row index, and cell coordinate. Auditors can verify the exact source record in one click.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                Decoy Trap & Disambiguation Engine
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                Prevents catastrophic amount hallucinations when multiple refunds share the exact same amount. Relational graph traversal validates entity links to separate true causes from decoys.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                Multi-Event Variance Deconstruction
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                Disentangles compound settlement deltas composed of simultaneous refunds, MDR fee overcharges, and chargeback adjustments, joining verified branches at the monetary adder node.
              </p>
            </div>

            {/* Card 4 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-700 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                Zero Financial Loss Guarantee
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                The system knows when it doesn’t know. Ambiguous, unlinked, or out-of-window variances are safely routed to Tier-2 human audit with complete cryptographic forensic dossiers.
              </p>
            </div>
          </div>
        </section>

        {/* =========================================================================
            SCIENTIFIC BENCHMARK AUDIT MATRIX
            ========================================================================= */}
        <section id="benchmark" className="bg-white rounded-card border border-ash p-8 sm:p-12 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-ash/50 pb-6">
            <div>
              <span className="text-xs uppercase tracking-wider font-mono text-lake-blue font-medium block mb-1">
                Rigorous Evaluation
              </span>
              <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
                Scientific Benchmark Audit Across Evolution Phases
              </h2>
            </div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill bg-periwinkle-mist/40 border border-ash text-xs font-mono text-off-black">
              <span>23 Synthetic Scenarios Evaluated</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="bg-parchment/70 border-b border-ash text-[11px] uppercase tracking-wider text-smoke font-semibold">
                  <th className="py-3 px-4">Evaluation Phase</th>
                  <th className="py-3 px-4">Investigation Engine</th>
                  <th className="py-3 px-4">Decision Accuracy</th>
                  <th className="py-3 px-4">False Closure Rate</th>
                  <th className="py-3 px-4">False Escalation</th>
                  <th className="py-3 px-4">Audit Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ash/40">
                {benchmarkData.benchmarks.benchmarks_comparison.map((b, idx) => {
                  const isPrimary = b.name.includes("Phase 7 Controlled");
                  return (
                    <tr
                      key={idx}
                      className={isPrimary ? "bg-emerald-50/40 font-medium" : "hover:bg-parchment/30"}
                    >
                      <td className="py-3.5 px-4 font-bold text-off-black">{b.name}</td>
                      <td className="py-3.5 px-4 text-graphite">{b.type}</td>
                      <td className="py-3.5 px-4 font-bold text-lake-blue">{b.accuracy}</td>
                      <td className="py-3.5 px-4 font-bold text-emerald-700">{b.false_closure}</td>
                      <td className="py-3.5 px-4 text-graphite">{b.false_escalation}</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                            isPrimary
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                              : "bg-ash/30 text-graphite"
                          }`}
                        >
                          {b.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* =========================================================================
            FAQ ACCORDION (Hairline bottom borders, Serif questions, mono text)
            ========================================================================= */}
        <section className="space-y-6">
          <div className="border-b border-ash pb-4">
            <span className="text-xs uppercase tracking-wider font-mono text-lake-blue font-medium block mb-1">
              Questions & Answers
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="divide-y divide-ash">
            {faqs.map((faq, idx) => {
              const isOpen = openFaq === idx;
              return (
                <div key={idx} className="py-6 transition-all">
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : idx)}
                    className="w-full text-left flex items-center justify-between gap-4 group"
                  >
                    <h3 className="font-serif text-xl sm:text-2xl text-off-black group-hover:text-lake-blue transition-colors">
                      {faq.q}
                    </h3>
                    <ChevronDown
                      className={`w-5 h-5 text-smoke shrink-0 transition-transform ${
                        isOpen ? "rotate-180 text-off-black" : ""
                      }`}
                    />
                  </button>
                  {isOpen && (
                    <div className="mt-4 text-xs sm:text-sm font-mono text-graphite leading-relaxed max-w-3xl">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* =========================================================================
            BOTTOM CALL-TO-ACTION
            ========================================================================= */}
        <section className="bg-off-black text-parchment rounded-card p-10 sm:p-16 text-center space-y-6 relative overflow-hidden">
          <div className="atmospheric-wash wash-sky-mint w-96 h-96 -top-20 -left-20 opacity-20" />
          <div className="relative z-10 max-w-2xl mx-auto space-y-4">
            <h2 className="font-serif text-4xl sm:text-5xl text-parchment font-normal">
              Ready to Audit Multi-Gateway Settlements?
            </h2>
            <p className="text-xs sm:text-sm font-mono text-ash leading-relaxed">
              Upload your transaction documents or start with our 23 pre-configured benchmark scenarios for full interactive proof inspection.
            </p>
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/connect"
                className="w-full sm:w-auto px-8 py-3.5 text-xs uppercase tracking-wider font-mono text-off-black bg-parchment hover:bg-white rounded-btn transition-all font-semibold"
              >
                Connect Documents or Start Simulation <span>▸</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

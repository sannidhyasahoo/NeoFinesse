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
  Zap,
} from "lucide-react";
import { benchmarkData } from "@/data/benchmarkData";

export default function LandingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const faqs = [
    {
      q: "How can you guarantee no incorrect closures?",
      a: "The AI's job is only to suggest possible explanations — it has no power to close a case on its own. Every suggested explanation must pass five independent mathematical checks: exact amount arithmetic, timing window compliance, a verified link between the transaction and the settlement, a valid transaction state, and a cryptographic record hash. If any check fails, the case stays open.",
    },
    {
      q: "What does 'source-level traceability' mean in practice?",
      a: "Every deduction, refund, fee, or payment that the system identifies is pinned to its exact location in the original uploaded file — the specific sheet name, row number, and cell. This means an auditor can open the raw file and verify each finding directly, with no black-box reasoning.",
    },
    {
      q: "How does the system handle two refunds with the same amount?",
      a: "In real reconciliation, hundreds of refunds can share the same value. Matching by amount alone would produce wrong results. Instead, the system traces the full chain from refund → payment → settlement batch, rejecting any refund that cannot be linked through that chain. Only the refund with a verified connection to the settlement is accepted.",
    },
    {
      q: "Can I use my own transaction files, or is it only a demo?",
      a: "Both. In the workspace you can upload your own multi-gateway CSV or Excel files — settlement batches, refund ledgers, bank statements, UPI logs — and the system will investigate them. Alternatively you can load the pre-built set of 23 demonstration cases to explore the system instantly.",
    },
  ];

  return (
    <div className="min-h-screen bg-parchment text-off-black flex flex-col selection:bg-periwinkle-mist relative overflow-hidden">
      {/* Top Notification */}
      <AnnouncementBar />

      {/* Navigation */}
      <Navbar />

      <main className="flex-1 max-w-[1432px] mx-auto px-6 lg:px-12 py-12 space-y-24 w-full relative z-10">

        {/* =========================================================================
            HERO — Plain language, what it is and what it does
            ========================================================================= */}
        <section className="text-center max-w-4xl mx-auto pt-8 sm:pt-16 pb-6 relative">
          {/* Atmospheric background */}
          <div className="atmospheric-wash wash-coral-sky w-[500px] h-[500px] -top-32 left-1/2 -translate-x-1/2 opacity-35" />

          <div className="relative z-10 space-y-6">
            {/* Eyebrow tag */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-pill bg-white/80 border border-ash text-xs font-mono text-off-black shadow-sm">
              <span className="w-2 h-2 rounded-full bg-lake-blue" />
              <span>Automated Settlement Reconciliation — Every Decision Mathematically Proven</span>
            </div>

            {/* Headline */}
            <h1 className="font-serif text-5xl sm:text-7xl lg:text-8xl text-off-black leading-[1.08] tracking-tight">
              Find why your settlement amount is wrong.
            </h1>

            {/* Subtext */}
            <p className="text-base sm:text-lg lg:text-xl font-mono text-graphite max-w-2xl mx-auto leading-relaxed">
              Upload your payment gateway exports. The system automatically investigates every discrepancy, traces it back to the exact source transaction, and either resolves it with proof or flags it for human review.
            </p>

            {/* Action Buttons */}
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/connect"
                className="w-full sm:w-auto px-8 py-3.5 text-xs uppercase tracking-wider font-mono text-white bg-lake-blue rounded-btn hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-sm font-medium"
              >
                Upload & Investigate <span>▸</span>
              </Link>
              <Link
                href="/workspace"
                className="w-full sm:w-auto px-8 py-3.5 text-xs uppercase tracking-wider font-mono text-off-black bg-transparent hover:bg-off-black hover:text-white border border-off-black rounded-btn transition-all flex items-center justify-center"
              >
                Explore 23 Demo Cases
              </Link>
            </div>

            {/* Trust badges */}
            <div className="pt-6 flex items-center justify-center gap-6 text-xs font-mono text-smoke flex-wrap">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" /> Zero incorrect closures
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-lake-blue" /> Traced to exact file cell
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-600" /> 5 independent checks per decision
              </span>
            </div>
          </div>
        </section>

        {/* =========================================================================
            SUPPORTED GATEWAYS STRIP
            ========================================================================= */}
        <section className="border-y border-ash/50 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="text-xs uppercase font-mono text-smoke tracking-wider">
              Works with data from:
            </div>
            <div className="flex flex-wrap items-center justify-center gap-8 text-sm font-mono font-medium text-graphite">
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">Razorpay</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">ICICI Bank</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">HDFC Bank</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">NPCI UPI</span>
              <span className="px-3 py-1 bg-white/60 rounded-lg border border-ash/40">Cashfree & Stripe</span>
            </div>
          </div>
        </section>

        {/* =========================================================================
            ELEVATED FEATURE CARD — The core separation explained simply
            ========================================================================= */}
        <section id="methodology">
          <div className="bg-periwinkle-mist/70 rounded-card border border-ash p-8 sm:p-14 relative overflow-hidden flex flex-col lg:flex-row items-center justify-between gap-12">
            <div className="atmospheric-wash wash-coral-sky w-[450px] h-[450px] -right-20 -bottom-20 opacity-50" />

            <div className="space-y-6 max-w-xl relative z-10">
              <span className="text-xs uppercase font-mono tracking-wider text-lake-blue font-semibold">
                Why This Approach Is Different
              </span>
              <h2 className="font-serif text-3xl sm:text-5xl text-off-black leading-tight">
                The AI suggests. The math decides.
              </h2>
              <p className="text-sm sm:text-base font-mono text-graphite leading-relaxed">
                Most automated tools let AI make the final call. That's risky in finance — a wrong closure means real money written off incorrectly. Here, the AI can only propose an explanation. A separate mathematical verifier checks five hard constraints before anything is marked resolved. If any constraint fails, the case is escalated — never silently closed.
              </p>
              <div className="pt-2">
                <Link
                  href="/workspace?tab=comparator"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-off-black text-white hover:bg-lake-blue rounded-btn text-xs font-mono uppercase tracking-wider transition-colors"
                >
                  See How They're Separated <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Live Constraint Engine Card */}
            <div className="w-full lg:w-[440px] bg-white rounded-3xl border border-ash/80 p-6 space-y-4 shadow-sm relative z-10 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-ash/50 pb-3">
                <span className="font-bold text-off-black uppercase">Verification Checks</span>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                  ALL 5 PASSED
                </span>
              </div>

              <div className="space-y-2">
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">1. Amount adds up exactly</span>
                  <strong className="text-emerald-700">₹100.00 == ₹100.00</strong>
                </div>
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">2. Happened within the time window</span>
                  <strong className="text-emerald-700">Within cut-off</strong>
                </div>
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">3. Linked to the right settlement</span>
                  <strong className="text-emerald-700">setl_9984 → pay_9984</strong>
                </div>
                <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 flex items-center justify-between">
                  <span className="text-graphite">4. Found in the source file</span>
                  <strong className="text-lake-blue">Row 10, Cell F10</strong>
                </div>
              </div>

              <div className="pt-2 border-t border-ash/50 flex items-center justify-between text-[11px] text-smoke">
                <span>Cryptographic record hash:</span>
                <span className="font-bold text-off-black">e3b0c44298fc...</span>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================================================
            PIPELINE DIAGRAM — "The Process" section
            ========================================================================= */}
        <section id="architecture">
          <PipelineDiagram />
        </section>

        {/* =========================================================================
            4 CAPABILITY CARDS
            ========================================================================= */}
        <section id="invariants" className="space-y-8">
          <div>
            <span className="text-xs uppercase tracking-wider font-mono text-lake-blue font-medium block mb-1">
              What It Does
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
              Built for the hard cases in financial reconciliation
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-blue-50 border border-lake-blue/20 text-lake-blue flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                Every finding traces back to the source file
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                Each deduction, refund, and fee variance is pinned to the exact sheet, row, and cell in the original uploaded file. Auditors can verify findings directly without trusting a summary.
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                Won't be fooled by matching amounts
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                Hundreds of refunds often share the exact same amount. Matching by value alone produces wrong results. The system traces the full chain from refund to payment to settlement, rejecting anything that isn't verifiably connected.
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                Handles variances caused by multiple events
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                A single settlement gap can be caused by a refund plus a fee adjustment together. The system identifies both, verifies each one independently, and only resolves the case when their combined total matches the exact discrepancy.
              </p>
            </div>

            {/* Card 4 */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-4 hover:border-off-black transition-all">
              <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-700 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-serif text-2xl text-off-black">
                Escalates what it can't prove
              </h3>
              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                When the system cannot fully verify an explanation — because a transaction falls outside the time window, the amounts don't add up, or the link is missing — it escalates to a human auditor with a complete evidence package, rather than guessing.
              </p>
            </div>
          </div>
        </section>

        {/* =========================================================================
            ACCURACY RESULTS TABLE
            ========================================================================= */}
        <section id="benchmark" className="bg-white rounded-card border border-ash p-8 sm:p-12 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-ash/50 pb-6">
            <div>
              <span className="text-xs uppercase tracking-wider font-mono text-lake-blue font-medium block mb-1">
                Verified Results
              </span>
              <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
                Tested on 23 real-world settlement mismatch scenarios
              </h2>
              <p className="text-sm font-mono text-graphite mt-2 leading-relaxed">
                The table below compares three versions of the system tested in sequence — from a basic rule engine to the full AI + verification pipeline.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill bg-periwinkle-mist/40 border border-ash text-xs font-mono text-off-black shrink-0">
              <span>23 scenarios evaluated</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="bg-parchment/70 border-b border-ash text-[11px] uppercase tracking-wider text-smoke font-semibold">
                  <th className="py-3 px-4">System Tested</th>
                  <th className="py-3 px-4">Approach</th>
                  <th className="py-3 px-4">Correct Decisions</th>
                  <th className="py-3 px-4">Wrong Closures</th>
                  <th className="py-3 px-4">Needless Escalations</th>
                  <th className="py-3 px-4">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ash/40">
                {[
                  {
                    name: "Rule-Based Baseline",
                    type: "Manual rules only, no AI",
                    accuracy: "73.9% (17/23)",
                    false_closure: "0.0% (0/12)",
                    false_escalation: "50.0% (6/12)",
                    status: "Baseline — superseded",
                    isPrimary: false,
                  },
                  {
                    name: "AI + Verification (this system)",
                    type: "AI investigation + mathematical verification",
                    accuracy: "100.0% (23/23)",
                    false_closure: "0.0% (0/12)",
                    false_escalation: "0.0% (0/12)",
                    status: "Current — verified",
                    isPrimary: true,
                  },
                  {
                    name: "Remote AI Only (no local verifier)",
                    type: "External AI model, no deterministic check",
                    accuracy: "65.2% (15/23)*",
                    false_closure: "0.0% (0/12)",
                    false_escalation: "66.7% (8/12)",
                    status: "Quota-limited audit (*8 infra failures)",
                    isPrimary: false,
                  },
                ].map((b, idx) => (
                  <tr
                    key={idx}
                    className={b.isPrimary ? "bg-emerald-50/40 font-medium" : "hover:bg-parchment/30"}
                  >
                    <td className="py-3.5 px-4 font-bold text-off-black">{b.name}</td>
                    <td className="py-3.5 px-4 text-graphite">{b.type}</td>
                    <td className="py-3.5 px-4 font-bold text-lake-blue">{b.accuracy}</td>
                    <td className="py-3.5 px-4 font-bold text-emerald-700">{b.false_closure}</td>
                    <td className="py-3.5 px-4 text-graphite">{b.false_escalation}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${b.isPrimary
                            ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                            : "bg-ash/30 text-graphite"
                          }`}
                      >
                        {b.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* =========================================================================
            FAQ ACCORDION
            ========================================================================= */}
        <section className="space-y-6">
          <div className="border-b border-ash pb-4">
            <span className="text-xs uppercase tracking-wider font-mono text-lake-blue font-medium block mb-1">
              Questions
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
              How does it work?
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
                      className={`w-5 h-5 text-smoke shrink-0 transition-transform ${isOpen ? "rotate-180 text-off-black" : ""
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
              Ready to audit your settlement files?
            </h2>
            <p className="text-xs sm:text-sm font-mono text-ash leading-relaxed">
              Upload your own gateway exports and get a verified explanation for every discrepancy, or load 23 pre-built demo cases to see the system in action right now.
            </p>
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/connect"
                className="w-full sm:w-auto px-8 py-3.5 text-xs uppercase tracking-wider font-mono text-off-black bg-parchment hover:bg-white rounded-btn transition-all font-semibold"
              >
                Upload Files or Start Demo <span>▸</span>
              </Link>
            </div>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}

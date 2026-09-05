"use client";

import React, { useState } from "react";
import { Database, Search, Cpu, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";

interface PipelineStep {
  id: string;
  stepNumber: string;
  title: string;
  subtitle: string;
  description: string;
  badge: string;
  icon: React.ReactNode;
  authority: "AI & Tools" | "Deterministic Verifier" | "Settlement Ledger";
}

const steps: PipelineStep[] = [
  {
    id: "step-1",
    stepNumber: "Step 01",
    title: "Multi-Gateway Ingestion",
    subtitle: "Expected vs Actual",
    description: "Ingests Razorpay, Cashfree, ICICI bank statements, and UPI switch payloads. Matches batch totals and registers initial delta.",
    badge: "Input Stream",
    icon: <Database className="w-4 h-4 text-graphite" />,
    authority: "Settlement Ledger",
  },
  {
    id: "step-2",
    stepNumber: "Step 02",
    title: "Variance Delta Isolation",
    subtitle: "Paise-level discrepancy",
    description: "Computes exact arithmetic difference (₹) per settlement batch and initializes an evidence-constrained investigation session.",
    badge: "Delta Trigger",
    icon: <Search className="w-4 h-4 text-crimson" />,
    authority: "Settlement Ledger",
  },
  {
    id: "step-3",
    stepNumber: "Step 03",
    title: "AI Hypothesis Generator",
    subtitle: "Candidate generation",
    description: "LLM analyzes domain rules, historical context, and proposes testable causal hypotheses without closing authority.",
    badge: "Planner (No Closing Power)",
    icon: <Cpu className="w-4 h-4 text-lake-blue" />,
    authority: "AI & Tools",
  },
  {
    id: "step-4",
    stepNumber: "Step 04",
    title: "Bounded Tool Retrieval",
    subtitle: "L5 cell coordinates",
    description: "Autonomous tool execution queries refunds, adjustments, disputes, and delayed credits, retrieving SHA-256 backed cell coordinates.",
    badge: "Evidence Collector",
    icon: <Database className="w-4 h-4 text-lake-blue" />,
    authority: "AI & Tools",
  },
  {
    id: "step-5",
    stepNumber: "Step 05",
    title: "5-Point Deterministic Verifier",
    subtitle: "Sole final authority",
    description: "Evaluates exact mathematical sum, temporal window cut-off, relational key provenance, state legality, and completeness.",
    badge: "Sole Authority",
    icon: <ShieldCheck className="w-4 h-4 text-emerald-600" />,
    authority: "Deterministic Verifier",
  },
  {
    id: "step-6",
    stepNumber: "Step 06",
    title: "Terminal Decision & Fail-Safe",
    subtitle: "RESOLVED / ESCALATE",
    description: "Either generates automated cryptographic ledger resolution or safely escalates trapped decoys to Tier-2 human audit queue.",
    badge: "Zero False Closures",
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
    authority: "Deterministic Verifier",
  },
];

export default function PipelineDiagram() {
  const [activeStep, setActiveStep] = useState<string>("step-5");
  const current = steps.find((s) => s.id === activeStep) || steps[4];

  return (
    <div className="w-full bg-parchment rounded-card border border-ash p-8 sm:p-12 relative overflow-hidden">
      {/* Background atmospheric gradient wash */}
      <div className="atmospheric-wash wash-sky-mint w-96 h-96 -top-20 -right-20" />
      <div className="atmospheric-wash wash-coral-sky w-80 h-80 -bottom-20 -left-20" />

      <div className="relative z-10 space-y-8">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-ash/50 pb-6">
          <div>
            <span className="text-xs uppercase tracking-wider font-mono text-lake-blue font-medium block mb-1">
              Deterministic Architecture
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
              End-to-End Investigation Architecture Flow
            </h2>
          </div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill bg-emerald-50 border border-emerald-300 text-xs font-mono text-emerald-800 self-start sm:self-auto">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Deterministic Safety Guaranteed</span>
          </div>
        </div>

        {/* Interactive Pipeline Node Strip */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
          {steps.map((step, idx) => {
            const isSelected = step.id === activeStep;
            const isVerifier = step.authority === "Deterministic Verifier";
            const isAI = step.authority === "AI & Tools";

            return (
              <button
                key={step.id}
                onClick={() => setActiveStep(step.id)}
                className={`text-left p-4 rounded-2xl border transition-all relative flex flex-col justify-between min-h-[140px] ${
                  isSelected
                    ? "bg-white border-off-black ring-2 ring-off-black/10 shadow-sm"
                    : "bg-parchment/60 hover:bg-white/80 border-ash"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-2">
                    <span className="text-[10px] font-mono text-smoke uppercase tracking-wider">
                      {step.stepNumber}
                    </span>
                    <div className="p-1 rounded-full bg-ash/20">{step.icon}</div>
                  </div>
                  <div className="font-mono font-medium text-xs text-off-black line-clamp-2 leading-tight">
                    {step.title}
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-ash/40">
                  <span
                    className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full inline-block ${
                      isVerifier
                        ? "bg-emerald-100 text-emerald-800 font-semibold"
                        : isAI
                        ? "bg-blue-100 text-lake-blue font-medium"
                        : "bg-ash/30 text-graphite"
                    }`}
                  >
                    {step.subtitle}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Deep Dive Detail Card for Selected Step */}
        <div className="p-6 sm:p-8 bg-white/90 rounded-3xl border border-ash/70 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 backdrop-blur-sm">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-smoke uppercase tracking-wider">
                {current.stepNumber} Focus
              </span>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-pill bg-periwinkle-mist/60 border border-ash text-off-black">
                Authority: {current.authority}
              </span>
            </div>
            <h3 className="font-serif text-2xl text-off-black">{current.title}</h3>
            <p className="text-sm font-mono text-graphite leading-relaxed">
              {current.description}
            </p>
          </div>

          <div className="shrink-0 flex flex-col sm:flex-row md:flex-col gap-2 w-full md:w-auto">
            <div className="px-4 py-2 bg-parchment rounded-xl border border-ash text-center">
              <div className="text-[10px] uppercase font-mono text-smoke">Invariable Constraint</div>
              <div className="text-xs font-mono text-off-black font-semibold mt-0.5">
                {current.badge}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

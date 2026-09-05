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
    title: "Files are imported",
    subtitle: "Expected vs received",
    description: "Your settlement files from Razorpay, Cashfree, ICICI, HDFC, or UPI are loaded. The system reads the expected payout and what was actually credited to the bank.",
    badge: "Data Import",
    icon: <Database className="w-4 h-4 text-graphite" />,
    authority: "Settlement Ledger",
  },
  {
    id: "step-2",
    stepNumber: "Step 02",
    title: "Discrepancies are found",
    subtitle: "Amount mismatch detected",
    description: "For each settlement batch, the system calculates the exact difference between what was expected and what arrived. Each gap gets its own investigation.",
    badge: "Mismatch Detected",
    icon: <Search className="w-4 h-4 text-crimson" />,
    authority: "Settlement Ledger",
  },
  {
    id: "step-3",
    stepNumber: "Step 03",
    title: "AI proposes an explanation",
    subtitle: "Hypothesis, not decision",
    description: "The AI looks at the data and suggests what might explain the gap — a refund, a fee, a dispute. It cannot close the case itself; it can only propose.",
    badge: "Suggestion Only",
    icon: <Cpu className="w-4 h-4 text-lake-blue" />,
    authority: "AI & Tools",
  },
  {
    id: "step-4",
    stepNumber: "Step 04",
    title: "Evidence is collected",
    subtitle: "Traced to source file",
    description: "The system retrieves the actual transactions — refunds, adjustments, disputes — and records where each one lives in the original uploaded file.",
    badge: "Evidence Collected",
    icon: <Database className="w-4 h-4 text-lake-blue" />,
    authority: "AI & Tools",
  },
  {
    id: "step-5",
    stepNumber: "Step 05",
    title: "Five checks are run",
    subtitle: "Math, time, link, state, file",
    description: "Each piece of evidence must pass: (1) amounts add up, (2) timing is within the window, (3) the transaction links to this settlement, (4) the state is valid, (5) the record exists in the source file.",
    badge: "All 5 Must Pass",
    icon: <ShieldCheck className="w-4 h-4 text-emerald-600" />,
    authority: "Deterministic Verifier",
  },
  {
    id: "step-6",
    stepNumber: "Step 06",
    title: "Resolved or escalated",
    subtitle: "Proven close or human review",
    description: "If all five checks pass, the case is closed with a full verified audit trail. If any check fails, the case is sent to a human reviewer with the complete evidence package.",
    badge: "No Incorrect Closures",
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
              How It Works
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl text-off-black">
              From uploaded file to verified decision — six steps
            </h2>
          </div>
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill bg-emerald-50 border border-emerald-300 text-xs font-mono text-emerald-800 self-start sm:self-auto">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>No incorrect closures, guaranteed</span>
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
                className={`text-left p-4 rounded-2xl border transition-all relative flex flex-col justify-between min-h-[140px] ${isSelected
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
                    className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full inline-block ${isVerifier
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

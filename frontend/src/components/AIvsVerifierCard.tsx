"use client";

import React from "react";
import { Scenario } from "@/types";
import { Bot, Zap, Shield, CheckCircle2, XCircle, ArrowRight } from "lucide-react";

interface AIvsVerifierCardProps {
  scenario: Scenario;
}

export default function AIvsVerifierCard({ scenario }: AIvsVerifierCardProps) {
  const isApproved = scenario.expected_outcome !== "ESCALATE";

  return (
    <div className="space-y-6">
      {/* Principle Banner */}
      <div className="p-4 bg-periwinkle-mist/30 rounded-2xl border border-ash flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-lake-blue" />
          <span className="text-xs font-mono text-off-black">
            <strong>Architectural Boundary:</strong> The LLM is strictly an investigator & hypothesis generator with <strong>zero closing authority</strong>.
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded-pill bg-white border border-ash text-graphite uppercase">
          Zero Hallucination Guaranteed
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-11 gap-4 items-stretch">
        {/* Left Col: AI Investigator (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-ash p-6 space-y-4 flex flex-col justify-between shadow-sm">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-ash/40 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-blue-50 border border-lake-blue/30 text-lake-blue flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-serif text-lg text-off-black">AI Investigator (Planner)</h3>
                  <div className="text-[10px] font-mono text-smoke">Proposes hypotheses & bounds tool searches</div>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-blue-50 text-lake-blue text-[10px] font-mono font-medium">
                Advisory Only
              </span>
            </div>

            {/* Generated Hypothesis */}
            <div>
              <div className="text-[10px] uppercase font-mono text-smoke tracking-wider mb-1">
                Generated Causal Hypothesis
              </div>
              <div className="p-3 bg-parchment rounded-2xl border border-ash/60 text-xs font-mono text-off-black leading-relaxed">
                &ldquo;{scenario.ai_hypothesis?.proposed_explanation || "Analyzing variance candidate causes against settlement window..."}&rdquo;
              </div>
            </div>

            {/* Requested Tools */}
            <div>
              <div className="text-[10px] uppercase font-mono text-smoke tracking-wider mb-1">
                Requested Bounded Tool Queries
              </div>
              <ul className="space-y-1 text-xs font-mono">
                {(scenario.ai_hypothesis?.requested_tools || [
                  `retrieve_entities_by_settlement('${scenario.settlement_id}')`,
                  "query_temporal_window(start='-48h', end='cut_off')",
                ]).map((tool, idx) => (
                  <li
                    key={idx}
                    className="p-2 bg-ash/10 rounded-xl text-lake-blue text-[11px] font-mono flex items-center gap-1.5"
                  >
                    <code>{tool}</code>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="pt-3 border-t border-ash/40 text-[10px] font-mono text-smoke">
            Closing Authority: <strong className="text-rose-600">NONE (Read-Only)</strong>
          </div>
        </div>

        {/* Center Barrier (1 col) */}
        <div className="lg:col-span-1 flex lg:flex-col items-center justify-center gap-2 py-2">
          <div className="h-px lg:h-full w-full lg:w-px bg-ash" />
          <div
            className="w-10 h-10 rounded-full bg-off-black text-parchment flex items-center justify-center shadow-md shrink-0"
            title="Deterministic Safety Boundary"
          >
            <Shield className="w-4 h-4 text-mint" />
          </div>
          <div className="h-px lg:h-full w-full lg:w-px bg-ash" />
        </div>

        {/* Right Col: Deterministic Verifier (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-ash p-6 space-y-4 flex flex-col justify-between shadow-sm">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-ash/40 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-emerald-50 border border-emerald-300 text-emerald-700 flex items-center justify-center">
                  <Zap className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-serif text-lg text-off-black">Deterministic Verifier</h3>
                  <div className="text-[10px] font-mono text-smoke">Strict mathematical & relational constraints</div>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-mono font-bold">
                Sole Authority
              </span>
            </div>

            {/* 5-Point Checklist */}
            <div>
              <div className="text-[10px] uppercase font-mono text-smoke tracking-wider mb-2">
                5-Point Deterministic Constraint Proof
              </div>
              <div className="space-y-2">
                {(scenario.verifier_constraints || []).map((c, idx) => {
                  const isPass = c.status === "PASS";
                  return (
                    <div
                      key={idx}
                      className={`p-2.5 rounded-2xl border text-xs font-mono transition-all flex items-start justify-between gap-3 ${
                        isPass
                          ? "bg-emerald-50/40 border-emerald-200 text-emerald-900"
                          : "bg-rose-50/40 border-rose-200 text-rose-900"
                      }`}
                    >
                      <div className="space-y-0.5">
                        <div className="font-bold text-[11px] flex items-center gap-1.5">
                          {isPass ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                          )}
                          <span>{c.constraint_name}</span>
                        </div>
                        <div className="text-[10px] opacity-80 pl-5">{c.details}</div>
                      </div>
                      <span
                        className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-bold ${
                          isPass ? "bg-emerald-200 text-emerald-900" : "bg-rose-200 text-rose-900"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-ash/40 flex items-center justify-between text-xs font-mono">
            <span className="text-smoke uppercase text-[10px] font-semibold">Verifier Verdict:</span>
            <span
              className={`px-3 py-1 rounded-pill font-bold uppercase text-[11px] ${
                isApproved
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  : "bg-rose-100 text-rose-800 border border-rose-300"
              }`}
            >
              {isApproved ? "✓ APPROVED (Auto-Close)" : "🚨 ESCALATE (Human Audit)"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

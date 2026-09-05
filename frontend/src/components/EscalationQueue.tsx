"use client";

import React from "react";
import { Scenario } from "@/types";
import { AlertOctagon, ShieldAlert, CheckCircle, ArrowRight, UserCheck } from "lucide-react";

interface EscalationQueueProps {
  scenario: Scenario;
}

export default function EscalationQueue({ scenario }: EscalationQueueProps) {
  const isEscalated = scenario.expected_outcome === "ESCALATE";
  const varFormatted =
    scenario.variance_inr < 0
      ? `-₹${Math.abs(scenario.variance_inr).toFixed(2)}`
      : `+₹${scenario.variance_inr.toFixed(2)}`;

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="bg-white rounded-3xl border border-ash p-6 sm:p-8 space-y-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-ash/50 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-serif text-2xl text-off-black">
                Cases Sent to Human Review &bull; <span className="text-lake-blue">{scenario.case_id}</span>
              </h3>
              <p className="text-xs font-mono text-smoke mt-0.5">
                When the system can&rsquo;t fully prove an explanation, it sends the case here rather than guessing. This view shows exactly why.
              </p>
            </div>
          </div>

          <div className="px-4 py-2 bg-parchment rounded-2xl border border-ash text-right self-start sm:self-auto">
            <div className="text-[10px] uppercase font-mono text-smoke">Unresolved Amount</div>
            <div className="text-lg font-mono font-bold text-rose-600">{varFormatted}</div>
          </div>
        </div>

        {/* Forensic Audit Details */}
        <div className="space-y-4">
          <div className="text-xs uppercase font-mono font-bold text-off-black tracking-wider flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            <span>Why was this case not closed automatically?</span>
          </div>

          <div className="p-4 bg-parchment rounded-2xl border border-ash/70 space-y-3">
            <p className="text-xs font-mono text-off-black leading-relaxed">
              {scenario.primary_cause || "No valid explanation satisfies all five verification checks."}
            </p>

            <div className="space-y-2 pt-2 border-t border-ash/40">
              <div className="text-[10px] uppercase font-mono text-smoke font-medium">
                Checks that failed:
              </div>
              {(scenario.verifier_constraints || [])
                .filter((c) => c.status === "FAIL")
                .map((c, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-rose-50/70 rounded-xl border border-rose-200 text-xs font-mono text-rose-900 flex items-start gap-2"
                  >
                    <span className="w-2 h-2 rounded-full bg-rose-500 mt-1.5 shrink-0" />
                    <div>
                      <strong>{c.constraint_name}:</strong> {c.details}
                    </div>
                  </div>
                ))}
              {(scenario.verifier_constraints || []).filter((c) => c.status === "FAIL").length === 0 && (
                <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs font-mono text-emerald-900">
                  All constraints passed. Case is resolved without escalation.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recommended System Action */}
        <div className="p-4 bg-periwinkle-mist/40 rounded-2xl border border-ash flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-[10px] uppercase font-mono text-smoke font-medium">
              Next Action
            </div>
            <div className="text-xs font-mono font-semibold text-off-black">
              Assign to a human auditor. Full source file evidence is attached to the case.
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="px-4 py-2 bg-off-black text-parchment hover:bg-lake-blue rounded-btn text-xs font-mono uppercase tracking-wider transition-colors flex items-center gap-1.5 shadow-sm">
              <UserCheck className="w-3.5 h-3.5" /> Assign Auditor
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

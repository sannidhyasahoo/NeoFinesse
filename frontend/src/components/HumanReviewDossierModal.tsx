"use client";

import React, { useState, useEffect } from "react";
import {
  AlertOctagon,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  FileSpreadsheet,
  Clock,
  ArrowRight,
  Copy,
  Check,
  X,
  ExternalLink,
  HelpCircle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  UserCheck,
  FileText,
} from "lucide-react";
import { Scenario, EvidenceNode } from "@/types";

interface HumanReviewDossierModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenario: Scenario | null;
  onViewSource: (evidence: EvidenceNode) => void;
}

export default function HumanReviewDossierModal({
  isOpen,
  onClose,
  scenario,
  onViewSource,
}: HumanReviewDossierModalProps) {
  const [handoff, setHandoff] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showTimeline, setShowTimeline] = useState(true);
  const [copiedReport, setCopiedReport] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Fetch summary handoff data whenever modal opens
  useEffect(() => {
    if (!isOpen || !scenario) {
      setHandoff(null);
      return;
    }

    let isMounted = true;
    setIsLoading(true);

    fetch(`/api/escalation/summary?scenario_id=${encodeURIComponent(scenario.scenario_id)}`)
      .then((res) => res.json())
      .then((data) => {
        if (isMounted) {
          if (data.status === "SUCCESS") {
            setHandoff(data.handoff);
          }
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load escalation handoff summary:", err);
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, scenario]);

  if (!isOpen || !scenario) return null;

  const varFormatted =
    scenario.variance_inr < 0
      ? `-₹${Math.abs(scenario.variance_inr).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
      : `+₹${scenario.variance_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;

  const handleCopyDossierReport = () => {
    if (!handoff) return;

    const mdReport = `# NEOFINESSE HUMAN REVIEW DOSSIER
**Case:** ${handoff.case_id} (${handoff.scenario_id})
**Settlement ID:** ${handoff.settlement_id}
**Severity:** ${handoff.severity}
**Variance:** ${varFormatted} (Expected: ₹${handoff.expected_amount_inr?.toLocaleString("en-IN")}, Bank Credit: ₹${handoff.actual_bank_credit_inr?.toLocaleString("en-IN")})

---

### 1. WHY ESCALATED
${handoff.why_escalated}

### 2. WHY IT COULD NOT CLOSE
${handoff.why_could_not_close}

### 3. WHAT NEOFINESSE TRIED
${handoff.verifications_attempted?.map((v: any) => `- [${v.passed ? "x" : " "}] ${v.check_name}: ${v.description}`).join("\n")}

### 4. EVIDENCE REVIEWED
${handoff.evidence_reviewed?.map((e: any) => `- ${e.evidence_id} (${e.entity_type}): ₹${e.amount_inr} [${e.source_file} > ${e.sheet}!${e.cell}]`).join("\n") || "None confirmed"}

### 5. REJECTED EVIDENCE / DECOYS
${handoff.rejected_evidence?.map((d: any) => `- ${d.evidence_id} (${d.entity_type}): ₹${d.amount_inr} - REJECTED: ${d.rejection_reason}`).join("\n") || "None"}

### 6. RECOMMENDED HUMAN NEXT ACTION
${handoff.recommended_human_action}

---
*Generated deterministically by NeoFinesse Verification Engine — 0% False Closure Guarantee.*`;

    navigator.clipboard.writeText(mdReport);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-off-black/65 backdrop-blur-md animate-fade-in">
      {/* Backdrop */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Modal Container */}
      <div className="relative w-full max-w-5xl bg-parchment rounded-3xl border border-ash shadow-2xl overflow-hidden flex flex-col max-h-[92vh] z-10 animate-slide-up">
        {/* =========================================================================
            HEADER — Case ID, Severity Badge, Copy Dossier & Close
            ========================================================================= */}
        <div className="p-6 bg-white border-b border-ash flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-mono text-smoke">
              <span className="px-2.5 py-0.5 rounded-pill bg-rose-100 text-rose-800 border border-rose-300 font-bold uppercase tracking-wider flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
                Human Review Handoff
              </span>
              <span>&bull;</span>
              <span className="font-semibold text-off-black">{scenario.case_id}</span>
              <span>&bull;</span>
              <span className="text-graphite">{scenario.settlement_id}</span>
            </div>

            <h2 className="font-serif text-2xl sm:text-3xl text-off-black flex items-center gap-3">
              <span>Investigation Summary & Auditor Dossier</span>
            </h2>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={handleCopyDossierReport}
              className="px-4 py-2 rounded-pill bg-parchment hover:bg-ash/30 border border-ash text-xs font-mono text-off-black transition-all flex items-center gap-1.5 shadow-sm font-semibold"
              title="Copy formatted Markdown dossier for ticketing/audit"
            >
              {copiedReport ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-smoke" />}
              <span>{copiedReport ? "Dossier Copied!" : "Copy Full Report"}</span>
            </button>

            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-parchment hover:bg-ash/40 border border-ash text-off-black flex items-center justify-center transition-all"
              title="Close (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* =========================================================================
            KEY VARIANCE STRIP
            ========================================================================= */}
        <div className="px-6 py-4 bg-white/70 border-b border-ash/70 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div>
            <div className="text-[10px] uppercase text-smoke font-medium">Unresolved Variance</div>
            <div className="text-lg font-bold text-rose-600 font-mono mt-0.5">{varFormatted}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-smoke font-medium">Expected Settlement</div>
            <div className="text-sm font-bold text-off-black font-mono mt-0.5">
              ₹{scenario.expected_amount_inr?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-smoke font-medium">Actual Bank Credit</div>
            <div className="text-sm font-bold text-graphite font-mono mt-0.5">
              ₹{scenario.actual_bank_credit_inr?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-smoke font-medium">Review Priority</div>
            <div className="mt-0.5">
              <span className="px-2.5 py-0.5 rounded-pill bg-rose-50 text-rose-700 border border-rose-200 text-[11px] font-bold uppercase">
                {handoff?.severity || "HIGH"} Priority
              </span>
            </div>
          </div>
        </div>

        {/* =========================================================================
            SCROLLABLE DOSSIER BODY
            ========================================================================= */}
        <div className="flex-1 p-6 sm:p-8 overflow-y-auto space-y-8">
          {isLoading ? (
            <div className="h-64 flex flex-col items-center justify-center space-y-3 bg-white rounded-2xl border border-ash">
              <div className="w-6 h-6 border-2 border-rose-600 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-mono text-smoke">Compiling evidence-backed investigation handoff...</span>
            </div>
          ) : handoff ? (
            <>
              {/* SECTION 1: WHY ESCALATED & WHY COULD NOT CLOSE */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-5 bg-white rounded-2xl border border-rose-200 shadow-sm space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono uppercase font-bold text-rose-700">
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                    <span>1. Why This Case Was Escalated</span>
                  </div>
                  <p className="text-xs sm:text-sm font-mono text-off-black leading-relaxed">
                    {handoff.why_escalated}
                  </p>
                </div>

                <div className="p-5 bg-white rounded-2xl border border-ash shadow-sm space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono uppercase font-bold text-off-black">
                    <HelpCircle className="w-4 h-4 text-lake-blue" />
                    <span>2. Why It Could Not Close Automatically</span>
                  </div>
                  <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                    {handoff.why_could_not_close}
                  </p>
                </div>
              </div>

              {/* SECTION 2: SEPARATING "WHAT AI THOUGHT" FROM "WHAT WAS PROVEN" */}
              <div className="bg-white rounded-2xl border border-ash p-6 space-y-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-ash/50 pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-600" />
                    <h3 className="font-serif text-lg text-off-black">
                      AI Hypothesis vs. Deterministic Proof Barrier
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-smoke uppercase font-semibold">
                    Core Invariant: AI Never Closes Financial Ledgers
                  </span>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-11 gap-4 items-center">
                  {/* AI Thought Column (5 cols) */}
                  <div className="lg:col-span-5 p-4 rounded-xl bg-purple-50/60 border border-purple-200 space-y-2 text-xs font-mono">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-purple-900 uppercase text-[11px]">
                        AI Investigation Hypothesis
                      </span>
                      <span className="px-2 py-0.5 rounded bg-purple-200 text-purple-900 text-[10px] font-bold">
                        {handoff.ai_hypothesis_summary?.ai_confidence || "Hypothesis Only"}
                      </span>
                    </div>
                    <p className="text-purple-950 text-[12px] leading-relaxed">
                      &ldquo;{handoff.ai_hypothesis_summary?.hypothesis}&rdquo;
                    </p>
                    <div className="text-[10px] text-purple-800 pt-1 border-t border-purple-200/60">
                      <strong>Tools Called:</strong> {handoff.ai_hypothesis_summary?.tools_used?.join(", ")}
                    </div>
                  </div>

                  {/* Separation Barrier Arrow (1 col) */}
                  <div className="lg:col-span-1 flex flex-col items-center justify-center text-smoke py-2 lg:py-0">
                    <div className="hidden lg:block w-px h-12 bg-ash mb-1" />
                    <ArrowRight className="w-5 h-5 text-lake-blue rotate-90 lg:rotate-0" />
                    <div className="hidden lg:block w-px h-12 bg-ash mt-1" />
                  </div>

                  {/* Deterministic Verifier Column (5 cols) */}
                  <div className="lg:col-span-5 p-4 rounded-xl bg-rose-50/60 border border-rose-200 space-y-2 text-xs font-mono">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-rose-900 uppercase text-[11px]">
                        Deterministic Verifier Outcome
                      </span>
                      <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 text-[10px] font-bold">
                        {handoff.deterministic_verdict?.verdict || "REJECTED"}
                      </span>
                    </div>
                    <p className="text-rose-950 text-[12px] leading-relaxed">
                      {handoff.deterministic_verdict?.constraints_failed} of {handoff.deterministic_verdict?.constraints_evaluated} mathematical/temporal constraints failed. Terminal decision: <strong>ESCALATE</strong>.
                    </p>
                    <div className="text-[10px] text-rose-800 pt-1 border-t border-rose-200/60">
                      <strong>Authority:</strong> Mathematical Verifier holds 100% closing power.
                    </div>
                  </div>
                </div>
              </div>

              {/* SECTION 3: WHAT NEOFINESSE TRIED (Checklist) */}
              <div className="bg-white rounded-2xl border border-ash p-6 space-y-4 shadow-sm">
                <div className="flex items-center justify-between border-b border-ash/50 pb-3">
                  <h3 className="font-serif text-lg text-off-black">
                    What NeoFinesse Verified Before Escalating
                  </h3>
                  <span className="text-xs font-mono text-smoke">
                    {handoff.verifications_attempted?.filter((v: any) => v.passed).length} Passed &bull; {handoff.verifications_attempted?.filter((v: any) => !v.passed).length} Failed
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {handoff.verifications_attempted?.map((v: any, idx: number) => (
                    <div
                      key={idx}
                      className={`p-3.5 rounded-xl border flex items-start gap-3 text-xs font-mono ${
                        v.passed
                          ? "bg-emerald-50/40 border-emerald-200 text-emerald-950"
                          : "bg-rose-50/50 border-rose-200 text-rose-950"
                      }`}
                    >
                      {v.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                      ) : (
                        <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <div className="font-bold">{v.check_name}</div>
                        <div className="text-[11px] text-graphite mt-0.5">{v.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* SECTION 4: REJECTED EVIDENCE & DECOYS WITH [VIEW SOURCE] */}
              {handoff.rejected_evidence && handoff.rejected_evidence.length > 0 && (
                <div className="bg-white rounded-2xl border border-ash p-6 space-y-4 shadow-sm">
                  <div className="flex items-center justify-between border-b border-ash/50 pb-3">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-rose-600" />
                      <h3 className="font-serif text-lg text-off-black">
                        Rejected Decoy Candidates ({handoff.rejected_evidence.length})
                      </h3>
                    </div>
                    <span className="text-xs font-mono text-smoke">
                      Plausible &ne; Proven
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {handoff.rejected_evidence.map((decoy: EvidenceNode, idx: number) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-rose-50/40 border border-rose-200 text-xs font-mono space-y-2 flex flex-col justify-between"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-rose-900">
                              {decoy.evidence_id} &bull; {decoy.entity_type}
                            </span>
                            <span className="font-bold text-rose-700 text-sm">
                              ₹{Math.abs(decoy.amount_inr).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                          <div className="text-[11px] text-smoke">
                            📄 {decoy.source_file} &bull; {decoy.sheet}!{decoy.cell}
                          </div>
                          <p className="text-rose-950 font-sans text-xs pt-1">
                            <strong>Why Rejected:</strong> {decoy.rejection_reason || "Failed constraint checks."}
                          </p>
                          {decoy.lesson && (
                            <p className="text-[10px] text-rose-800 italic pt-0.5">
                              💡 {decoy.lesson}
                            </p>
                          )}
                        </div>

                        <button
                          onClick={() => onViewSource(decoy)}
                          className="self-start px-3 py-1.5 mt-2 bg-white hover:bg-off-black hover:text-white border border-rose-300 rounded-pill text-[11px] font-mono font-bold transition-all flex items-center gap-1.5 shadow-sm"
                        >
                          <FileSpreadsheet className="w-3.5 h-3.5 text-lake-blue" />
                          <span>View Source Cell ({decoy.cell}) &rarr;</span>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SECTION 5: MISSING EVIDENCE ITEMS */}
              {handoff.missing_evidence && handoff.missing_evidence.length > 0 && (
                <div className="bg-white rounded-2xl border border-ash p-6 space-y-4 shadow-sm">
                  <div className="flex items-center justify-between border-b border-ash/50 pb-3">
                    <h3 className="font-serif text-lg text-off-black">
                      Missing Evidence Identified
                    </h3>
                    <span className="text-xs font-mono text-smoke">
                      Gaps Detected in Audit Graph
                    </span>
                  </div>

                  <div className="space-y-3">
                    {handoff.missing_evidence.map((item: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3.5 bg-parchment rounded-xl border border-ash flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono"
                      >
                        <div className="flex items-start gap-2.5">
                          <span className="px-2 py-0.5 rounded bg-ash/30 text-off-black font-bold text-[10px] uppercase">
                            {item.category}
                          </span>
                          <div>
                            <div className="font-bold text-off-black">{item.description}</div>
                            <div className="text-[10px] text-smoke">Expected entity type: {item.expected_entity}</div>
                          </div>
                        </div>

                        <div className="text-rose-600 font-bold sm:text-right shrink-0">
                          Impact: ₹{item.potential_impact_inr?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SECTION 6: RECOMMENDED HUMAN NEXT ACTION (HERO BANNER) */}
              <div className="p-6 bg-off-black text-parchment rounded-2xl shadow-md space-y-3 relative overflow-hidden">
                <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 font-bold uppercase tracking-wider">
                  <UserCheck className="w-4 h-4 text-emerald-400" />
                  <span>Recommended Human Action for Finance Operator</span>
                </div>

                <p className="font-serif text-xl text-parchment leading-snug">
                  {handoff.recommended_human_action}
                </p>

                <div className="pt-2 flex flex-wrap items-center gap-3 text-xs font-mono text-ash">
                  <span>1. Check subsequent settlement cycles</span>
                  <span>&bull;</span>
                  <span>2. Inspect manual adjustment ledger</span>
                  <span>&bull;</span>
                  <span>3. Re-ingest updated statement</span>
                </div>
              </div>

              {/* SECTION 7: EXPANDABLE INVESTIGATION TIMELINE */}
              <div className="bg-white rounded-2xl border border-ash overflow-hidden shadow-sm">
                <button
                  onClick={() => setShowTimeline(!showTimeline)}
                  className="w-full p-5 bg-white hover:bg-parchment/40 transition-colors flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-lake-blue" />
                    <h3 className="font-serif text-lg text-off-black">
                      Investigation Audit Timeline ({handoff.investigation_timeline?.length || 0} Events)
                    </h3>
                  </div>
                  {showTimeline ? <ChevronUp className="w-4 h-4 text-smoke" /> : <ChevronDown className="w-4 h-4 text-smoke" />}
                </button>

                {showTimeline && (
                  <div className="p-5 pt-0 border-t border-ash/40 space-y-3 font-mono text-xs">
                    {handoff.investigation_timeline?.map((step: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-start gap-4 p-3 rounded-xl bg-parchment/60 hover:bg-parchment transition-colors border border-ash/50"
                      >
                        <span className="text-[11px] font-bold text-lake-blue shrink-0 w-16">
                          {step.timestamp}
                        </span>

                        <div className="flex-1 space-y-0.5">
                          <div className="font-bold text-off-black flex items-center gap-2">
                            <span>{step.action}</span>
                            {step.status === "PASS" && (
                              <span className="px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 text-[9px] font-bold">PASS</span>
                            )}
                            {step.status === "FAIL" && (
                              <span className="px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 text-[9px] font-bold">FAIL</span>
                            )}
                            {step.status === "REJECTED" && (
                              <span className="px-1.5 py-0.2 rounded bg-rose-200 text-rose-900 text-[9px] font-bold">DECOY REJECTED</span>
                            )}
                          </div>
                          <div className="text-[11px] text-graphite">{step.detail}</div>
                        </div>

                        {step.audit_event_id && (
                          <span className="text-[10px] text-smoke shrink-0 font-mono">
                            {step.audit_event_id}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-8 text-center bg-white rounded-2xl border border-ash text-xs font-mono text-smoke">
              No escalation data available for this scenario.
            </div>
          )}
        </div>

        {/* =========================================================================
            FOOTER — Principle & Dismiss
            ========================================================================= */}
        <div className="p-4 sm:p-5 bg-white border-t border-ash flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-smoke">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>
              <strong>Resolved cases show the proof. Escalated cases show the investigation.</strong>
            </span>
          </div>

          <button
            onClick={onClose}
            className="w-full sm:w-auto px-6 py-2.5 rounded-pill bg-off-black text-parchment hover:bg-lake-blue font-bold text-xs uppercase tracking-wider transition-all shadow-sm"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
}

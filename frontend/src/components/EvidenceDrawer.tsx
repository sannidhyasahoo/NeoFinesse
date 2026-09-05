"use client";

import React, { useState } from "react";
import { EvidenceNode } from "@/types";
import { Copy, Check, FileSpreadsheet, ShieldAlert, ShieldCheck, Layers } from "lucide-react";

interface EvidenceDrawerProps {
  evidence: EvidenceNode | null;
  className?: string;
  onViewSource?: (evidence: EvidenceNode) => void;
}

export default function EvidenceDrawer({ evidence, className = "", onViewSource }: EvidenceDrawerProps) {
  const [copied, setCopied] = useState(false);

  if (!evidence) {
    return (
      <div className={`bg-white rounded-3xl border border-ash p-6 flex flex-col items-center justify-center text-center text-smoke font-mono text-xs ${className}`}>
        <Layers className="w-8 h-8 text-ash mb-2 animate-bounce" />
        <p>Click any node in the trace graph to see where that transaction lives in the original file.</p>
      </div>
    );
  }

  const isRejected = evidence.status === "REJECTED";

  const handleCopyHash = () => {
    navigator.clipboard.writeText(evidence.record_hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedAmount =
    evidence.amount_inr < 0
      ? `-₹${Math.abs(evidence.amount_inr).toFixed(2)}`
      : `₹${evidence.amount_inr.toFixed(2)}`;

  // Map internal level codes to readable labels
  const levelLabel =
    evidence.evidence_level === "L5" ? "Traced to cell" :
      evidence.evidence_level === "L2" ? "Partial trace" :
        evidence.evidence_level === "L1" ? "Not linked" :
          evidence.evidence_level;

  return (
    <div className={`bg-white rounded-3xl border border-ash p-6 space-y-5 transition-all shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-ash/50 pb-4">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-lake-blue" />
          <span className="font-serif text-lg text-off-black">Source File Record</span>
        </div>
        <div className="flex items-center gap-2">
          {onViewSource && (
            <button
              onClick={() => onViewSource(evidence)}
              className="px-3 py-1 bg-parchment hover:bg-off-black hover:text-parchment border border-ash rounded-pill text-[11px] font-mono text-off-black transition-all flex items-center gap-1.5 shadow-sm font-semibold"
              title="Inspect exact spreadsheet cell and surrounding context"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-lake-blue" />
              <span>View Source</span>
            </button>
          )}
          <span
            className={`px-2.5 py-0.5 rounded-pill text-[10px] font-mono uppercase tracking-wider font-semibold ${isRejected
                ? "bg-rose-100 text-rose-800 border border-rose-200"
                : "bg-emerald-100 text-emerald-800 border border-emerald-200"
              }`}
          >
            {isRejected ? "Rejected — wrong link" : "Verified — all checks passed"}
          </span>
        </div>
      </div>

      {/* Property Grid */}
      <div className="space-y-4 text-xs font-mono">
        {/* Evidence ID & Trace Level */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Record ID & Traceability
          </div>
          <div className="flex items-center gap-2 font-medium text-off-black">
            <span className="font-bold text-lake-blue">{evidence.evidence_id}</span>
            <span>&bull;</span>
            <span className="px-2 py-0.5 rounded-md bg-periwinkle-mist/50 text-off-black text-[11px]">
              {levelLabel}
            </span>
          </div>
        </div>

        {/* Entity Type & Amount */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Transaction Type & Amount
          </div>
          <div className="flex items-center gap-3">
            <span className="font-medium text-graphite">{evidence.entity_type}</span>
            <span className={`font-bold text-sm ${isRejected ? "text-rose-600" : "text-emerald-700"}`}>
              {formattedAmount}
            </span>
          </div>
        </div>

        {/* Relational Path */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Transaction Chain
          </div>
          <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 text-graphite text-[11px] leading-relaxed break-words">
            {evidence.relationship_path}
          </div>
        </div>

        {/* Source File, Sheet & Cell */}
        <div>
          <div className="flex items-center justify-between text-[10px] uppercase text-smoke tracking-wider mb-1">
            <span>Location in Original File</span>
            {onViewSource && (
              <button
                onClick={() => onViewSource(evidence)}
                className="text-lake-blue hover:underline font-bold flex items-center gap-1 text-[11px]"
              >
                <span>Open in Cell Viewer &rarr;</span>
              </button>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2.5 py-1 bg-ash/20 rounded-lg text-off-black">
              📄 {evidence.source_file}
            </span>
            <span className="px-2.5 py-1 bg-ash/20 rounded-lg text-off-black">
              Sheet: {evidence.sheet}
            </span>
            <span className="px-2.5 py-1 bg-lake-blue/10 text-lake-blue font-bold rounded-lg border border-lake-blue/20">
              Cell: {evidence.cell}
            </span>
            <span className="px-2.5 py-1 bg-ash/20 rounded-lg text-off-black">
              Row: {evidence.row}
            </span>
          </div>
        </div>

        {/* SHA-256 Record Hash */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Cryptographic Record Hash (SHA-256)
          </div>
          <div className="flex items-center justify-between gap-2 p-2 bg-parchment rounded-xl border border-ash/70">
            <span className="text-[10px] text-smoke font-mono truncate max-w-[240px]">
              {evidence.record_hash}
            </span>
            <button
              onClick={handleCopyHash}
              className="px-2 py-1 rounded bg-white hover:bg-ash/30 text-off-black transition-colors flex items-center gap-1 text-[10px]"
              title="Copy record hash"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          </div>
        </div>

        {/* Verification or Rejection note */}
        {isRejected ? (
          <div className="p-3 bg-rose-50 rounded-2xl border border-rose-200 text-rose-900 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-rose-800 text-[11px]">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
              <span>Why this was rejected</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              {evidence.rejection_reason || "Not linked to this settlement batch."}
            </p>
            {evidence.lesson && (
              <p className="text-[10px] text-rose-700 italic pt-1">
                💡 {evidence.lesson}
              </p>
            )}
          </div>
        ) : (
          <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-200 text-emerald-900 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-emerald-800 text-[11px]">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Verification passed</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              {evidence.description || "All five checks passed for this record."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

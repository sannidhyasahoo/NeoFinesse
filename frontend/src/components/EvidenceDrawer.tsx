"use client";

import React, { useState } from "react";
import { EvidenceNode } from "@/types";
import { Copy, Check, FileSpreadsheet, ShieldAlert, ShieldCheck, Hash, Layers } from "lucide-react";

interface EvidenceDrawerProps {
  evidence: EvidenceNode | null;
  className?: string;
}

export default function EvidenceDrawer({ evidence, className = "" }: EvidenceDrawerProps) {
  const [copied, setCopied] = useState(false);

  if (!evidence) {
    return (
      <div className={`bg-white rounded-3xl border border-ash p-6 flex flex-col items-center justify-center text-center text-smoke font-mono text-xs ${className}`}>
        <Layers className="w-8 h-8 text-ash mb-2 animate-bounce" />
        <p>Click any node in the investigation graph to inspect cell-level provenance.</p>
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

  return (
    <div className={`bg-white rounded-3xl border border-ash p-6 space-y-5 transition-all shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-ash/50 pb-4">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-lake-blue" />
          <span className="font-serif text-lg text-off-black">Cell-Level Evidence Inspector</span>
        </div>
        <span
          className={`px-2.5 py-0.5 rounded-pill text-[10px] font-mono uppercase tracking-wider font-semibold ${
            isRejected
              ? "bg-rose-100 text-rose-800 border border-rose-200"
              : "bg-emerald-100 text-emerald-800 border border-emerald-200"
          }`}
        >
          {isRejected ? "Decoy (Rejected)" : "Verified Proof (L5)"}
        </span>
      </div>

      {/* Property Grid */}
      <div className="space-y-4 text-xs font-mono">
        {/* Evidence ID & Level */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Evidence Identifier & Level
          </div>
          <div className="flex items-center gap-2 font-medium text-off-black">
            <span className="font-bold text-lake-blue">{evidence.evidence_id}</span>
            <span>&bull;</span>
            <span className="px-2 py-0.5 rounded-md bg-periwinkle-mist/50 text-off-black text-[11px]">
              {evidence.evidence_level} (Cell Coordinates Verified)
            </span>
          </div>
        </div>

        {/* Entity Type & Amount */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Entity Type & Evaluated Amount
          </div>
          <div className="flex items-center gap-3">
            <span className="font-medium text-graphite">{evidence.entity_type}</span>
            <span
              className={`font-bold text-sm ${
                isRejected ? "text-rose-600" : "text-emerald-700"
              }`}
            >
              {formattedAmount}
            </span>
          </div>
        </div>

        {/* Relational Path */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Causal Relational Path
          </div>
          <div className="p-2.5 bg-parchment rounded-xl border border-ash/60 text-graphite text-[11px] leading-relaxed break-words">
            {evidence.relationship_path}
          </div>
        </div>

        {/* Source File, Sheet & Cell */}
        <div>
          <div className="text-[10px] uppercase text-smoke tracking-wider mb-1">
            Excel / CSV File Coordinate
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
            SHA-256 Cryptographic Record Hash
          </div>
          <div className="flex items-center justify-between gap-2 p-2 bg-parchment rounded-xl border border-ash/70">
            <span className="text-[10px] text-smoke font-mono truncate max-w-[240px]">
              {evidence.record_hash}
            </span>
            <button
              onClick={handleCopyHash}
              className="px-2 py-1 rounded bg-white hover:bg-ash/30 text-off-black transition-colors flex items-center gap-1 text-[10px]"
              title="Copy SHA-256 Hash"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
          </div>
        </div>

        {/* Dynamic Verification or Rejection Note */}
        {isRejected ? (
          <div className="p-3 bg-rose-50 rounded-2xl border border-rose-200 text-rose-900 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-rose-800 text-[11px]">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
              <span>Decoy Rejection Reason</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              {evidence.rejection_reason || "Unlinked to settlement batch."}
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
              <span>Deterministic Verification Note</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              {evidence.description || "Satisfies all 5 deterministic financial constraints."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

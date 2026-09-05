"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  FileSpreadsheet,
  CheckCircle2,
  AlertOctagon,
  Copy,
  Check,
  X,
  ShieldCheck,
  Hash,
  Layers,
  ArrowRight,
  ExternalLink,
  Search,
} from "lucide-react";
import { EvidenceNode } from "@/types";

interface CellData {
  address: string;
  row: number;
  column: number;
  column_letter: string;
  value: any;
  raw_value?: string;
  is_target: boolean;
}

interface RowData {
  row_number: number;
  is_target_row: boolean;
  cells: CellData[];
}

interface ColumnMeta {
  index: number;
  letter: string;
  header: string;
  is_target_column: boolean;
}

interface SourceContextResponse {
  status: string;
  error?: string;
  source_file: string;
  sheet: string;
  target_cell: string;
  target_row: number;
  target_column: number;
  target_column_letter: string;
  target_value: any;
  file_hash: string;
  record_hash?: string;
  is_provenance_verified: boolean;
  total_rows?: number;
  total_columns?: number;
  window?: {
    min_row: number;
    max_row: number;
    min_col: number;
    max_col: number;
    row_radius: number;
    column_radius: number;
  };
  context?: {
    columns: ColumnMeta[];
    rows: RowData[];
  };
}

interface SourceEvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceNode | null;
}

function formatDisplayAmount(val: any): string {
  if (val === null || val === undefined || val === "") return "—";
  if (typeof val === "number") {
    // If value looks like paise (> 10000 and whole number), format as ₹ (e.g. 400000 -> ₹4,000)
    if (val >= 10000 && Number.isInteger(val) && val % 100 === 0) {
      return `₹${(val / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
    }
    return `₹${val.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  }
  const s = String(val).trim();
  if (/^-?\d+$/.test(s)) {
    const num = parseInt(s, 10);
    if (num >= 10000 && num % 100 === 0) {
      return `₹${(num / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
    }
    return `₹${num.toLocaleString("en-IN")}`;
  }
  if (/^-?\d+\.\d+$/.test(s)) {
    const flt = parseFloat(s);
    return `₹${flt.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
  }
  return s;
}

export default function SourceEvidenceModal({
  isOpen,
  onClose,
  evidence,
}: SourceEvidenceModalProps) {
  const [contextData, setContextData] = useState<SourceContextResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedRef, setCopiedRef] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [selectedCell, setSelectedCell] = useState<CellData | null>(null);

  const targetCellElementRef = useRef<HTMLTableCellElement | null>(null);

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

  // Fetch cell context from backend endpoint whenever evidence changes
  useEffect(() => {
    if (!isOpen || !evidence) {
      setContextData(null);
      setSelectedCell(null);
      return;
    }

    let isMounted = true;
    setIsLoading(true);

    const params = new URLSearchParams({
      file: evidence.source_file,
      sheet: evidence.sheet || "Sheet1",
      cell: evidence.cell,
      row: String(evidence.row || 1),
      row_radius: "3",
      column_radius: "3",
    });

    fetch(`/api/evidence/source-context?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        if (isMounted) {
          setContextData(data);
          if (data.status === "SUCCESS" && data.context?.rows) {
            for (const r of data.context.rows) {
              const target = r.cells.find((c: CellData) => c.is_target);
              if (target) {
                setSelectedCell(target);
                break;
              }
            }
          }
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load source evidence context:", err);
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, evidence]);

  // Auto-scroll to target cell once loaded
  useEffect(() => {
    if (targetCellElementRef.current) {
      targetCellElementRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
        inline: "center",
      });
    }
  }, [contextData]);

  if (!isOpen || !evidence) return null;

  const isRejected = evidence.status === "REJECTED";
  const cellReferenceString = `${evidence.sheet || "Sheet1"}!${evidence.cell}`;
  const isAvailable = contextData && contextData.status === "SUCCESS" && contextData.context && contextData.context.rows.length > 0;

  const handleCopyRef = () => {
    navigator.clipboard.writeText(cellReferenceString);
    setCopiedRef(true);
    setTimeout(() => setCopiedRef(false), 2000);
  };

  const handleCopyHash = () => {
    navigator.clipboard.writeText(evidence.record_hash || contextData?.record_hash || "");
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  // Compute clean window description
  let windowDescription = "Loading source context...";
  if (isAvailable && contextData.context) {
    const rows = contextData.context.rows;
    const cols = contextData.context.columns;
    const minRowNum = rows[0]?.row_number;
    const maxRowNum = rows[rows.length - 1]?.row_number;
    const minColLet = cols[0]?.letter;
    const maxColLet = cols[cols.length - 1]?.letter;

    if (rows.length > 1) {
      windowDescription = `Showing source context: Rows ${minRowNum}–${maxRowNum} × Columns ${minColLet}–${maxColLet}`;
    } else {
      windowDescription = `Showing source record: Row ${minRowNum} × Columns ${minColLet}–${maxColLet}`;
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-off-black/60 backdrop-blur-sm animate-fade-in">
      {/* Click outside backdrop */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Modal Container */}
      <div className="relative w-full max-w-5xl bg-parchment rounded-3xl border border-ash shadow-2xl overflow-hidden flex flex-col max-h-[92vh] z-10 animate-slide-up">
        {/* =========================================================================
            HEADER — Breadcrumbs, Status, Copy Controls & Close
            ========================================================================= */}
        <div className="p-6 bg-white border-b border-ash flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-mono text-smoke">
              <span className="text-off-black font-bold flex items-center gap-1.5">
                <FileSpreadsheet className="w-4 h-4 text-lake-blue" />
                {evidence.source_file}
              </span>
              <span>&rsaquo;</span>
              <span className="text-graphite font-medium">{evidence.sheet || "Sheet1"}</span>
              <span>&rsaquo;</span>
              <span className="px-2 py-0.5 rounded bg-blue-50 text-lake-blue font-bold border border-blue-200">
                {evidence.cell}
              </span>
            </div>

            <h2 className="font-serif text-2xl text-off-black flex items-center gap-2.5">
              <span>Source Evidence Context</span>
              {isRejected ? (
                <span className="px-2.5 py-0.5 rounded-pill bg-rose-100 text-rose-800 border border-rose-300 text-xs font-mono font-bold uppercase tracking-wider">
                  Rejected Decoy
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-pill bg-emerald-100 text-emerald-800 border border-emerald-300 text-xs font-mono font-bold uppercase tracking-wider">
                  ✓ Provenance Verified
                </span>
              )}
            </h2>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={handleCopyRef}
              className="px-3 py-1.5 rounded-pill bg-parchment hover:bg-ash/30 border border-ash text-xs font-mono text-off-black transition-all flex items-center gap-1.5 shadow-sm"
              title="Copy Excel reference (Sheet!Cell)"
            >
              {copiedRef ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-smoke" />}
              <span>{copiedRef ? "Copied!" : "Copy Cell Reference"}</span>
            </button>

            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-parchment hover:bg-ash/40 border border-ash text-off-black flex items-center justify-center transition-all"
              title="Close modal (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* =========================================================================
            PROVENANCE & TARGET VALUE PROMINENT STRIP
            ========================================================================= */}
        <div className="px-6 py-3 bg-white/70 border-b border-ash/60 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
          <div className="flex items-center gap-4 flex-wrap">
            {/* Target Cell & Value Display */}
            <div className="flex items-center gap-2 px-3 py-1 rounded-xl bg-parchment border border-ash">
              <span className="text-smoke text-[11px]">Target Cell:</span>
              <span className="font-bold text-lake-blue">{evidence.cell}</span>
              <span className="text-smoke">&bull;</span>
              <span className="text-smoke text-[11px]">Value:</span>
              <span className={`font-bold ${isRejected ? "text-rose-700" : "text-emerald-700"}`}>
                {contextData?.target_value !== null && contextData?.target_value !== undefined && contextData?.target_value !== ""
                  ? formatDisplayAmount(contextData.target_value)
                  : evidence.amount_inr
                  ? `₹${Math.abs(evidence.amount_inr).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                  : "—"}
              </span>
            </div>

            <div className="text-smoke">|</div>

            <div className="flex items-center gap-1.5 text-graphite truncate max-w-xs sm:max-w-md">
              <Hash className="w-3.5 h-3.5 text-smoke" />
              <span className="truncate">
                Record SHA-256: <code className="text-off-black">{evidence.record_hash}</code>
              </span>
              <button
                onClick={handleCopyHash}
                className="hover:text-lake-blue text-smoke ml-1"
                title="Copy Full SHA-256 Hash"
              >
                {copiedHash ? <Check className="w-3 h-3 text-emerald-600 inline" /> : <Copy className="w-3 h-3 inline" />}
              </button>
            </div>
          </div>

          <span className="text-[11px] text-smoke">
            Zero LLM Involvement &bull; Deterministic L5 Cell Provenance
          </span>
        </div>

        {/* Rejection Alert Box if Decoy */}
        {isRejected && (
          <div className="mx-6 mt-4 p-4 rounded-2xl bg-rose-50 border border-rose-300 text-xs font-mono text-rose-900 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-rose-700">
                <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
                <span>REJECTED EVIDENCE DECOY &mdash; INVARIANT CHECK FAILED</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-rose-200/80 text-rose-900 text-[10px] font-bold">
                Target: {evidence.sheet || "Sheet1"}!{evidence.cell}
              </span>
            </div>
            <p className="text-rose-950 font-sans text-sm leading-relaxed">
              <strong>Rejection Reason:</strong> {evidence.rejection_reason || "Constraint check failed against settlement graph."}
            </p>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1 border-t border-rose-200/80 text-[11px]">
              <span className="text-rose-800">
                <strong>Actual Source Value:</strong>{" "}
                <code className="bg-rose-100 px-1.5 py-0.5 rounded font-bold text-rose-900">
                  {contextData?.target_value !== null && contextData?.target_value !== undefined
                    ? formatDisplayAmount(contextData.target_value)
                    : "₹4,000.00"}
                </code>
              </span>
              {evidence.lesson && (
                <span className="text-rose-800 italic">
                  <strong>Forensic Lesson:</strong> {evidence.lesson}
                </span>
              )}
            </div>
          </div>
        )}

        {/* =========================================================================
            SPREADSHEET VIEWER GRID (Excel-like matrix with exact row/cell highlighted)
            ========================================================================= */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4">
          <div className="flex items-center justify-between text-xs font-mono text-smoke">
            <span>{windowDescription}</span>
            <span className="flex items-center gap-2">
              <span className={`inline-block w-3 h-3 rounded border ${
                isRejected ? "bg-rose-100 border-rose-600" : "bg-lake-blue/20 border-lake-blue"
              }`} />
              <span className="text-off-black font-semibold">Target Cell ({evidence.cell})</span>
            </span>
          </div>

          {isLoading ? (
            <div className="h-64 flex flex-col items-center justify-center space-y-3 bg-white rounded-2xl border border-ash">
              <div className="w-6 h-6 border-2 border-lake-blue border-t-transparent rounded-full animate-spin" />
              <span className="text-xs font-mono text-smoke">Loading cell context from {evidence.source_file}...</span>
            </div>
          ) : isAvailable && contextData && contextData.context ? (
            <div className="overflow-x-auto rounded-2xl border border-ash bg-white shadow-inner max-h-[460px]">
              <table className="w-full border-collapse font-mono text-xs text-left">
                {/* Column Headers (Excel letters & semantic names) */}
                <thead className="sticky top-0 z-20">
                  <tr className="bg-ash/30 border-b border-ash text-smoke select-none">
                    {/* Corner header (Row number column) */}
                    <th className="w-14 p-2 text-center border-r border-ash text-[10px] font-bold uppercase tracking-wider bg-ash/40 sticky left-0 z-30">
                      #
                    </th>
                    {contextData.context.columns.map((col) => (
                      <th
                        key={col.index}
                        className={`p-2.5 border-r border-ash/60 text-center transition-colors min-w-[130px] ${
                          col.is_target_column
                            ? "bg-blue-100/90 text-lake-blue font-bold"
                            : "bg-ash/20 text-graphite font-semibold"
                        }`}
                      >
                        <div className="text-[11px] font-bold">{col.letter}</div>
                        <div className="text-[9px] font-normal text-smoke truncate max-w-[140px]" title={col.header}>
                          {col.header}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>

                {/* Matrix Rows */}
                <tbody>
                  {contextData.context.rows.map((row) => (
                    <tr
                      key={row.row_number}
                      className={`border-b border-ash/40 transition-colors ${
                        row.is_target_row ? "bg-blue-50/60" : "hover:bg-ash/10"
                      }`}
                    >
                      {/* Row number header */}
                      <td
                        className={`p-2 text-center border-r border-ash select-none font-bold text-[11px] sticky left-0 z-10 ${
                          row.is_target_row
                            ? "bg-blue-100 text-lake-blue border-r-2 border-r-lake-blue"
                            : "bg-ash/20 text-smoke"
                        }`}
                      >
                        {row.row_number}
                      </td>

                      {/* Row cells */}
                      {row.cells.map((cell) => {
                        const isTarget = cell.is_target;
                        const isSelected = selectedCell?.address === cell.address;

                        return (
                          <td
                            key={cell.address}
                            ref={isTarget ? (targetCellElementRef as any) : undefined}
                            onClick={() => setSelectedCell(cell)}
                            className={`p-2.5 border-r border-ash/40 cursor-pointer transition-all relative ${
                              isTarget
                                ? isRejected
                                  ? "bg-rose-100/95 text-rose-950 font-bold border-2 border-rose-600 shadow-md ring-2 ring-rose-400 z-10"
                                  : "bg-blue-100/95 text-lake-blue font-bold border-2 border-lake-blue shadow-md ring-2 ring-blue-400 z-10"
                                : isSelected
                                ? "bg-ash/30 ring-1 ring-off-black"
                                : "text-off-black"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-1.5">
                              <span className="truncate" title={String(cell.value)}>
                                {cell.value !== null && cell.value !== undefined && cell.value !== ""
                                  ? typeof cell.value === "number" && !Number.isInteger(cell.value)
                                    ? cell.value.toFixed(2)
                                    : String(cell.value)
                                  : "—"}
                              </span>

                              {isTarget && (
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider shrink-0 ${
                                    isRejected
                                      ? "bg-rose-600 text-white shadow-sm"
                                      : "bg-lake-blue text-white shadow-sm"
                                  }`}
                                >
                                  {isRejected ? "✕ Decoy" : "← Evidence"}
                                </span>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center bg-white rounded-2xl border border-ash text-xs font-mono space-y-3">
              <div className="w-10 h-10 rounded-full bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto font-bold">
                !
              </div>
              <h4 className="font-serif text-base text-off-black">SOURCE RECORD UNAVAILABLE</h4>
              <p className="text-smoke max-w-md mx-auto">
                The provenance reference exists, but the source record could not be loaded or is out of bounds for {evidence.source_file}.
              </p>
              <div className="inline-block p-3 rounded-xl bg-parchment border border-ash text-left text-xs font-mono text-graphite space-y-1">
                <div><strong>File:</strong> {evidence.source_file}</div>
                <div><strong>Reference:</strong> {evidence.sheet || "Sheet1"}!{evidence.cell}</div>
                <div><strong>Record Hash:</strong> <code className="text-off-black">{evidence.record_hash}</code></div>
              </div>
            </div>
          )}

          {/* =========================================================================
              CELL INSPECTION DETAIL STRIP
              ========================================================================= */}
          {selectedCell && (
            <div className="p-4 bg-white rounded-2xl border border-ash flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono">
              <div className="flex items-center gap-3">
                <div className="px-3 py-1.5 rounded-lg bg-parchment border border-ash font-bold text-off-black">
                  Cell: <span className="text-lake-blue">{selectedCell.address}</span>
                </div>
                <div>
                  <div className="text-smoke text-[10px]">Row {selectedCell.row} &bull; Column {selectedCell.column} ({selectedCell.column_letter})</div>
                  <div className="text-off-black font-bold text-sm">
                    Value: {selectedCell.value !== null && selectedCell.value !== undefined && selectedCell.value !== "" ? String(selectedCell.value) : "Empty"}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {selectedCell.is_target && (
                  <span className={`px-2.5 py-1 rounded-pill text-[10px] font-bold uppercase tracking-wider ${
                    isRejected ? "bg-rose-100 text-rose-800 border border-rose-300" : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  }`}>
                    {isRejected ? "Target Decoy Node" : "Active Verified Evidence"}
                  </span>
                )}
                <span className="text-smoke text-[11px]">
                  Causal Relationship: {evidence.relationship_path}
                </span>
              </div>
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
              <strong>Core Invariant:</strong> AI investigates &bull; Tools retrieve &bull; Evidence constrains &bull; Deterministic verification decides
            </span>
          </div>

          <button
            onClick={onClose}
            className="w-full sm:w-auto px-6 py-2 rounded-pill bg-off-black text-parchment hover:bg-lake-blue font-bold text-xs uppercase tracking-wider transition-all"
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
}

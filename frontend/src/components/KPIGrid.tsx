"use client";

import React from "react";
import { ShieldCheck, CheckCircle2, AlertOctagon, FileSpreadsheet, Layers } from "lucide-react";

interface KPIGridProps {
  kpis?: {
    total_settlements: number;
    total_variances: number;
    resolved_count: number;
    escalated_count: number;
    false_closure_rate_pct: number;
    evidence_coverage_pct: number;
  };
}

export default function KPIGrid({ kpis }: KPIGridProps) {
  const data = kpis || {
    total_settlements: 19,
    total_variances: 23,
    resolved_count: 12,
    escalated_count: 11,
    false_closure_rate_pct: 0.0,
    evidence_coverage_pct: 100.0,
  };

  const resolvedPct = Math.round((data.resolved_count / data.total_variances) * 100);
  const escalatedPct = Math.round((data.escalated_count / data.total_variances) * 100);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {/* KPI 1 */}
      <div className="bg-parchment rounded-3xl border border-ash p-5 flex flex-col justify-between transition-all hover:border-off-black">
        <div className="flex items-center justify-between text-smoke mb-2">
          <span className="text-[11px] uppercase font-mono tracking-wider">Settlements</span>
          <Layers className="w-3.5 h-3.5" />
        </div>
        <div>
          <div className="text-3xl font-mono font-medium text-off-black tracking-tight">
            {data.total_settlements}
          </div>
          <div className="text-[11px] font-mono text-graphite mt-1">
            Gateway batches loaded
          </div>
        </div>
      </div>

      {/* KPI 2 */}
      <div className="bg-parchment rounded-3xl border border-ash p-5 flex flex-col justify-between transition-all hover:border-off-black">
        <div className="flex items-center justify-between text-smoke mb-2">
          <span className="text-[11px] uppercase font-mono tracking-wider">Discrepancies</span>
          <FileSpreadsheet className="w-3.5 h-3.5" />
        </div>
        <div>
          <div className="text-3xl font-mono font-medium text-off-black tracking-tight">
            {data.total_variances}
          </div>
          <div className="text-[11px] font-mono text-graphite mt-1">
            Amount mismatches investigated
          </div>
        </div>
      </div>

      {/* KPI 3 (Highlight) */}
      <div className="bg-periwinkle-mist/40 rounded-3xl border border-lake-blue/30 p-5 flex flex-col justify-between transition-all hover:border-lake-blue">
        <div className="flex items-center justify-between text-lake-blue mb-2">
          <span className="text-[11px] uppercase font-mono tracking-wider font-semibold">Resolved</span>
          <CheckCircle2 className="w-3.5 h-3.5" />
        </div>
        <div>
          <div className="text-3xl font-mono font-medium text-lake-blue tracking-tight">
            {data.resolved_count} <span className="text-sm font-normal text-graphite">({resolvedPct}%)</span>
          </div>
          <div className="text-[11px] font-mono text-graphite mt-1">
            Explained with full proof
          </div>
        </div>
      </div>

      {/* KPI 4 */}
      <div className="bg-parchment rounded-3xl border border-ash p-5 flex flex-col justify-between transition-all hover:border-off-black">
        <div className="flex items-center justify-between text-smoke mb-2">
          <span className="text-[11px] uppercase font-mono tracking-wider">Escalated</span>
          <AlertOctagon className="w-3.5 h-3.5 text-crimson" />
        </div>
        <div>
          <div className="text-3xl font-mono font-medium text-off-black tracking-tight">
            {data.escalated_count} <span className="text-sm font-normal text-graphite">({escalatedPct}%)</span>
          </div>
          <div className="text-[11px] font-mono text-graphite mt-1">
            Sent to human review
          </div>
        </div>
      </div>

      {/* KPI 5 (Safety highlight) */}
      <div className="bg-emerald-50/70 rounded-3xl border border-emerald-300 p-5 flex flex-col justify-between transition-all hover:border-emerald-500">
        <div className="flex items-center justify-between text-emerald-800 mb-2">
          <span className="text-[11px] uppercase font-mono tracking-wider font-bold">Wrong Closures</span>
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
        </div>
        <div>
          <div className="text-3xl font-mono font-bold text-emerald-700 tracking-tight">
            {data.false_closure_rate_pct.toFixed(1)}%
          </div>
          <div className="text-[11px] font-mono text-emerald-900 mt-1">
            No case incorrectly closed
          </div>
        </div>
      </div>

      {/* KPI 6 */}
      <div className="bg-parchment rounded-3xl border border-ash p-5 flex flex-col justify-between transition-all hover:border-off-black">
        <div className="flex items-center justify-between text-smoke mb-2">
          <span className="text-[11px] uppercase font-mono tracking-wider">Traceable</span>
          <ShieldCheck className="w-3.5 h-3.5 text-lake-blue" />
        </div>
        <div>
          <div className="text-3xl font-mono font-medium text-off-black tracking-tight">
            {data.evidence_coverage_pct.toFixed(0)}%
          </div>
          <div className="text-[11px] font-mono text-graphite mt-1">
            Pinned to source file cell
          </div>
        </div>
      </div>
    </div>
  );
}

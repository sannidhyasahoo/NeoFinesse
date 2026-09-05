"use client";

import React, { useState } from "react";
import { Scenario } from "@/types";
import { Search, Filter, ArrowUpRight, CheckCircle, AlertTriangle, Clock } from "lucide-react";

interface CaseTableProps {
  scenarios: Scenario[];
  onInspectScenario: (scenario: Scenario) => void;
}

export default function CaseTable({ scenarios, onInspectScenario }: CaseTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const filtered = scenarios.filter((s) => {
    const matchesSearch =
      s.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.scenario_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.settlement_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.primary_cause.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === "ALL" || s.expected_outcome === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Search & Filter Controls */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-smoke absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Case ID, Settlement ID, or Cause..."
            className="w-full bg-white border border-ash rounded-pill pl-10 pr-4 py-2 text-xs font-mono text-off-black placeholder:text-smoke focus:outline-none focus:border-lake-blue focus:ring-1 focus:ring-lake-blue"
          />
        </div>

        {/* Status Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
          {[
            { label: `All (${scenarios.length})`, val: "ALL" },
            { label: "Resolved", val: "RESOLVED" },
            { label: "Delayed Credit", val: "VALID_DELAYED_CREDIT" },
            { label: "Partial", val: "PARTIALLY_RESOLVED" },
            { label: "Escalated", val: "ESCALATE" },
          ].map((f) => {
            const isActive = statusFilter === f.val;
            return (
              <button
                key={f.val}
                onClick={() => setStatusFilter(f.val)}
                className={`px-3 py-1.5 rounded-pill text-xs transition-all uppercase tracking-wider ${
                  isActive
                    ? "bg-off-black text-parchment font-medium shadow-sm"
                    : "bg-white text-graphite hover:bg-ash/20 border border-ash/70"
                }`}
              >
                {f.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-3xl border border-ash overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-parchment/70 border-b border-ash text-[11px] uppercase tracking-wider text-smoke font-semibold">
                <th className="py-3.5 px-4">Case ID</th>
                <th className="py-3.5 px-4">Scenario ID</th>
                <th className="py-3.5 px-4">Settlement ID</th>
                <th className="py-3.5 px-4">Expected</th>
                <th className="py-3.5 px-4">Bank Credit</th>
                <th className="py-3.5 px-4">Variance</th>
                <th className="py-3.5 px-4">Outcome</th>
                <th className="py-3.5 px-4">Root Cause</th>
                <th className="py-3.5 px-4">Level</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ash/40">
              {filtered.map((s) => {
                const isResolved =
                  s.expected_outcome === "RESOLVED" ||
                  s.expected_outcome === "VALID_DELAYED_CREDIT";
                const isPartial = s.expected_outcome === "PARTIALLY_RESOLVED";
                const isEscalate = s.expected_outcome === "ESCALATE";

                const varFormatted =
                  s.variance_inr < 0
                    ? `-₹${Math.abs(s.variance_inr).toFixed(2)}`
                    : `+₹${s.variance_inr.toFixed(2)}`;

                return (
                  <tr
                    key={s.scenario_id}
                    className="hover:bg-parchment/40 transition-colors"
                  >
                    <td className="py-3 px-4 font-bold text-lake-blue">
                      {s.case_id}
                    </td>
                    <td className="py-3 px-4 text-graphite text-[11px] truncate max-w-[160px]">
                      {s.scenario_id}
                    </td>
                    <td className="py-3 px-4 text-smoke text-[11px]">
                      {s.settlement_id}
                    </td>
                    <td className="py-3 px-4 text-off-black">
                      ₹{s.expected_amount_inr.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-off-black">
                      ₹{s.actual_bank_credit_inr.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 font-bold">
                      <span
                        className={
                          s.variance_inr < 0 ? "text-rose-600" : "text-emerald-600"
                        }
                      >
                        {varFormatted}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                          isResolved
                            ? "bg-emerald-100 text-emerald-800"
                            : isPartial
                            ? "bg-amber-100 text-amber-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {s.expected_outcome}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[11px] text-graphite max-w-[200px] truncate">
                      {s.primary_cause}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-1.5 py-0.5 rounded bg-ash/30 text-off-black text-[10px] font-medium">
                        {s.evidence_level}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onInspectScenario(s)}
                        className="px-3 py-1 bg-parchment hover:bg-off-black hover:text-white border border-ash rounded-pill text-[11px] uppercase tracking-wider transition-all inline-flex items-center gap-1"
                      >
                        Inspect <ArrowUpRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <div className="py-12 text-center text-smoke font-mono text-xs">
            No variance scenarios match your query.
          </div>
        )}
      </div>
    </div>
  );
}

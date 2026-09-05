"use client";

import React from "react";
import { Scenario, EvidenceNode } from "@/types";
import { ShieldCheck, Info } from "lucide-react";

interface ProvenanceGraphProps {
  scenario: Scenario;
  selectedEvidenceId?: string;
  onSelectEvidence: (evidence: EvidenceNode) => void;
}

export default function ProvenanceGraph({
  scenario,
  selectedEvidenceId,
  onSelectEvidence,
}: ProvenanceGraphProps) {
  const width = 880;
  const height = 500;

  const rootX = 440;
  const rootY = 60;

  const verifiedEvents = scenario.evidence_nodes || [];
  const decoyEvents = scenario.rejected_decoys || [];
  const allCandidateEvents = [...verifiedEvents, ...decoyEvents];

  const varDisplay =
    scenario.variance_inr < 0
      ? `-₹${Math.abs(scenario.variance_inr).toFixed(2)}`
      : `+₹${scenario.variance_inr.toFixed(2)}`;

  const eventY = 190;
  const numEvents = allCandidateEvents.length;
  const spacing = numEvents > 1 ? 560 / (numEvents - 1) : 0;
  const startX = numEvents > 1 ? 160 : 440;

  const verifierY = 320;
  const verifierX = 440;
  const isApproved = scenario.expected_outcome !== "ESCALATE";
  const verifierColor = isApproved ? "#2b59d1" : "#e11d48";

  const termY = 440;
  const termColor = isApproved ? "#059669" : "#e11d48";

  return (
    <div className="w-full bg-parchment rounded-3xl border border-ash p-6 relative overflow-hidden flex flex-col justify-between">
      {/* Graph Header & Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-ash/40 pb-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-mono text-smoke">Investigation Tree</span>
            <span className="px-2 py-0.5 rounded-pill bg-periwinkle-mist/60 border border-ash text-xs font-mono font-semibold text-off-black">
              {scenario.case_id} &bull; {scenario.scenario_id}
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-smoke">Variance Root</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
            <span className="text-smoke">Verified Proof</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span className="text-smoke">Decoy (Rejected)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-lake-blue" />
            <span className="text-smoke">5-Point Verifier</span>
          </div>
        </div>
      </div>

      {/* Interactive SVG Canvas */}
      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full min-w-[700px] h-auto select-none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <filter id="soft-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#000000" floodOpacity="0.08" />
            </filter>
          </defs>

          {/* ROOT NODE: Settlement Variance */}
          <g className="cursor-pointer">
            <rect
              x={rootX - 120}
              y={rootY - 30}
              width={240}
              height={60}
              rx={16}
              fill="#ffffff"
              stroke="#f59e0b"
              strokeWidth={2}
              filter="url(#soft-glow)"
            />
            <text
              x={rootX}
              y={rootY - 8}
              textAnchor="middle"
              fill="#797776"
              fontSize={10}
              fontWeight={600}
              fontFamily="var(--font-mono)"
              letterSpacing={1}
            >
              SETTLEMENT VARIANCE
            </text>
            <text
              x={rootX}
              y={rootY + 16}
              textAnchor="middle"
              fill="#242424"
              fontSize={16}
              fontWeight={700}
              fontFamily="var(--font-mono)"
            >
              {varDisplay}
            </text>
          </g>

          {/* Connectors: Root -> Candidate Events */}
          {allCandidateEvents.map((ev, idx) => {
            const evX = numEvents > 1 ? startX + idx * spacing : 440;
            const isRejected = ev.status === "REJECTED";
            const strokeColor = isRejected ? "#f87171" : "#10b981";
            const strokeDash = isRejected ? "5,5" : "none";

            return (
              <line
                key={`line-root-${idx}`}
                x1={rootX}
                y1={rootY + 30}
                x2={evX}
                y2={eventY - 30}
                stroke={strokeColor}
                strokeWidth={2}
                strokeDasharray={strokeDash}
                opacity={0.8}
              />
            );
          })}

          {/* Candidate Event Nodes */}
          {allCandidateEvents.map((ev, idx) => {
            const evX = numEvents > 1 ? startX + idx * spacing : 440;
            const isRejected = ev.status === "REJECTED";
            const strokeColor = isRejected ? "#ef4444" : "#10b981";
            const isSelected = ev.evidence_id === selectedEvidenceId;
            const amountText =
              ev.amount_inr < 0
                ? `-₹${Math.abs(ev.amount_inr).toFixed(2)}`
                : `₹${ev.amount_inr.toFixed(2)}`;

            return (
              <g
                key={`node-${ev.evidence_id}-${idx}`}
                className="cursor-pointer transition-transform hover:opacity-90"
                onClick={() => onSelectEvidence(ev)}
              >
                <rect
                  x={evX - 95}
                  y={eventY - 30}
                  width={190}
                  height={60}
                  rx={14}
                  fill="#ffffff"
                  stroke={strokeColor}
                  strokeWidth={isSelected ? 3 : 2}
                  strokeDasharray={isRejected ? "5,5" : "none"}
                  filter="url(#soft-glow)"
                />
                <text
                  x={evX}
                  y={eventY - 10}
                  textAnchor="middle"
                  fill={isRejected ? "#dc2626" : "#059669"}
                  fontSize={10}
                  fontWeight={700}
                  fontFamily="var(--font-mono)"
                >
                  {isRejected ? "✗ DECOY REJECTED" : `✓ ${ev.entity_type}`}
                </text>
                <text
                  x={evX}
                  y={eventY + 11}
                  textAnchor="middle"
                  fill="#242424"
                  fontSize={13}
                  fontWeight={700}
                  fontFamily="var(--font-mono)"
                >
                  {amountText}
                </text>
                <text
                  x={evX}
                  y={eventY + 23}
                  textAnchor="middle"
                  fill="#797776"
                  fontSize={9}
                  fontFamily="var(--font-mono)"
                >
                  {ev.evidence_id} &bull; {ev.evidence_level}
                </text>
              </g>
            );
          })}

          {/* Connectors: Verified Events -> Deterministic Verifier */}
          {allCandidateEvents.map((ev, idx) => {
            const evX = numEvents > 1 ? startX + idx * spacing : 440;
            const isRejected = ev.status === "REJECTED";
            if (isRejected) return null;

            return (
              <line
                key={`line-verif-${idx}`}
                x1={evX}
                y1={eventY + 30}
                x2={verifierX}
                y2={verifierY - 25}
                stroke="#2b59d1"
                strokeWidth={2}
                opacity={0.8}
              />
            );
          })}

          {/* DETERMINISTIC VERIFIER CONSTRAINT NODE */}
          <g className="cursor-pointer">
            <rect
              x={verifierX - 150}
              y={verifierY - 25}
              width={300}
              height={50}
              rx={14}
              fill="#ffffff"
              stroke={verifierColor}
              strokeWidth={2}
              filter="url(#soft-glow)"
            />
            <text
              x={verifierX}
              y={verifierY - 5}
              textAnchor="middle"
              fill={verifierColor}
              fontSize={10}
              fontWeight={700}
              fontFamily="var(--font-mono)"
              letterSpacing={1}
            >
              5-POINT DETERMINISTIC VERIFIER
            </text>
            <text
              x={verifierX}
              y={verifierY + 14}
              textAnchor="middle"
              fill="#4e4d4d"
              fontSize={11}
              fontWeight={600}
              fontFamily="var(--font-mono)"
            >
              Mathematical & Relational Proof Evaluated
            </text>
          </g>

          {/* Connector: Verifier -> Terminal Node */}
          <line
            x1={verifierX}
            y1={verifierY + 25}
            x2={verifierX}
            y2={termY - 25}
            stroke={termColor}
            strokeWidth={2}
            opacity={0.85}
          />

          {/* TERMINAL OUTCOME NODE */}
          <g>
            <rect
              x={verifierX - 130}
              y={termY - 25}
              width={260}
              height={50}
              rx={25}
              fill="#242424"
              stroke={termColor}
              strokeWidth={2}
              filter="url(#soft-glow)"
            />
            <text
              x={verifierX}
              y={termY - 6}
              textAnchor="middle"
              fill="#cecac8"
              fontSize={9}
              fontWeight={700}
              fontFamily="var(--font-mono)"
              letterSpacing={1}
            >
              TERMINAL DECISION
            </text>
            <text
              x={verifierX}
              y={termY + 14}
              textAnchor="middle"
              fill={isApproved ? "#34d399" : "#fb7185"}
              fontSize={13}
              fontWeight={700}
              fontFamily="var(--font-mono)"
            >
              {isApproved ? `✓ ${scenario.expected_outcome}` : "🚨 SAFE ESCALATE TO HUMAN"}
            </text>
          </g>
        </svg>
      </div>

      <div className="mt-4 pt-3 border-t border-ash/40 flex items-center justify-between text-[11px] font-mono text-smoke">
        <span className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-lake-blue" />
          Click any candidate node above to inspect its exact Excel/CSV row, sheet, and SHA-256 hash.
        </span>
        <span>
          Authority: <strong>Deterministic Financial Verifier</strong>
        </span>
      </div>
    </div>
  );
}

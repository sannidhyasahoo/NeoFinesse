"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import KPIGrid from "@/components/KPIGrid";
import DemoBanner from "@/components/DemoBanner";
import ProvenanceGraph from "@/components/ProvenanceGraph";
import EvidenceDrawer from "@/components/EvidenceDrawer";
import CaseTable from "@/components/CaseTable";
import AIvsVerifierCard from "@/components/AIvsVerifierCard";
import EscalationQueue from "@/components/EscalationQueue";
import PipelineDiagram from "@/components/PipelineDiagram";
import SourceEvidenceModal from "@/components/SourceEvidenceModal";
import HumanReviewDossierModal from "@/components/HumanReviewDossierModal";
import { benchmarkData } from "@/data/benchmarkData";
import { Scenario, EvidenceNode } from "@/types";
import {
  LayoutDashboard,
  FileSpreadsheet,
  Network,
  FileCheck,
  Scale,
  AlertOctagon,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export default function WorkspacePage() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [activeDemoId, setActiveDemoId] = useState<string>("demo_1");
  const [activeScenarioId, setActiveScenarioId] = useState<string>("VAR-001_REFUND_VARIANCE");
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceNode | null>(null);
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);
  const [modalEvidence, setModalEvidence] = useState<EvidenceNode | null>(null);
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [dossierScenario, setDossierScenario] = useState<Scenario | null>(null);

  const handleOpenSourceContext = (evidence: EvidenceNode) => {
    setModalEvidence(evidence);
    setIsSourceModalOpen(true);
  };

  const handleOpenReviewDossier = (scenarioToReview: Scenario) => {
    setDossierScenario(scenarioToReview);
    setIsDossierOpen(true);
  };

  const currentScenario =
    benchmarkData.scenarios.find((s) => s.scenario_id === activeScenarioId) ||
    benchmarkData.scenarios[0];

  // Set default selected evidence when scenario changes
  useEffect(() => {
    if (currentScenario.evidence_nodes && currentScenario.evidence_nodes.length > 0) {
      setSelectedEvidence(currentScenario.evidence_nodes[0]);
    } else if (currentScenario.rejected_decoys && currentScenario.rejected_decoys.length > 0) {
      setSelectedEvidence(currentScenario.rejected_decoys[0]);
    } else {
      setSelectedEvidence(null);
    }
  }, [activeScenarioId, currentScenario]);

  // Handle demo case selection
  const handleSelectDemo = (demoId: string) => {
    setActiveDemoId(demoId);
    const demo = benchmarkData.demo_cases.find((d) => d.demo_id === demoId);
    if (demo) {
      setActiveScenarioId(demo.scenario_id);
    }
  };

  // Handle inspection from Case Table
  const handleInspectScenario = (scenario: Scenario) => {
    setActiveScenarioId(scenario.scenario_id);
    setActiveTab("graph");
  };

  return (
    <div className="min-h-screen bg-parchment text-off-black flex flex-col selection:bg-periwinkle-mist relative overflow-hidden">
      {/* Editorial Nav */}
      <Navbar />

      <main className="flex-1 max-w-[1432px] mx-auto px-6 lg:px-12 py-8 space-y-8 w-full relative z-10">
        {/* Workspace Top Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-ash/50 pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs uppercase font-mono tracking-wider text-smoke font-medium">
                Live Investigation Workspace
              </span>
            </div>
            <h1 className="font-serif text-3xl sm:text-4xl text-off-black">
              Settlement Discrepancy Audit
            </h1>
          </div>

          {/* Action & Core Invariant Badges */}
          <div className="flex flex-wrap items-center gap-3 self-start md:self-auto">
            <Link
              href="/connect"
              className="px-4 py-2 rounded-pill bg-white hover:bg-off-black hover:text-white border border-ash text-xs font-mono uppercase tracking-wider transition-all flex items-center gap-1.5 shadow-sm"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-lake-blue" />
              <span>Ingest / Insert Files</span>
            </Link>

            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-pill bg-white border border-ash text-xs font-mono text-off-black shadow-sm">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>
                <strong>Core Invariant:</strong> AI investigates &bull; Tools retrieve &bull; Evidence constrains &bull; Deterministic verification decides
              </span>
            </div>
          </div>
        </div>

        {/* Active Demo Banner */}
        <DemoBanner
          demoCases={benchmarkData.demo_cases}
          activeDemoId={activeDemoId}
          onSelectDemo={handleSelectDemo}
        />

        {/* View Navigation Tabs */}
        <nav
          className="flex items-center gap-2 overflow-x-auto border-b border-ash/60 pb-2 scrollbar-none"
          aria-label="Workspace Views"
        >
          {[
            { id: "dashboard", label: "Overview", icon: <LayoutDashboard className="w-4 h-4" /> },
            { id: "cases", label: `All Cases (${benchmarkData.scenarios.length})`, icon: <FileSpreadsheet className="w-4 h-4" /> },
            { id: "graph", label: "Transaction Trace", icon: <Network className="w-4 h-4" /> },
            { id: "evidence", label: "Source File Evidence", icon: <FileCheck className="w-4 h-4" /> },
            { id: "comparator", label: "AI vs. Verifier", icon: <Scale className="w-4 h-4" /> },
            { id: "escalation", label: "Escalation Queue", icon: <AlertOctagon className="w-4 h-4" /> },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 rounded-pill text-xs font-mono uppercase tracking-wider transition-all flex items-center gap-2 whitespace-nowrap ${isActive
                  ? "bg-off-black text-parchment font-semibold shadow-sm"
                  : "bg-white/70 hover:bg-white text-graphite border border-ash/60"
                  }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* =====================================================================
            TAB 1: EXECUTIVE DASHBOARD
            ===================================================================== */}
        {activeTab === "dashboard" && (
          <div className="space-y-10 animate-fade-in">
            {/* KPI Cards */}
            <KPIGrid kpis={benchmarkData.kpis} />

            {/* End-to-End Architecture Flow */}
            <PipelineDiagram />

            {/* Benchmark Audit Table */}
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-ash/40 pb-4">
                <div>
                  <span className="text-xs uppercase font-mono text-lake-blue font-medium">
                    How the systems compare
                  </span>
                  <h2 className="font-serif text-2xl sm:text-3xl text-off-black">
                    Accuracy across three versions of the system
                  </h2>
                </div>
                <span className="px-3 py-1 rounded-pill bg-emerald-100 text-emerald-800 text-xs font-mono font-bold uppercase">
                  23 scenarios evaluated
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs font-mono">
                  <thead>
                    <tr className="bg-parchment/70 border-b border-ash text-[11px] uppercase tracking-wider text-smoke font-semibold">
                      <th className="py-3 px-4">System Tested</th>
                      <th className="py-3 px-4">Approach</th>
                      <th className="py-3 px-4">Correct Decisions</th>
                      <th className="py-3 px-4">Wrong Closures</th>
                      <th className="py-3 px-4">Needless Escalations</th>
                      <th className="py-3 px-4">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ash/40">
                    {benchmarkData.benchmarks.benchmarks_comparison.map((b, idx) => {
                      const isPrimary = b.name.includes("Phase 7 Controlled");
                      const readableName =
                        b.name.includes("Phase 5") ? "Rule-Based Baseline" :
                          b.name.includes("Phase 7 Controlled") ? "AI + Verification (this system)" :
                            b.name.includes("Phase 7") ? "Remote AI Only (no local verifier)" :
                              b.name;
                      const readableType =
                        b.type.includes("Rule-based") ? "Manual rules only, no AI" :
                          b.type.includes("Agentic") ? "AI investigation + mathematical verification" :
                            b.type.includes("Remote") ? "External AI model, no deterministic check" :
                              b.type;
                      const readableStatus =
                        b.status.includes("Frozen Baseline") ? "Baseline — superseded" :
                          b.status.includes("Primary Authority") ? "Current — verified" :
                            b.status.includes("Quota") ? "Partial audit (*8 infra failures)" :
                              b.status;
                      return (
                        <tr
                          key={idx}
                          className={isPrimary ? "bg-emerald-50/40 font-medium" : "hover:bg-parchment/30"}
                        >
                          <td className="py-3.5 px-4 font-bold text-off-black">{readableName}</td>
                          <td className="py-3.5 px-4 text-graphite">{readableType}</td>
                          <td className="py-3.5 px-4 font-bold text-lake-blue">{b.accuracy}</td>
                          <td className="py-3.5 px-4 font-bold text-emerald-700">{b.false_closure}</td>
                          <td className="py-3.5 px-4 text-graphite">{b.false_escalation}</td>
                          <td className="py-3.5 px-4">
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${isPrimary
                                ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                                : "bg-ash/30 text-graphite"
                                }`}
                            >
                              {readableStatus}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* =====================================================================
            TAB 2: VARIANCE CASES (23 SCENARIOS)
            ===================================================================== */}
        {activeTab === "cases" && (
          <div className="space-y-6 animate-fade-in">
            <CaseTable
              scenarios={benchmarkData.scenarios}
              onInspectScenario={handleInspectScenario}
            />
          </div>
        )}

        {/* =====================================================================
            TAB 3: FLAGSHIP PROVENANCE GRAPH & DRAWER
            ===================================================================== */}
        {activeTab === "graph" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start animate-fade-in">
            {/* Left Col: SVG Graph Canvas (8 cols) */}
            <div className="lg:col-span-8">
              <ProvenanceGraph
                scenario={currentScenario}
                selectedEvidenceId={selectedEvidence?.evidence_id}
                onSelectEvidence={(ev) => setSelectedEvidence(ev)}
              />
            </div>

            {/* Right Col: Evidence Drawer (4 cols) */}
            <div className="lg:col-span-4 sticky top-28">
              <EvidenceDrawer
                evidence={selectedEvidence}
                onViewSource={handleOpenSourceContext}
              />
            </div>
          </div>
        )}

        {/* =====================================================================
            TAB 4: CELL-LEVEL EVIDENCE INSPECTOR (FULL VIEW)
            ===================================================================== */}
        {activeTab === "evidence" && (
          <div className="space-y-6 animate-fade-in">
            <div className="bg-white rounded-card border border-ash p-8 sm:p-10 space-y-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-ash/40 pb-4">
                <div>
                  <span className="text-xs uppercase font-mono text-lake-blue font-medium">
                    Source File Grounding
                  </span>
                  <h2 className="font-serif text-2xl sm:text-3xl text-off-black">
                    Where every finding lives in the original file
                  </h2>
                </div>
                <span className="px-3 py-1 rounded-pill bg-periwinkle-mist/40 border border-ash text-xs font-mono text-off-black">
                  Cell-level traceability
                </span>
              </div>

              <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
                Every transaction identified by the system is pinned to its exact location in the uploaded file — sheet name, row number, and cell. A cryptographic hash ensures the record hasn't changed since it was read.
              </p>

              {/* Comprehensive Evidence Table across all scenarios */}
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs font-mono">
                  <thead>
                    <tr className="bg-parchment/70 border-b border-ash text-[11px] uppercase tracking-wider text-smoke font-semibold">
                      <th className="py-3 px-4">Evidence ID</th>
                      <th className="py-3 px-4">Case / Scenario</th>
                      <th className="py-3 px-4">Entity</th>
                      <th className="py-3 px-4">Relationship Path</th>
                      <th className="py-3 px-4">Source File</th>
                      <th className="py-3 px-4">Sheet & Cell</th>
                      <th className="py-3 px-4">SHA-256 Hash</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ash/40">
                    {benchmarkData.scenarios.slice(0, 10).map((s) => {
                      const allNodes = [...(s.evidence_nodes || []), ...(s.rejected_decoys || [])];
                      return allNodes.map((ev, evIdx) => {
                        const isRejected = ev.status === "REJECTED";
                        return (
                          <tr key={`${s.scenario_id}-${evIdx}`} className="hover:bg-parchment/30">
                            <td className="py-3 px-4 font-bold text-lake-blue">{ev.evidence_id}</td>
                            <td className="py-3 px-4 text-graphite text-[11px]">
                              {s.case_id} &bull; {s.scenario_id}
                            </td>
                            <td className="py-3 px-4 font-medium text-off-black">{ev.entity_type}</td>
                            <td className="py-3 px-4 text-[11px] text-graphite max-w-[220px] truncate">
                              {ev.relationship_path}
                            </td>
                            <td className="py-3 px-4 text-smoke">{ev.source_file}</td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-0.5 rounded bg-ash/20 text-off-black font-semibold text-[10px]">
                                {ev.sheet} : {ev.cell}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-smoke text-[10px] font-mono truncate max-w-[120px]">
                              {ev.record_hash}
                            </td>
                            <td className="py-3 px-4">
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${isRejected
                                  ? "bg-rose-100 text-rose-800"
                                  : "bg-emerald-100 text-emerald-800"
                                  }`}
                              >
                                {ev.status}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">
                              <button
                                onClick={() => handleOpenSourceContext(ev)}
                                className="px-3 py-1 bg-parchment hover:bg-off-black hover:text-white border border-ash rounded-pill text-[10px] font-bold uppercase tracking-wider transition-all shadow-sm"
                                title="Inspect cell and surrounding spreadsheet context"
                              >
                                View Source
                              </button>
                            </td>
                          </tr>
                        );
                      });
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* =====================================================================
            TAB 5: AI VS. VERIFIER SEPARATION
            ===================================================================== */}
        {activeTab === "comparator" && (
          <div className="space-y-6 animate-fade-in">
            <AIvsVerifierCard scenario={currentScenario} />
          </div>
        )}

        {/* =====================================================================
            TAB 6: ESCALATION & SAFETY QUEUE
            ===================================================================== */}
        {activeTab === "escalation" && (
          <div className="space-y-6 animate-fade-in">
            <EscalationQueue
              scenario={currentScenario}
              onViewSource={handleOpenSourceContext}
              onOpenReviewDossier={handleOpenReviewDossier}
              onSelectScenario={(scenId) => {
                setActiveScenarioId(scenId);
              }}
            />
          </div>
        )}
      </main>

      {/* Spreadsheet Cell-Level Source Evidence Modal */}
      <SourceEvidenceModal
        isOpen={isSourceModalOpen}
        onClose={() => setIsSourceModalOpen(false)}
        evidence={modalEvidence}
      />

      {/* Human Review Investigation Handoff Dossier Modal */}
      <HumanReviewDossierModal
        isOpen={isDossierOpen}
        onClose={() => setIsDossierOpen(false)}
        scenario={dossierScenario || currentScenario}
        onViewSource={handleOpenSourceContext}
      />

      <Footer />
    </div>
  );
}

"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import {
  UploadCloud,
  FileSpreadsheet,
  Database,
  Sparkles,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Layers,
  FileCheck,
  Zap,
} from "lucide-react";

export default function ConnectPage() {
  const router = useRouter();
  const [selectedSource, setSelectedSource] = useState<"synthetic" | "custom">("synthetic");
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([
    "settlement_batch_fy25_q3.csv (19 Batches, 1,420 Txns)",
    "refunds_and_reversals_fy25.csv (430 Refunds)",
    "bank_payout_feed_icici.xlsx (1,401 Credits)",
  ]);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleProceed = () => {
    setIsProcessing(true);
    setTimeout(() => {
      router.push("/workspace");
    }, 500);
  };

  return (
    <div className="min-h-screen bg-parchment text-off-black flex flex-col selection:bg-periwinkle-mist relative overflow-hidden">
      <Navbar />

      <main className="flex-1 max-w-[1432px] mx-auto px-6 lg:px-12 py-12 space-y-12 w-full relative z-10">
        {/* Step Progress Header */}
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-pill bg-periwinkle-mist/60 border border-ash text-xs font-mono text-off-black">
            <span className="text-emerald-700 font-bold">✓ Step 01: Auth</span>
            <span>&rarr;</span>
            <span className="font-bold text-lake-blue">Step 02: Ingest Data</span>
            <span>&rarr;</span>
            <span className="text-smoke">Step 03: Workspace</span>
          </div>
          <h1 className="font-serif text-4xl sm:text-5xl text-off-black">
            Connect Transaction Data
          </h1>
          <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
            Choose to upload your custom financial batch documents or load our pre-configured 23-scenario synthetic benchmark world for immediate audit and exploration.
          </p>
        </div>

        {/* Two Main Ingestion Choices */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch max-w-5xl mx-auto">
          {/* Choice A: Synthetic Benchmark (Recommended) */}
          <div
            onClick={() => setSelectedSource("synthetic")}
            className={`cursor-pointer rounded-card border p-8 sm:p-10 transition-all flex flex-col justify-between relative overflow-hidden ${
              selectedSource === "synthetic"
                ? "bg-white border-lake-blue ring-2 ring-lake-blue/20 shadow-md"
                : "bg-parchment/70 hover:bg-white border-ash"
            }`}
          >
            {/* Soft wash */}
            <div className="atmospheric-wash wash-sky-mint w-64 h-64 -top-10 -right-10 opacity-30" />

            <div className="space-y-6 relative z-10">
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-2xl bg-periwinkle-mist/50 border border-lake-blue/30 text-lake-blue flex items-center justify-center">
                  <Sparkles className="w-6 h-6" />
                </div>
                <span className="px-3 py-1 rounded-pill bg-emerald-100 text-emerald-800 text-[10px] font-mono font-bold uppercase tracking-wider">
                  Recommended &bull; Instant Load
                </span>
              </div>

              <div>
                <h3 className="font-serif text-2xl sm:text-3xl text-off-black">
                  Synthetic 23-Scenario Benchmark World
                </h3>
                <p className="text-xs sm:text-sm font-mono text-graphite mt-2 leading-relaxed">
                  Pre-configured financial world containing all 23 real-world multi-gateway variance edge cases: 1-to-1 refund deductions, same-amount decoy traps, multi-event compound splits, and delayed credits.
                </p>
              </div>

              {/* Feature bullet points */}
              <div className="space-y-2.5 pt-2 text-xs font-mono text-graphite">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>23 Comprehensive settlement variance scenarios</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>4 Curated interactive demo presets (VAR-001, VAR-002, VAR-004, VAR-008)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>L5 Cell coordinates & SHA-256 hashes pre-verified</span>
                </div>
              </div>
            </div>

            <div className="pt-8 border-t border-ash/40 mt-6 flex items-center justify-between text-xs font-mono">
              <span className="text-smoke">No file upload required</span>
              <span className="font-bold text-lake-blue flex items-center gap-1">
                Select Simulation {selectedSource === "synthetic" && "✓"}
              </span>
            </div>
          </div>

          {/* Choice B: Custom Upload & Connectors */}
          <div
            onClick={() => setSelectedSource("custom")}
            className={`cursor-pointer rounded-card border p-8 sm:p-10 transition-all flex flex-col justify-between relative overflow-hidden ${
              selectedSource === "custom"
                ? "bg-white border-lake-blue ring-2 ring-lake-blue/20 shadow-md"
                : "bg-parchment/70 hover:bg-white border-ash"
            }`}
          >
            <div className="space-y-6 relative z-10">
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-2xl bg-ash/20 border border-ash text-off-black flex items-center justify-center">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <span className="px-3 py-1 rounded-pill bg-ash/30 text-graphite text-[10px] font-mono font-medium uppercase tracking-wider">
                  Live Custom Batch Ingestion
                </span>
              </div>

              <div>
                <h3 className="font-serif text-2xl sm:text-3xl text-off-black">
                  Upload CSV / Excel Batch Files
                </h3>
                <p className="text-xs sm:text-sm font-mono text-graphite mt-2 leading-relaxed">
                  Drop multi-gateway settlement CSVs, refund logs, ICICI/HDFC bank statement feeds, or connect directly via Razorpay Settlement Webhooks.
                </p>
              </div>

              {/* Upload Dropzone Preview */}
              <div className="p-4 bg-parchment rounded-2xl border-2 border-dashed border-ash text-center space-y-2">
                <div className="text-xs font-mono text-smoke">
                  Drag & drop batch files or click to browse
                </div>
                <div className="text-[10px] font-mono text-smoke">
                  Supports: .csv, .xlsx, .json (Max 100MB)
                </div>
              </div>

              {/* Sample Files Loaded */}
              <div className="space-y-1.5 text-xs font-mono">
                <div className="text-[10px] uppercase font-mono text-smoke font-semibold">
                  Detected Source Documents:
                </div>
                {uploadedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="p-2 bg-ash/10 rounded-xl flex items-center gap-2 text-off-black text-[11px]"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5 text-lake-blue shrink-0" />
                    <span className="truncate">{file}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-8 border-t border-ash/40 mt-6 flex items-center justify-between text-xs font-mono">
              <span className="text-smoke">3 Documents ready to parse</span>
              <span className="font-bold text-lake-blue flex items-center gap-1">
                Select Custom Upload {selectedSource === "custom" && "✓"}
              </span>
            </div>
          </div>
        </div>

        {/* Bottom Navigation & Confirmation Action */}
        <div className="max-w-5xl mx-auto bg-white rounded-3xl border border-ash p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-sm">
          <div className="space-y-1">
            <div className="text-xs uppercase font-mono text-smoke font-semibold">
              Selected Ingestion Mode:
            </div>
            <div className="font-serif text-xl sm:text-2xl text-off-black">
              {selectedSource === "synthetic"
                ? "Synthetic 23-Scenario Benchmark World"
                : "Custom Document Batch Stream (3 Files Attached)"}
            </div>
            <div className="text-xs font-mono text-graphite">
              All records will be indexed with L5 cell coordinates and SHA-256 provenance hashes.
            </div>
          </div>

          <button
            onClick={handleProceed}
            disabled={isProcessing}
            className="w-full sm:w-auto px-8 py-3.5 text-xs uppercase tracking-wider font-mono text-white bg-lake-blue rounded-btn hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-sm font-semibold shrink-0"
          >
            {isProcessing ? "Loading Workspace..." : "Proceed to Analysis Workspace"} <span>▸</span>
          </button>
        </div>
      </main>

      <Footer />
    </div>
  );
}

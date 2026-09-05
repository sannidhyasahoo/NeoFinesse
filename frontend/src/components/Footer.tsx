import React from "react";
import Link from "next/link";
import { Shield, FileCheck, ArrowUpRight } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full bg-parchment border-t border-ash/60 pt-16 pb-12 mt-20">
      <div className="max-w-[1432px] mx-auto px-6 lg:px-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          {/* Col 1: Brand & Thesis */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-off-black text-parchment flex items-center justify-center font-mono font-bold text-xs">
                NF
              </div>
              <span className="font-serif text-2xl text-off-black font-normal">
                NeoFinesse
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-lake-blue" />
            </div>
            <p className="text-sm text-graphite font-mono max-w-lg leading-relaxed">
              Evidence-constrained autonomous financial investigation engine. Multi-gateway settlement reconciliation, active tool retrieval, and deterministic verification guaranteeing 0.0% false closure rate.
            </p>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill bg-periwinkle-mist/40 border border-ash text-xs font-mono text-off-black">
              <Shield className="w-3.5 h-3.5 text-lake-blue" />
              <span>Razorpay AI Innovation Hackathon &bull; Phase 8 Verified</span>
            </div>
          </div>

          {/* Col 2: Navigation */}
          <div className="space-y-3">
            <div className="text-xs uppercase tracking-wider font-mono text-smoke font-medium">
              Architecture & Views
            </div>
            <ul className="space-y-2 text-xs font-mono text-graphite">
              <li>
                <Link href="/workspace?tab=dashboard" className="hover:text-lake-blue transition-colors">
                  Executive Dashboard
                </Link>
              </li>
              <li>
                <Link href="/workspace?tab=cases" className="hover:text-lake-blue transition-colors">
                  23 Variance Cases
                </Link>
              </li>
              <li>
                <Link href="/workspace?tab=graph" className="hover:text-lake-blue transition-colors">
                  Provenance Graph
                </Link>
              </li>
              <li>
                <Link href="/workspace?tab=evidence" className="hover:text-lake-blue transition-colors">
                  Cell Evidence Inspector
                </Link>
              </li>
              <li>
                <Link href="/workspace?tab=comparator" className="hover:text-lake-blue transition-colors">
                  AI vs. Verifier Separation
                </Link>
              </li>
              <li>
                <Link href="/workspace?tab=escalation" className="hover:text-lake-blue transition-colors">
                  Escalation & Safety Queue
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Research & Invariants */}
          <div className="space-y-3">
            <div className="text-xs uppercase tracking-wider font-mono text-smoke font-medium">
              Scientific Principles
            </div>
            <ul className="space-y-2 text-xs font-mono text-graphite">
              <li className="flex items-center gap-1.5">
                <FileCheck className="w-3 h-3 text-lake-blue" /> L5 Cell Coordinate Grounding
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck className="w-3 h-3 text-lake-blue" /> SHA-256 Record Traceability
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck className="w-3 h-3 text-lake-blue" /> 5-Point Constraint Proof
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck className="w-3 h-3 text-lake-blue" /> Zero Financial Loss Invariant
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Strip */}
        <div className="pt-8 border-t border-ash/40 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-smoke">
          <div>
            &copy; 2026 NeoFinesse. Autonomous Financial Intelligence & Audit Infrastructure.
          </div>
          <div className="flex items-center gap-6">
            <span className="text-graphite">
              <em>&ldquo;AI investigates. Evidence constrains. Deterministic verification decides.&rdquo;</em>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}

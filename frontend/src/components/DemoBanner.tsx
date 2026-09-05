"use client";

import React from "react";
import { DemoCase } from "@/types";
import { Sparkles, ArrowRight } from "lucide-react";

interface DemoBannerProps {
  demoCases: DemoCase[];
  activeDemoId: string;
  onSelectDemo: (demoId: string) => void;
}

export default function DemoBanner({
  demoCases,
  activeDemoId,
  onSelectDemo,
}: DemoBannerProps) {
  const current = demoCases.find((d) => d.demo_id === activeDemoId) || demoCases[0];

  return (
    <div className="w-full bg-periwinkle-mist/40 rounded-3xl border border-ash/80 p-6 relative overflow-hidden transition-all">
      {/* Soft gradient wash */}
      <div className="atmospheric-wash wash-coral-sky w-72 h-72 -top-20 -right-20 opacity-30" />

      <div className="relative z-10 space-y-4">
        {/* Preset Selector Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ash/40 pb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-lake-blue" />
            <span className="text-xs uppercase font-mono tracking-wider font-semibold text-off-black">
              Example Cases:
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {demoCases.map((demo) => {
              const isActive = demo.demo_id === activeDemoId;
              return (
                <button
                  key={demo.demo_id}
                  onClick={() => onSelectDemo(demo.demo_id)}
                  className={`px-3.5 py-1.5 rounded-pill text-xs font-mono transition-all uppercase tracking-wider ${isActive
                    ? "bg-off-black text-parchment font-semibold shadow-sm"
                    : "bg-white/80 hover:bg-white text-graphite border border-ash/60"
                    }`}
                >
                  {demo.title.split(":")[0]}: {demo.subtitle.split("(")[0]}
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Demo Explanation */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1 max-w-3xl">
            <div className="flex items-center gap-3">
              <h3 className="font-serif text-xl sm:text-2xl text-off-black">
                {current.title} &mdash; <span className="text-graphite font-serif">{current.subtitle}</span>
              </h3>
            </div>
            <p className="text-xs sm:text-sm font-mono text-graphite leading-relaxed">
              {current.core_lesson}
            </p>
          </div>

          <div className="shrink-0 flex items-center gap-3">
            <div className="px-4 py-2 bg-white rounded-2xl border border-ash text-right">
              <div className="text-[10px] uppercase font-mono text-smoke">
                {current.case_id} &bull; Discrepancy
              </div>
              <div className="text-base font-mono font-bold text-lake-blue">
                {current.variance_display}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

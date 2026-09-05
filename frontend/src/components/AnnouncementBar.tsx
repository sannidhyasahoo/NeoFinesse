"use client";

import React, { useState } from "react";
import Link from "next/link";
import { X, ArrowRight } from "lucide-react";

export default function AnnouncementBar() {
  const [isOpen, setIsOpen] = useState(true);

  if (!isOpen) return null;

  return (
    <aside aria-label="Platform Announcement" className="w-full bg-ink text-parchment text-xs font-mono py-2.5 px-4 sm:px-6 relative z-50 flex items-center justify-between border-b border-ash/20">
      <div className="max-w-[1432px] mx-auto w-full flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          <span className="inline-block w-2 h-2 rounded-full bg-mint animate-pulse" />
          <span className="tracking-tight text-white/90">
            <strong>VERIFIED ACCURACY:</strong> Zero incorrect closures across all 23 settlement mismatch scenarios — every decision is mathematically proven.
          </span>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Link
            href="/workspace"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 text-[11px] uppercase tracking-wider text-white border border-white/30 rounded-pill hover:bg-white/10 transition-colors"
          >
            See the Results <ArrowRight className="w-3 h-3" />
          </Link>
          <button
            onClick={() => setIsOpen(false)}
            aria-label="Close notification"
            className="text-white/60 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}

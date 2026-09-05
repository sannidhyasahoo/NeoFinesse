"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ShieldCheck, Menu, X, ArrowUpRight } from "lucide-react";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="w-full bg-parchment/90 backdrop-blur-md sticky top-0 z-40 border-b border-ash/40">
      <div className="max-w-[1432px] mx-auto px-6 lg:px-12 h-20 flex items-center justify-between">
        {/* Brand Lockup */}
        <Link href="/" className="flex items-center gap-3 group">
          <img src="/logo.svg" alt="NeoFinesse Logo" className="w-9 h-9 group-hover:scale-105 transition-transform" />
          <div className="flex items-center gap-2">
            <span className="font-serif text-2xl text-off-black tracking-tight font-normal">
              NeoFinesse
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-lake-blue" />
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-xs uppercase tracking-wider text-graphite font-mono">
          <Link href="/#methodology" className="hover:text-off-black transition-colors">
            How It Works
          </Link>
          <Link href="/#architecture" className="hover:text-off-black transition-colors">
            The Process
          </Link>
          <Link href="/#benchmark" className="hover:text-off-black transition-colors">
            Results
          </Link>
          <Link href="/#invariants" className="hover:text-off-black transition-colors">
            Capabilities
          </Link>
          <Link href="/workspace" className="hover:text-lake-blue text-off-black font-medium transition-colors flex items-center gap-1">
            Live Demo <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </nav>

        {/* CTA Buttons */}
        <div className="hidden sm:flex items-center gap-4">
          <Link
            href="/auth"
            className="px-6 py-2.5 text-xs uppercase tracking-wider font-mono text-off-black border border-off-black rounded-btn hover:bg-off-black hover:text-parchment transition-all"
          >
            Sign In
          </Link>
          <Link
            href="/connect"
            className="px-7 py-2.5 text-xs uppercase tracking-wider font-mono text-white bg-lake-blue rounded-btn hover:bg-blue-700 transition-all flex items-center gap-2 shadow-sm"
          >
            Start Audit <span>▸</span>
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 text-off-black"
          aria-label="Toggle Navigation Menu"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-parchment border-b border-ash px-6 py-6 space-y-4">
          <nav className="flex flex-col gap-4 text-sm font-mono uppercase tracking-wider text-graphite">
            <Link
              href="/#methodology"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-off-black"
            >
              How It Works
            </Link>
            <Link
              href="/#architecture"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-off-black"
            >
              The Process
            </Link>
            <Link
              href="/#benchmark"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-off-black"
            >
              Results
            </Link>
            <Link
              href="/#invariants"
              onClick={() => setMobileMenuOpen(false)}
              className="hover:text-off-black"
            >
              Capabilities
            </Link>
            <Link
              href="/workspace"
              onClick={() => setMobileMenuOpen(false)}
              className="text-lake-blue font-bold"
            >
              Live Demo →
            </Link>
          </nav>
          <div className="pt-4 border-t border-ash/40 flex flex-col gap-3">
            <Link
              href="/auth"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full text-center py-2.5 text-xs uppercase tracking-wider font-mono text-off-black border border-off-black rounded-btn"
            >
              Sign In
            </Link>
            <Link
              href="/connect"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full text-center py-2.5 text-xs uppercase tracking-wider font-mono text-white bg-lake-blue rounded-btn"
            >
              Start Audit ▸
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

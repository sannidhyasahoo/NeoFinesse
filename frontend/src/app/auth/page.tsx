"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { ShieldCheck, ArrowRight, Lock, Building, Mail, KeyRound, Check } from "lucide-react";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("ops.finance@enterprise-merchant.com");
  const [password, setPassword] = useState("••••••••••••");
  const [merchantId, setMerchantId] = useState("merch_rzp_live_9984");
  const [gateway, setGateway] = useState("razorpay");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      router.push("/connect");
    }, 600);
  };

  return (
    <div className="min-h-screen bg-parchment text-off-black flex flex-col selection:bg-periwinkle-mist relative overflow-hidden">
      <Navbar />

      <main className="flex-1 max-w-[1432px] mx-auto px-6 lg:px-12 py-12 flex items-center justify-center relative z-10 w-full">
        {/* Background atmospheric gradient wash */}
        <div className="atmospheric-wash wash-coral-sky w-[450px] h-[450px] -top-20 left-1/4 opacity-30" />
        <div className="atmospheric-wash wash-sky-mint w-[400px] h-[400px] -bottom-20 right-1/4 opacity-30" />

        <div className="w-full max-w-lg bg-white rounded-card border border-ash p-8 sm:p-12 space-y-8 shadow-sm relative z-10">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-pill bg-periwinkle-mist/50 border border-ash text-xs font-mono text-off-black mb-1">
              <Lock className="w-3.5 h-3.5 text-lake-blue" />
              <span>Step 01 &bull; Financial Access Control</span>
            </div>
            <h1 className="font-serif text-3xl sm:text-4xl text-off-black">
              {mode === "signin" ? "Sign In to NeoFinesse" : "Register Financial Workspace"}
            </h1>
            <p className="text-xs font-mono text-graphite">
              Autonomous, evidence-constrained reconciliation & audit platform.
            </p>
          </div>

          {/* Mode Pill Switcher */}
          <div className="grid grid-cols-2 p-1 bg-parchment rounded-pill border border-ash/70 text-xs font-mono">
            <button
              type="button"
              onClick={() => setMode("signin")}
              className={`py-2 rounded-pill uppercase tracking-wider transition-all font-medium ${
                mode === "signin"
                  ? "bg-off-black text-parchment shadow-sm"
                  : "text-smoke hover:text-off-black"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setMode("signup")}
              className={`py-2 rounded-pill uppercase tracking-wider transition-all font-medium ${
                mode === "signup"
                  ? "bg-off-black text-parchment shadow-sm"
                  : "text-smoke hover:text-off-black"
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
            {/* Email */}
            <div>
              <label className="block uppercase text-smoke tracking-wider text-[10px] mb-1 font-semibold">
                Organization Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-smoke absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-parchment border border-ash rounded-xl pl-10 pr-4 py-2.5 text-off-black focus:outline-none focus:border-lake-blue focus:ring-1 focus:ring-lake-blue text-xs font-mono"
                  placeholder="finance@company.com"
                />
              </div>
            </div>

            {/* Merchant ID */}
            <div>
              <label className="block uppercase text-smoke tracking-wider text-[10px] mb-1 font-semibold">
                Merchant / Entity ID
              </label>
              <div className="relative">
                <Building className="w-4 h-4 text-smoke absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={merchantId}
                  onChange={(e) => setMerchantId(e.target.value)}
                  className="w-full bg-parchment border border-ash rounded-xl pl-10 pr-4 py-2.5 text-off-black focus:outline-none focus:border-lake-blue focus:ring-1 focus:ring-lake-blue text-xs font-mono"
                  placeholder="merch_12345"
                />
              </div>
            </div>

            {/* Primary Payment Gateway */}
            <div>
              <label className="block uppercase text-smoke tracking-wider text-[10px] mb-1 font-semibold">
                Primary Payment Provider
              </label>
              <select
                value={gateway}
                onChange={(e) => setGateway(e.target.value)}
                className="w-full bg-parchment border border-ash rounded-xl px-4 py-2.5 text-off-black focus:outline-none focus:border-lake-blue focus:ring-1 focus:ring-lake-blue text-xs font-mono appearance-none"
              >
                <option value="razorpay">Razorpay Payouts & Subscriptions</option>
                <option value="icici">ICICI Corporate Bank H2H</option>
                <option value="hdfc">HDFC Bank Direct Statements</option>
                <option value="cashfree">Cashfree Auto-Collect</option>
                <option value="stripe">Stripe Connect & Payouts</option>
                <option value="all">Multi-Gateway Consolidated World</option>
              </select>
            </div>

            {/* Password */}
            <div>
              <label className="block uppercase text-smoke tracking-wider text-[10px] mb-1 font-semibold">
                Security Password
              </label>
              <div className="relative">
                <KeyRound className="w-4 h-4 text-smoke absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-parchment border border-ash rounded-xl pl-10 pr-4 py-2.5 text-off-black focus:outline-none focus:border-lake-blue focus:ring-1 focus:ring-lake-blue text-xs font-mono"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-3">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 text-xs uppercase tracking-wider font-mono text-white bg-lake-blue rounded-btn hover:bg-blue-700 transition-all flex items-center justify-center gap-2 shadow-sm font-semibold"
              >
                {loading ? "Authenticating..." : "Continue to Ingestion"} <span>▸</span>
              </button>
            </div>
          </form>

          {/* Bottom helper note */}
          <div className="pt-4 border-t border-ash/40 flex items-center justify-between text-[11px] font-mono text-smoke">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> SOC2 Type II Certified
            </span>
            <span>256-Bit TLS In-Transit</span>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

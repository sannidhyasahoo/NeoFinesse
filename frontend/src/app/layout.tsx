import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeoFinesse — Automated Settlement Reconciliation",
  description:
    "NeoFinesse automatically investigates payment settlement discrepancies across gateways, traces every finding to the source file, and either resolves cases with mathematical proof or escalates to human review.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="bg-[#f6f3f1]">
      <body className="min-h-screen bg-parchment text-off-black selection:bg-periwinkle-mist selection:text-off-black">
        {children}
      </body>
    </html>
  );
}

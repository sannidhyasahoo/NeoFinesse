import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeoFinesse — Evidence-Constrained AI Financial Investigation",
  description:
    "NeoFinesse traces settlement variances across payments, refunds, disputes, UPI events, and bank transactions using active evidence retrieval and deterministic constraint verification.",
  icons: {
    icon: "/favicon.ico",
  },
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

import { NextResponse } from "next/server";
import { benchmarkData } from "@/data/benchmarkData";

export async function GET() {
  return NextResponse.json({
    status: "SUCCESS",
    message: "Dataset generation service ready",
    files_available: [
      { name: "settlements.csv", type: "CSV", description: "Multi-gateway settlement batch records" },
      { name: "settlement_lines.csv", type: "CSV", description: "Itemized deductions, MDR fees, and transaction links" },
      { name: "payments.csv", type: "CSV", description: "Captured customer payments with order references" },
      { name: "orders.csv", type: "CSV", description: "Merchant order master items" },
      { name: "refunds.csv", type: "CSV", description: "Customer refunds and reversals with cut-off timestamps" },
      { name: "disputes.csv", type: "CSV", description: "Chargeback disputes and evidence deadlines" },
      { name: "adjustments.csv", type: "CSV", description: "MDR fee adjustments and penalty debits" },
      { name: "bank_transactions.csv", type: "CSV", description: "Bank credit entries with UTR numbers" },
      { name: "upi_transactions.csv", type: "CSV", description: "UPI payment switch transaction lifecycles" },
      { name: "upi_events.csv", type: "CSV", description: "NPCI raw event status transitions" },
      { name: "settlement_recon.xlsx", type: "XLSX", description: "Multi-tab Excel workbook with cell coordinates" },
      { name: "bank_statement.xlsx", type: "XLSX", description: "Bank account statement with UTR matching" },
      { name: "source_registry.json", type: "JSON", description: "Cryptographic SHA-256 file registry" },
    ],
    zip_download_url: "/data/neofinesse_demo_dataset.zip",
    total_scenarios: benchmarkData.scenarios.length,
    kpis: benchmarkData.kpis,
  });
}

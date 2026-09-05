import { NextResponse } from "next/server";
import { benchmarkData } from "@/data/benchmarkData";

export async function GET() {
  return NextResponse.json(benchmarkData);
}

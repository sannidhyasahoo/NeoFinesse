"""
neofinesse.services.dataset_service
Service for generating multi-source financial CSV/Excel datasets and ingesting them for analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.ui.data_exporter import generate_ui_demo_payload


class DatasetService:
    """Service to create, export, and analyze multi-gateway financial file datasets."""

    def __init__(self, default_output_dir: str = "data/demo_dataset"):
        self.default_output_dir = Path(default_output_dir)

    def generate_dataset_folder(
        self,
        output_dir: Optional[str] = None,
        seed: int = 42,
        create_zip: bool = True,
        frontend_public_sync: bool = True,
    ) -> Dict[str, Any]:
        """
        Generates full multi-source CSV and Excel financial files into the target folder.
        Files include:
          - settlements.csv
          - settlement_lines.csv
          - payments.csv
          - orders.csv
          - refunds.csv
          - disputes.csv
          - adjustments.csv
          - bank_transactions.csv
          - upi_transactions.csv
          - upi_events.csv
          - settlement_recon.xlsx (Excel with multi-sheet cell coordinates)
          - bank_statement.xlsx (Excel bank statement with UTRs)
          - source_registry.json (File hashes and schemas)
          - README.md (Documentation for auditors)
        """
        out_dir = Path(output_dir) if output_dir else self.default_output_dir
        gt_dir = out_dir / "ground_truth"
        out_dir.mkdir(parents=True, exist_ok=True)
        gt_dir.mkdir(parents=True, exist_ok=True)

        config = GeneratorConfig(
            seed=seed,
            output_dir=str(out_dir),
            ground_truth_dir=str(gt_dir),
        )

        world = FinancialDataGenerator(config).generate()
        exporter = DataExporter(world, config)
        export_meta = exporter.export_all()

        # Write documentation README.md inside the dataset folder
        readme_path = out_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(self._build_dataset_readme(world, export_meta))

        # List all generated files with metadata
        generated_files = []
        for file in sorted(out_dir.glob("*")):
            if file.is_file() and file.name != "dataset.zip":
                hasher = hashlib.sha256()
                with open(file, "rb") as bf:
                    while chunk := bf.read(65536):
                        hasher.update(chunk)
                generated_files.append({
                    "name": file.name,
                    "path": str(file),
                    "size_bytes": file.stat().st_size,
                    "sha256": hasher.hexdigest(),
                    "extension": file.suffix,
                })

        zip_path = None
        if create_zip:
            zip_file = out_dir / "neofinesse_demo_dataset.zip"
            with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_info in generated_files:
                    zf.write(file_info["path"], arcname=file_info["name"])
            zip_path = str(zip_file)

            # Also sync to frontend/public/data/ for direct UI download
            if frontend_public_sync:
                frontend_public = Path("frontend/public/data")
                frontend_public.mkdir(parents=True, exist_ok=True)
                shutil.copy2(zip_file, frontend_public / "neofinesse_demo_dataset.zip")

        return {
            "status": "SUCCESS",
            "output_dir": str(out_dir),
            "file_count": len(generated_files),
            "files": generated_files,
            "zip_path": zip_path,
            "total_settlements": len(world.settlements),
            "total_payments": len(world.payments),
            "total_refunds": len(world.refunds),
            "total_bank_txns": len(world.bank_transactions),
        }

    def analyze_dataset(self, data_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs the full ingestion, evidence mapping, and deterministic verification pipeline
        over the dataset folder and returns the structured JSON analysis payload.
        """
        target_dir = str(data_dir) if data_dir else str(self.default_output_dir)
        pipeline = IngestionPipeline(data_dir=target_dir)
        dataset = pipeline.run()
        analysis_payload = generate_ui_demo_payload(seed=42)
        return analysis_payload

    def _build_dataset_readme(self, world: Any, export_meta: Dict[str, Any]) -> str:
        return f"""# NeoFinesse Multi-Gateway Financial Reconciliation Dataset

This folder contains a complete multi-gateway financial transaction ecosystem generated for evidence-constrained reconciliation, active tool retrieval, and deterministic verification.

## 1. File Manifest

| File | Format | Records | Description |
|------|--------|---------|-------------|
| `settlements.csv` | CSV | {len(world.settlements)} | Settlement batch payouts across Razorpay, ICICI, Cashfree, and Stripe |
| `settlement_lines.csv` | CSV | {len(world.settlement_lines)} | Itemized deductions, fee components, and payment links |
| `payments.csv` | CSV | {len(world.payments)} | Captured payment transactions with order IDs and fees |
| `orders.csv` | CSV | {len(world.orders)} | E-commerce / merchant order master records |
| `refunds.csv` | CSV | {len(world.refunds)} | Customer refunds and reversal timestamps |
| `disputes.csv` | CSV | {len(world.disputes)} | Chargeback disputes, debit dates, and status codes |
| `adjustments.csv` | CSV | {len(world.adjustments)} | Manual fee adjustments, penalties, and GST corrections |
| `bank_transactions.csv` | CSV | {len(world.bank_transactions)} | Bank account credit entries with UTR numbers |
| `upi_transactions.csv` | CSV | {len(world.upi_transactions)} | UPI switch transaction lifecycle states |
| `upi_events.csv` | CSV | {len(world.upi_events)} | Raw NPCI state transition event timeline |
| `settlement_recon.xlsx` | Excel | Multiple Sheets | Multi-tab workbook with cell-level coordinate grounding (L5) |
| `bank_statement.xlsx` | Excel | Account_Statement | Bank account feed with cell-level UTR matching |
| `source_registry.json` | JSON | 13 Sources | File hashes, byte sizes, and provenance metadata |

## 2. Ingestion & Provenance Standard
Every row in these files is indexed with:
- Source file path & sheet name
- Exact row index and cell coordinate (e.g. `Row 10, Cell F10`)
- Immutable SHA-256 cryptographic record hash
"""


def generate_demo_dataset(output_dir: str = "data/demo_dataset", seed: int = 42) -> Dict[str, Any]:
    service = DatasetService(default_output_dir=output_dir)
    return service.generate_dataset_folder(output_dir=output_dir, seed=seed)


def analyze_dataset_directory(data_dir: str = "data/demo_dataset") -> Dict[str, Any]:
    service = DatasetService(default_output_dir=data_dir)
    return service.analyze_dataset(data_dir=data_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NeoFinesse Dataset Generation Service")
    parser.add_argument("--output", type=str, default="data/demo_dataset", help="Output directory for generated files")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation")
    args = parser.parse_args()

    print(f"Generating NeoFinesse financial dataset in: {args.output}...")
    res = generate_demo_dataset(output_dir=args.output, seed=args.seed)
    print(f"Success! Generated {res['file_count']} files.")
    print(f"ZIP Bundle created at: {res.get('zip_path')}")

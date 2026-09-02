from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline


def main() -> None:
    print("=== NeoFinesse: AI Finance Controller ===")
    config = GeneratorConfig(seed=42)
    print(f"Generating synthetic financial world (seed={config.seed})...")
    world = FinancialDataGenerator(config).generate()
    print(f"Generated {len(world.orders)} orders, {len(world.payments)} payments, {len(world.settlement_lines)} settlement lines, {len(world.settlements)} settlements.")
    print(f"Injecting {len(world.ground_truths)} controlled failure scenarios...")

    exporter = DataExporter(world, config)
    res = exporter.export_all()
    print(f"Exported multi-source files to '{res['data_dir']}' and ground truth to '{res['ground_truth_path']}'.")

    print("\nRunning Ingestion Pipeline & Validation...")
    pipeline = IngestionPipeline(data_dir=res["data_dir"])
    dataset = pipeline.run()
    print(f"Ingested {len(dataset.payments)} payments, {len(dataset.settlement_lines)} settlement lines, {len(dataset.settlements)} settlements.")
    print(f"Validation errors: {len(dataset.validation_errors)}")
    print("[SUCCESS] Phase 2 Data Generation & Ingestion Engine ready.")


if __name__ == "__main__":
    main()

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import Provider, SourceType


class FileRegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(description="Unique source ID (e.g. SRC-PAYMENTS)")
    filename: str = Field(description="Name of the file")
    file_path: str = Field(description="Absolute or relative path to file")
    file_hash: str = Field(description="SHA-256 hash of entire file")
    file_size: int = Field(ge=0, description="File size in bytes")
    format: SourceType = Field(description="File format (CSV, XLSX)")
    provider: Provider = Field(description="Originating provider")
    record_count: int = Field(ge=0, description="Number of data rows")
    ingested_at: datetime = Field(description="Registration/ingestion timestamp")
    ingestion_status: str = Field(default="REGISTERED", description="Status of ingestion")


class SourceRegistry:
    """Manages discovery and integrity registration of source files."""

    def __init__(self, data_dir: str, provider: Provider = Provider.RAZORPAY):
        self.data_dir = Path(data_dir)
        self.provider = provider
        self.entries: Dict[str, FileRegistryEntry] = {}

    def compute_file_hash(self, filepath: Path) -> str:
        """Computes SHA-256 hash of an entire file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def discover_and_register_files(self) -> Dict[str, FileRegistryEntry]:
        """Discovers all CSV and XLSX files in data_dir and registers their hashes and metadata."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory {self.data_dir} does not exist.")

        self.entries.clear()

        # Iterate over files (ignoring subdirectories like ground_truth)
        for filepath in sorted(self.data_dir.iterdir()):
            if filepath.is_file() and filepath.suffix.lower() in [".csv", ".xlsx", ".xls"]:
                if filepath.name.startswith("source_registry"):
                    continue

                fmt = SourceType.XLSX if filepath.suffix.lower() == ".xlsx" else SourceType.CSV
                file_hash = self.compute_file_hash(filepath)
                file_size = filepath.stat().st_size

                # Count records (approximate or exact)
                record_count = 0
                if fmt == SourceType.CSV:
                    with open(filepath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        record_count = max(0, len(lines) - 1)

                entry = FileRegistryEntry(
                    source_id=f"SRC-{filepath.stem.upper()}",
                    filename=filepath.name,
                    file_path=str(filepath),
                    file_hash=file_hash,
                    file_size=file_size,
                    format=fmt,
                    provider=self.provider,
                    record_count=record_count,
                    ingested_at=datetime.now(),
                    ingestion_status="REGISTERED",
                )
                self.entries[filepath.name] = entry

        return self.entries

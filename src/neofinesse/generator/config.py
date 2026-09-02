from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.models.base import Provider


class GeneratorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: int = Field(default=42, description="Random seed for reproducibility")
    num_orders: int = Field(default=150, description="Number of baseline orders to generate")
    num_payments: int = Field(default=160, description="Number of baseline payments to generate")
    num_settlements: int = Field(default=10, description="Number of baseline settlement batches")
    num_refunds: int = Field(default=15, description="Number of baseline refunds")
    num_disputes: int = Field(default=8, description="Number of baseline disputes")
    num_adjustments: int = Field(default=8, description="Number of baseline adjustments")
    num_transfers: int = Field(default=4, description="Number of baseline transfers")
    start_date: datetime = Field(default=datetime(2026, 8, 1, 9, 0, 0), description="Simulation start datetime")
    days: int = Field(default=30, description="Simulation duration in days")
    provider: Provider = Field(default=Provider.RAZORPAY, description="Primary payment gateway provider")
    output_dir: str = Field(default="data", description="Output directory for generated datasets")
    ground_truth_dir: str = Field(default="ground_truth", description="Output directory for ground truth metadata")

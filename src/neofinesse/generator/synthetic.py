from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.scenarios import ScenarioInjector
from neofinesse.models.base import (
    AdjustmentType,
    Currency,
    DisputePhase,
    DisputeStatus,
    FinalDeterminedStatus,
    FinancialEffectStatus,
    NormalizedObservedStatus,
    Provider,
    RefundSpeed,
    RefundStatus,
    ReversalStatus,
    SettlementReconStatus,
    SettlementStatus,
    SourceEventType,
)
from neofinesse.models.events import Adjustment, Dispute, Order, Payment, Refund, Transfer
from neofinesse.models.settlement import Settlement, SettlementLine
from neofinesse.models.upi import UPIEvent, UPITransaction
from neofinesse.models.bank import BankTransaction
from neofinesse.models.ground_truth import CaseGroundTruth


class SyntheticWorld(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    orders: List[Order] = Field(default_factory=list)
    payments: List[Payment] = Field(default_factory=list)
    upi_transactions: List[UPITransaction] = Field(default_factory=list)
    upi_events: List[UPIEvent] = Field(default_factory=list)
    refunds: List[Refund] = Field(default_factory=list)
    disputes: List[Dispute] = Field(default_factory=list)
    adjustments: List[Adjustment] = Field(default_factory=list)
    transfers: List[Transfer] = Field(default_factory=list)
    settlement_lines: List[SettlementLine] = Field(default_factory=list)
    settlements: List[Settlement] = Field(default_factory=list)
    bank_transactions: List[BankTransaction] = Field(default_factory=list)
    ground_truths: List[CaseGroundTruth] = Field(default_factory=list)


class FinancialDataGenerator:
    """Generates a complete, internally consistent synthetic financial world with ground truth."""

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.rng = random.Random(config.seed)
        self.injector = ScenarioInjector(self.rng, config.provider)

    def generate(self) -> SyntheticWorld:
        """Generates baseline financial records and injects failure scenarios."""
        world = SyntheticWorld()

        orders: List[Order] = []
        payments: List[Payment] = []
        upi_txns: List[UPITransaction] = []
        upi_events: List[UPIEvent] = []
        refunds: List[Refund] = []
        disputes: List[Dispute] = []
        adjustments: List[Adjustment] = []
        transfers: List[Transfer] = []
        settlement_lines: List[SettlementLine] = []
        settlements: List[Settlement] = []
        bank_txns: List[BankTransaction] = []

        banks = ["HDFC", "ICIC", "SBIN", "UTIB", "KKBK", "PUNB"]
        vpa_handles = ["okaxis", "okhdfcbank", "oksbi", "paytm", "apl"]

        # 1. Generate baseline Orders and Payments
        current_time = self.config.start_date
        time_step = timedelta(minutes=(self.config.days * 24 * 60) // max(self.config.num_orders, 1))

        for i in range(1, self.config.num_orders + 1):
            order_id = f"order_base_{i:04d}"
            # Amount in paise: between ₹100 (10,000 paise) and ₹25,000 (2,500,000 paise)
            order_amount = self.rng.randint(100, 25000) * 100
            order_time = current_time + (i * time_step)

            orders.append(
                Order(
                    id=order_id,
                    amount=order_amount,
                    status="paid",
                    created_at=order_time,
                )
            )

            # Generate Payment for this order
            pay_id = f"pay_base_{i:04d}"
            method_choice = self.rng.random()
            if method_choice < 0.70:
                method = "upi"
            elif method_choice < 0.90:
                method = "card"
            else:
                method = "netbanking"

            # 92% successful/captured, 8% failed
            is_success = self.rng.random() < 0.92
            status_str = "captured" if is_success else "failed"
            norm_status = NormalizedObservedStatus.CAPTURED if is_success else NormalizedObservedStatus.FAILED

            fee = (order_amount * 2) // 100 if is_success else 0  # 2% fee
            tax = (fee * 18) // 100 if is_success else 0          # 18% GST
            net_amount = order_amount - fee - tax if is_success else 0

            bank_code = self.rng.choice(banks)
            vpa = f"user_{i:03d}@{self.rng.choice(vpa_handles)}" if method == "upi" else None
            rrn = f"{self.rng.randint(100000000000, 999999999999)}" if method == "upi" else None

            pay_time = order_time + timedelta(seconds=self.rng.randint(30, 300))
            captured_time = pay_time + timedelta(seconds=self.rng.randint(5, 60)) if is_success else None

            payment = Payment(
                id=pay_id,
                amount=order_amount,
                status=status_str,
                normalized_status=norm_status,
                order_id=order_id,
                method=method,
                bank=bank_code,
                vpa=vpa,
                fee=fee,
                tax=tax,
                net_amount=net_amount,
                acquirer_data={"rrn": rrn} if rrn else None,
                created_at=pay_time,
                captured_at=captured_time,
                settled=False,  # will be set to True when assigned to settlement
                provider=self.config.provider,
            )
            payments.append(payment)

            # Generate UPI transaction & events if UPI
            if method == "upi":
                upi_id = f"upi_base_{i:04d}"
                upi_txn = UPITransaction(
                    upi_transaction_id=upi_id,
                    payment_id=pay_id,
                    order_id=order_id,
                    rrn=rrn,
                    amount=order_amount,
                    vpa=vpa,
                    initiated_at=pay_time,
                    current_observed_status=norm_status,
                    final_determined_status=FinalDeterminedStatus.SUCCESS if is_success else FinalDeterminedStatus.FAILED,
                    debit_observed=is_success,
                    reversal_status=ReversalStatus.NONE,
                    financial_effect_status=FinancialEffectStatus.DETERMINED,
                    financial_effect_amount=order_amount if is_success else 0,
                    provider=self.config.provider,
                )
                upi_txns.append(upi_txn)

                # Events
                upi_events.append(
                    UPIEvent(
                        event_id=f"upievt_base_{i:04d}_1",
                        upi_transaction_id=upi_id,
                        timestamp=pay_time,
                        previous_state=NormalizedObservedStatus.INITIATED,
                        new_state=NormalizedObservedStatus.PENDING,
                        event_type="UPI_INTENT_SENT",
                        amount=order_amount,
                        rrn=rrn,
                    )
                )
                upi_events.append(
                    UPIEvent(
                        event_id=f"upievt_base_{i:04d}_2",
                        upi_transaction_id=upi_id,
                        timestamp=captured_time or (pay_time + timedelta(seconds=45)),
                        previous_state=NormalizedObservedStatus.PENDING,
                        new_state=norm_status,
                        event_type="WEBHOOK_CAPTURED" if is_success else "WEBHOOK_FAILED",
                        amount=order_amount,
                        rrn=rrn,
                    )
                )

        # 2. Generate baseline Refunds on some captured payments
        captured_payments = [p for p in payments if p.normalized_status == NormalizedObservedStatus.CAPTURED]
        refund_candidates = self.rng.sample(captured_payments, min(self.config.num_refunds, len(captured_payments)))

        for r_idx, p in enumerate(refund_candidates, 1):
            rfnd_id = f"rfnd_base_{r_idx:04d}"
            # Refund partial or full amount
            rfnd_amount = p.amount if self.rng.random() < 0.5 else p.amount // 2
            rfnd_time = (p.captured_at or p.created_at) + timedelta(hours=self.rng.randint(2, 48))

            refunds.append(
                Refund(
                    id=rfnd_id,
                    amount=rfnd_amount,
                    payment_id=p.id,
                    status=RefundStatus.PROCESSED,
                    speed_requested=RefundSpeed.NORMAL,
                    speed_processed=RefundSpeed.NORMAL,
                    acquirer_data={"arn": f"{self.rng.randint(100000000000000, 999999999999999)}"},
                    created_at=rfnd_time,
                    processed_at=rfnd_time + timedelta(minutes=15),
                    provider=self.config.provider,
                )
            )

        # 3. Generate baseline Disputes on some captured payments
        dispute_candidates = self.rng.sample(
            [p for p in captured_payments if p not in refund_candidates],
            min(self.config.num_disputes, len(captured_payments) - len(refund_candidates)),
        )
        for d_idx, p in enumerate(dispute_candidates, 1):
            disp_id = f"disp_base_{d_idx:04d}"
            disp_time = (p.captured_at or p.created_at) + timedelta(days=self.rng.randint(1, 5))
            is_won = self.rng.random() < 0.3
            status = DisputeStatus.WON if is_won else DisputeStatus.LOST

            disputes.append(
                Dispute(
                    id=disp_id,
                    payment_id=p.id,
                    amount=p.amount,
                    amount_deducted=p.amount,
                    reason_code="FRAUDULENT_TRANSACTION",
                    status=status,
                    phase=DisputePhase.CHARGEBACK,
                    created_at=disp_time,
                    net_financial_effect=0 if is_won else -p.amount,
                    provider=self.config.provider,
                )
            )

        # 4. Generate baseline Adjustments
        for a_idx in range(1, self.config.num_adjustments + 1):
            adj_id = f"adj_base_{a_idx:04d}"
            adj_amount = self.rng.randint(50, 500) * 100  # ₹50 to ₹500
            is_credit = self.rng.random() < 0.4
            signed_amount = adj_amount if is_credit else -adj_amount
            adj_type = AdjustmentType.MANUAL_CREDIT if is_credit else AdjustmentType.RISK_HOLD
            adj_time = self.config.start_date + timedelta(days=self.rng.randint(1, self.config.days - 1))

            adjustments.append(
                Adjustment(
                    id=adj_id,
                    amount=signed_amount,
                    description="Routine reserve or manual adjustment",
                    adjustment_type=adj_type,
                    created_at=adj_time,
                    provider=self.config.provider,
                )
            )

        # 5. Generate baseline Transfers
        for t_idx in range(1, self.config.num_transfers + 1):
            trf_id = f"trf_base_{t_idx:04d}"
            trf_amount = self.rng.randint(100, 1000) * 100
            trf_time = self.config.start_date + timedelta(days=self.rng.randint(1, self.config.days - 1))

            transfers.append(
                Transfer(
                    id=trf_id,
                    amount=trf_amount,
                    recipient=f"acc_vendor_{t_idx:03d}",
                    created_at=trf_time,
                    provider=self.config.provider,
                )
            )

        # 6. Construct baseline Settlements and SettlementLines
        # Partition captured payments across settlements
        num_sets = self.config.num_settlements
        chunks = [[] for _ in range(num_sets)]
        for idx, p in enumerate(captured_payments):
            chunks[idx % num_sets].append(p)

        line_counter = 1
        for s_idx, batch_payments in enumerate(chunks, 1):
            setl_id = f"setl_base_{s_idx:04d}"
            setl_time = self.config.start_date + timedelta(days=(s_idx * (self.config.days // max(num_sets, 1))))
            utr = f"AXISCN{self.rng.randint(1000000000, 9999999999)}"

            batch_lines: List[SettlementLine] = []
            gross_total = 0
            fees_total = 0
            tax_total = 0
            refund_total = 0
            adjustment_total = 0
            dispute_total = 0
            transfer_total = 0

            # Add Payment lines
            for p in batch_payments:
                p.settled = True
                p.settlement_id = setl_id
                line_id = f"line_base_{line_counter:05d}"
                line_counter += 1

                gross_total += p.amount
                fees_total += p.fee
                tax_total += p.tax

                line = SettlementLine(
                    settlement_line_id=line_id,
                    settlement_id=setl_id,
                    source_event_id=p.id,
                    source_event_type=SourceEventType.PAYMENT,
                    payment_id=p.id,
                    amount=p.amount,
                    fee=p.fee,
                    tax=p.tax,
                    net_amount=p.net_amount,
                    event_timestamp=p.captured_at,
                    settlement_timestamp=setl_time,
                    provider=self.config.provider,
                )
                batch_lines.append(line)

            # Assign some refunds to this batch
            batch_refunds = [r for r in refunds if r.settlement_id is None and (r.processed_at or r.created_at) <= setl_time][:2]
            for r in batch_refunds:
                r.settlement_id = setl_id
                line_id = f"line_base_{line_counter:05d}"
                line_counter += 1
                refund_total += r.amount

                line = SettlementLine(
                    settlement_line_id=line_id,
                    settlement_id=setl_id,
                    source_event_id=r.id,
                    source_event_type=SourceEventType.REFUND,
                    payment_id=r.payment_id,
                    amount=r.amount,
                    fee=0,
                    tax=0,
                    net_amount=-r.amount,
                    event_timestamp=r.processed_at,
                    settlement_timestamp=setl_time,
                    provider=self.config.provider,
                )
                batch_lines.append(line)

            # Assign some adjustments to this batch
            batch_adjustments = [a for a in adjustments if a.settlement_id is None and a.created_at <= setl_time][:1]
            for a in batch_adjustments:
                a.settlement_id = setl_id
                line_id = f"line_base_{line_counter:05d}"
                line_counter += 1
                adjustment_total += a.amount

                line = SettlementLine(
                    settlement_line_id=line_id,
                    settlement_id=setl_id,
                    source_event_id=a.id,
                    source_event_type=SourceEventType.ADJUSTMENT,
                    amount=abs(a.amount),
                    fee=0,
                    tax=0,
                    net_amount=a.amount,
                    event_timestamp=a.created_at,
                    settlement_timestamp=setl_time,
                    provider=self.config.provider,
                )
                batch_lines.append(line)

            settlement_lines.extend(batch_lines)

            # Expected amount is strictly the sum of all SettlementLine.net_amount
            expected_amount = sum(l.net_amount for l in batch_lines)

            settlement = Settlement(
                id=setl_id,
                amount=expected_amount,  # In baseline, actual = expected
                status=SettlementStatus.PROCESSED,
                fees=fees_total,
                tax=tax_total,
                utr=utr,
                gross_amount=gross_total,
                refund_total=refund_total,
                adjustment_total=adjustment_total,
                dispute_total=dispute_total,
                transfer_total=transfer_total,
                expected_amount=expected_amount,
                variance=0,
                recon_status=SettlementReconStatus.MATCHED,
                created_at=setl_time,
                settled_at=setl_time + timedelta(hours=2),
                provider=self.config.provider,
            )
            settlements.append(settlement)

            # Generate matching Bank Transaction
            bank_txns.append(
                BankTransaction(
                    bank_txn_id=f"bank_base_{s_idx:04d}",
                    utr=utr,
                    credit_amount=expected_amount,
                    value_date=setl_time + timedelta(hours=4),
                    transaction_date=setl_time + timedelta(hours=4),
                    raw_description=f"CMS/NEFT/{utr}/RAZORPAY SETTLEMENT",
                    parsed_utr=utr,
                )
            )

        # 7. Inject 10 Controlled Failure Scenarios
        ground_truths = self.injector.inject_all_scenarios(
            self.config.start_date,
            orders,
            payments,
            upi_txns,
            upi_events,
            refunds,
            disputes,
            adjustments,
            settlement_lines,
            settlements,
            bank_txns,
        )

        world.orders = orders
        world.payments = payments
        world.upi_transactions = upi_txns
        world.upi_events = upi_events
        world.refunds = refunds
        world.disputes = disputes
        world.adjustments = adjustments
        world.transfers = transfers
        world.settlement_lines = settlement_lines
        world.settlements = settlements
        world.bank_transactions = bank_txns
        world.ground_truths = ground_truths

        return world

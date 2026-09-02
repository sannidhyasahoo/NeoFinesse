from datetime import datetime, timedelta
import random
from typing import List, Tuple, Dict, Any

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
from neofinesse.models.events import Adjustment, Dispute, Order, Payment, Refund
from neofinesse.models.settlement import Settlement, SettlementLine
from neofinesse.models.upi import UPIEvent, UPITransaction
from neofinesse.models.bank import BankTransaction
from neofinesse.models.ground_truth import (
    CaseGroundTruth,
    ExpectedOutcome,
    GroundTruthCause,
    GroundTruthDecoy,
    ScenarioType,
)


class ScenarioInjector:
    """Injects 10 controlled failure and edge scenarios into the synthetic financial world."""

    def __init__(self, rng: random.Random, provider: Provider = Provider.RAZORPAY):
        self.rng = rng
        self.provider = provider

    def inject_all_scenarios(
        self,
        base_time: datetime,
        orders: List[Order],
        payments: List[Payment],
        upi_txns: List[UPITransaction],
        upi_events: List[UPIEvent],
        refunds: List[Refund],
        disputes: List[Dispute],
        adjustments: List[Adjustment],
        settlement_lines: List[SettlementLine],
        settlements: List[Settlement],
        bank_txns: List[BankTransaction],
    ) -> List[CaseGroundTruth]:
        """Runs all 10 scenario injectors and returns ground truth records."""
        ground_truths: List[CaseGroundTruth] = []

        # VAR-001: Refund Variance
        gt1 = self._inject_var_001_refund_variance(
            base_time + timedelta(days=2), orders, payments, refunds, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt1)

        # VAR-002: Same-Amount Decoy
        gt2 = self._inject_var_002_same_amount_decoy(
            base_time + timedelta(days=5), orders, payments, refunds, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt2)

        # VAR-003: Partial Explanation
        gt3 = self._inject_var_003_partial_explanation(
            base_time + timedelta(days=8), orders, payments, refunds, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt3)

        # VAR-004: Multiple-Event Explanation
        gt4 = self._inject_var_004_multiple_event(
            base_time + timedelta(days=11), orders, payments, refunds, adjustments, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt4)

        # VAR-005: UPI Late Success
        gt5 = self._inject_var_005_upi_late_success(
            base_time + timedelta(days=14), orders, payments, upi_txns, upi_events, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt5)

        # VAR-006: UPI Debit + Reversal
        gt6 = self._inject_var_006_upi_debit_reversal(
            base_time + timedelta(days=17), orders, payments, upi_txns, upi_events
        )
        ground_truths.append(gt6)

        # VAR-007: Delayed Bank Credit
        gt7 = self._inject_var_007_delayed_bank_credit(
            base_time + timedelta(days=20), orders, payments, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt7)

        # VAR-008: Wrong-Date Decoy
        gt8 = self._inject_var_008_wrong_date_decoy(
            base_time + timedelta(days=23), orders, payments, refunds, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt8)

        # VAR-009: Wrong-Payment Decoy
        gt9 = self._inject_var_009_wrong_payment_decoy(
            base_time + timedelta(days=26), orders, payments, disputes, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt9)

        # VAR-010: Completely Unexplained Variance
        gt10 = self._inject_var_010_completely_unexplained(
            base_time + timedelta(days=28), orders, payments, settlement_lines, settlements, bank_txns
        )
        ground_truths.append(gt10)

        return ground_truths

    def _inject_var_001_refund_variance(
        self, t: datetime, orders, payments, refunds, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-001: Legitimate refund explains settlement variance."""
        order_id = f"order_scen_001_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_001_{self.rng.randint(1000, 9999)}"
        rfnd_id = f"rfnd_scen_001_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_001_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_001_p_{self.rng.randint(1000, 9999)}"
        line_rfnd_id = f"line_scen_001_r_{self.rng.randint(1000, 9999)}"
        utr = f"AXISCN{self.rng.randint(1000000000, 9999999999)}"

        gross_amount = 500000  # ₹5,000
        fee = 10000  # ₹100
        tax = 1800   # ₹18
        net_payment = gross_amount - fee - tax  # 488200
        refund_amount = 200000  # ₹2,000 refund

        orders.append(Order(id=order_id, amount=gross_amount, created_at=t))
        payment = Payment(
            id=pay_id,
            amount=gross_amount,
            status="captured",
            normalized_status=NormalizedObservedStatus.CAPTURED,
            order_id=order_id,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            created_at=t + timedelta(minutes=5),
            captured_at=t + timedelta(minutes=6),
            settled=True,
            settlement_id=setl_id,
            provider=self.provider,
        )
        payments.append(payment)

        refund = Refund(
            id=rfnd_id,
            amount=refund_amount,
            payment_id=pay_id,
            status=RefundStatus.PROCESSED,
            created_at=t + timedelta(hours=2),
            processed_at=t + timedelta(hours=3),
            settlement_id=setl_id,
            provider=self.provider,
        )
        refunds.append(refund)

        # Settlement Lines
        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_id,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_id,
            amount=gross_amount,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            event_timestamp=payment.captured_at,
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        sl_rfnd = SettlementLine(
            settlement_line_id=line_rfnd_id,
            settlement_id=setl_id,
            source_event_id=rfnd_id,
            source_event_type=SourceEventType.REFUND,
            payment_id=pay_id,
            amount=refund_amount,
            fee=0,
            tax=0,
            net_amount=-refund_amount,
            event_timestamp=refund.processed_at,
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.extend([sl_pay, sl_rfnd])

        # Actual settled = net_payment - refund_amount = 288200
        actual_settled = net_payment - refund_amount
        # In this scenario, variance is injected where expected baseline is net_payment (without refund) = 488200
        # and actual settled = 288200, so variance = 200000
        settlement = Settlement(
            id=setl_id,
            amount=actual_settled,
            status=SettlementStatus.PROCESSED,
            fees=fee,
            tax=tax,
            utr=utr,
            gross_amount=gross_amount,
            refund_total=refund_amount,
            expected_amount=net_payment - refund_amount,  # Mathematical expected = 288200
            variance=0,  # Line sum matches actual; investigator proves refund was the deduction
            created_at=t + timedelta(days=1),
            settled_at=t + timedelta(days=1, hours=2),
            provider=self.provider,
        )
        settlements.append(settlement)

        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_001_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=actual_settled,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY SETTLEMENT",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-001",
            settlement_id=setl_id,
            scenario=ScenarioType.REFUND_VARIANCE,
            expected_variance=-refund_amount,
            true_causes=[
                GroundTruthCause(
                    entity_type="refund",
                    entity_id=rfnd_id,
                    settlement_line_id=line_rfnd_id,
                    amount=-refund_amount,
                )
            ],
            explained_amount=-refund_amount,
            unexplained_amount=0,
            expected_outcome=ExpectedOutcome.RESOLVED,
            notes="Legitimate processed refund rfnd_scen_001 deducted from batch explains the settlement deficit.",
        )

    def _inject_var_002_same_amount_decoy(
        self, t: datetime, orders, payments, refunds, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-002: Same-amount wrong-entity decoy tests that amount equality alone is not proof."""
        order_real = f"order_scen_002_r_{self.rng.randint(1000, 9999)}"
        order_decoy = f"order_scen_002_d_{self.rng.randint(1000, 9999)}"
        pay_real = f"pay_scen_002_r_{self.rng.randint(1000, 9999)}"
        pay_decoy = f"pay_scen_002_d_{self.rng.randint(1000, 9999)}"
        rfnd_real = f"rfnd_scen_002_real_{self.rng.randint(1000, 9999)}"
        rfnd_decoy = f"rfnd_scen_002_decoy_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_002_{self.rng.randint(1000, 9999)}"
        setl_other = f"setl_scen_002_other_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_002_p_{self.rng.randint(1000, 9999)}"
        line_rfnd_id = f"line_scen_002_r_{self.rng.randint(1000, 9999)}"
        utr = f"HDFCN{self.rng.randint(1000000000, 9999999999)}"

        target_amount = 250000  # ₹2,500
        gross_pay = 800000     # ₹8,000
        fee = 16000
        tax = 2880
        net_pay = gross_pay - fee - tax

        orders.append(Order(id=order_real, amount=gross_pay, created_at=t))
        orders.append(Order(id=order_decoy, amount=gross_pay, created_at=t))

        payments.append(
            Payment(
                id=pay_real,
                amount=gross_pay,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_real,
                fee=fee,
                tax=tax,
                net_amount=net_pay,
                created_at=t + timedelta(minutes=5),
                captured_at=t + timedelta(minutes=6),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )
        payments.append(
            Payment(
                id=pay_decoy,
                amount=gross_pay,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_decoy,
                fee=fee,
                tax=tax,
                net_amount=net_pay,
                created_at=t + timedelta(minutes=10),
                captured_at=t + timedelta(minutes=11),
                settled=True,
                settlement_id=setl_other,
                provider=self.provider,
            )
        )

        # Real refund attached to setl_id
        refunds.append(
            Refund(
                id=rfnd_real,
                amount=target_amount,
                payment_id=pay_real,
                status=RefundStatus.PROCESSED,
                created_at=t + timedelta(hours=1),
                processed_at=t + timedelta(hours=2),
                settlement_id=setl_id,
                provider=self.provider,
            )
        )
        # Decoy refund with exact same amount but attached to setl_other
        refunds.append(
            Refund(
                id=rfnd_decoy,
                amount=target_amount,
                payment_id=pay_decoy,
                status=RefundStatus.PROCESSED,
                created_at=t + timedelta(hours=1),
                processed_at=t + timedelta(hours=2),
                settlement_id=setl_other,
                provider=self.provider,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_real,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_real,
            amount=gross_pay,
            fee=fee,
            tax=tax,
            net_amount=net_pay,
            event_timestamp=t + timedelta(minutes=6),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        sl_rfnd = SettlementLine(
            settlement_line_id=line_rfnd_id,
            settlement_id=setl_id,
            source_event_id=rfnd_real,
            source_event_type=SourceEventType.REFUND,
            payment_id=pay_real,
            amount=target_amount,
            fee=0,
            tax=0,
            net_amount=-target_amount,
            event_timestamp=t + timedelta(hours=2),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.extend([sl_pay, sl_rfnd])

        actual_settled = net_pay - target_amount
        settlements.append(
            Settlement(
                id=setl_id,
                amount=actual_settled,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=gross_pay,
                refund_total=target_amount,
                expected_amount=actual_settled,
                variance=0,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_002_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=actual_settled,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-002",
            settlement_id=setl_id,
            scenario=ScenarioType.SAME_AMOUNT_DECOY,
            expected_variance=-target_amount,
            true_causes=[
                GroundTruthCause(
                    entity_type="refund",
                    entity_id=rfnd_real,
                    settlement_line_id=line_rfnd_id,
                    amount=-target_amount,
                )
            ],
            decoys=[
                GroundTruthDecoy(
                    decoy_type="same_amount",
                    entity_type="refund",
                    entity_id=rfnd_decoy,
                    amount=target_amount,
                    rejection_reason="Belongs to payment pay_scen_002_d settled in batch setl_scen_002_other, not target settlement.",
                )
            ],
            explained_amount=-target_amount,
            unexplained_amount=0,
            expected_outcome=ExpectedOutcome.RESOLVED,
            notes="Decoy refund has identical ₹2,500 amount but belongs to another settlement batch.",
        )

    def _inject_var_003_partial_explanation(
        self, t: datetime, orders, payments, refunds, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-003: Only part of variance is explainable; residual must be escalated."""
        order_id = f"order_scen_003_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_003_{self.rng.randint(1000, 9999)}"
        rfnd_id = f"rfnd_scen_003_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_003_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_003_p_{self.rng.randint(1000, 9999)}"
        line_rfnd_id = f"line_scen_003_r_{self.rng.randint(1000, 9999)}"
        utr = f"ICICN{self.rng.randint(1000000000, 9999999999)}"

        gross_amount = 1000000  # ₹10,000
        fee = 20000
        tax = 3600
        net_payment = gross_amount - fee - tax  # 976400

        explained_amount = 300000    # ₹3,000 legitimate refund
        unexplained_amount = 200000  # ₹2,000 mysterious shortfall
        total_variance = explained_amount + unexplained_amount  # ₹5,000

        orders.append(Order(id=order_id, amount=gross_amount, created_at=t))
        payments.append(
            Payment(
                id=pay_id,
                amount=gross_amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_id,
                fee=fee,
                tax=tax,
                net_amount=net_payment,
                created_at=t,
                captured_at=t + timedelta(minutes=2),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )
        refunds.append(
            Refund(
                id=rfnd_id,
                amount=explained_amount,
                payment_id=pay_id,
                status=RefundStatus.PROCESSED,
                created_at=t + timedelta(hours=1),
                processed_at=t + timedelta(hours=2),
                settlement_id=setl_id,
                provider=self.provider,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_id,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_id,
            amount=gross_amount,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            event_timestamp=t + timedelta(minutes=2),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        sl_rfnd = SettlementLine(
            settlement_line_id=line_rfnd_id,
            settlement_id=setl_id,
            source_event_id=rfnd_id,
            source_event_type=SourceEventType.REFUND,
            payment_id=pay_id,
            amount=explained_amount,
            fee=0,
            tax=0,
            net_amount=-explained_amount,
            event_timestamp=t + timedelta(hours=2),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.extend([sl_pay, sl_rfnd])

        expected_calc = net_payment - explained_amount  # 676400
        actual_settled = expected_calc - unexplained_amount  # 476400 (unexplained shortfall)

        settlements.append(
            Settlement(
                id=setl_id,
                amount=actual_settled,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=gross_amount,
                refund_total=explained_amount,
                expected_amount=expected_calc,
                variance=unexplained_amount,
                recon_status=SettlementReconStatus.VARIANCE_DETECTED,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_003_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=actual_settled,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-003",
            settlement_id=setl_id,
            scenario=ScenarioType.PARTIAL_EXPLANATION,
            expected_variance=unexplained_amount,
            true_causes=[
                GroundTruthCause(
                    entity_type="refund",
                    entity_id=rfnd_id,
                    settlement_line_id=line_rfnd_id,
                    amount=-explained_amount,
                )
            ],
            explained_amount=explained_amount,
            unexplained_amount=unexplained_amount,
            expected_outcome=ExpectedOutcome.PARTIALLY_RESOLVED,
            notes="Refund explains ₹3,000 of ₹5,000 variance; remaining ₹2,000 has no matching event and must be escalated.",
        )

    def _inject_var_004_multiple_event(
        self, t: datetime, orders, payments, refunds, adjustments, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-004: Multiple legitimate events jointly explain variance."""
        order_id = f"order_scen_004_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_004_{self.rng.randint(1000, 9999)}"
        rfnd_id = f"rfnd_scen_004_{self.rng.randint(1000, 9999)}"
        adj_id = f"adj_scen_004_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_004_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_004_p_{self.rng.randint(1000, 9999)}"
        line_rfnd_id = f"line_scen_004_r_{self.rng.randint(1000, 9999)}"
        line_adj_id = f"line_scen_004_a_{self.rng.randint(1000, 9999)}"
        utr = f"SBIN00{self.rng.randint(1000000000, 9999999999)}"

        gross_amount = 1500000  # ₹15,000
        fee = 30000
        tax = 5400
        net_payment = gross_amount - fee - tax  # 1464600

        refund_amount = 70000    # ₹700
        adjustment_amount = 30000 # ₹300 risk hold debit
        total_deductions = refund_amount + adjustment_amount  # ₹1,000

        orders.append(Order(id=order_id, amount=gross_amount, created_at=t))
        payments.append(
            Payment(
                id=pay_id,
                amount=gross_amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_id,
                fee=fee,
                tax=tax,
                net_amount=net_payment,
                created_at=t,
                captured_at=t + timedelta(minutes=2),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )
        refunds.append(
            Refund(
                id=rfnd_id,
                amount=refund_amount,
                payment_id=pay_id,
                status=RefundStatus.PROCESSED,
                created_at=t + timedelta(hours=1),
                processed_at=t + timedelta(hours=2),
                settlement_id=setl_id,
                provider=self.provider,
            )
        )
        adjustments.append(
            Adjustment(
                id=adj_id,
                amount=-adjustment_amount,
                description="Risk reserve hold",
                settlement_id=setl_id,
                adjustment_type=AdjustmentType.RISK_HOLD,
                created_at=t + timedelta(hours=3),
                provider=self.provider,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_id,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_id,
            amount=gross_amount,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            event_timestamp=t + timedelta(minutes=2),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        sl_rfnd = SettlementLine(
            settlement_line_id=line_rfnd_id,
            settlement_id=setl_id,
            source_event_id=rfnd_id,
            source_event_type=SourceEventType.REFUND,
            payment_id=pay_id,
            amount=refund_amount,
            fee=0,
            tax=0,
            net_amount=-refund_amount,
            event_timestamp=t + timedelta(hours=2),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        sl_adj = SettlementLine(
            settlement_line_id=line_adj_id,
            settlement_id=setl_id,
            source_event_id=adj_id,
            source_event_type=SourceEventType.ADJUSTMENT,
            amount=adjustment_amount,
            fee=0,
            tax=0,
            net_amount=-adjustment_amount,
            event_timestamp=t + timedelta(hours=3),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.extend([sl_pay, sl_rfnd, sl_adj])

        actual_settled = net_payment - total_deductions
        settlements.append(
            Settlement(
                id=setl_id,
                amount=actual_settled,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=gross_amount,
                refund_total=refund_amount,
                adjustment_total=-adjustment_amount,
                expected_amount=actual_settled,
                variance=0,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_004_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=actual_settled,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-004",
            settlement_id=setl_id,
            scenario=ScenarioType.MULTIPLE_EVENT_EXPLANATION,
            expected_variance=-total_deductions,
            true_causes=[
                GroundTruthCause(
                    entity_type="refund",
                    entity_id=rfnd_id,
                    settlement_line_id=line_rfnd_id,
                    amount=-refund_amount,
                ),
                GroundTruthCause(
                    entity_type="adjustment",
                    entity_id=adj_id,
                    settlement_line_id=line_adj_id,
                    amount=-adjustment_amount,
                ),
            ],
            explained_amount=-total_deductions,
            unexplained_amount=0,
            expected_outcome=ExpectedOutcome.RESOLVED,
            notes="Joint attribution: ₹700 refund + ₹300 risk hold adjustment = ₹1,000 total variance.",
        )

    def _inject_var_005_upi_late_success(
        self, t: datetime, orders, payments, upi_txns, upi_events, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-005: UPI payment initially reported FAILED later authorized (LATE_SUCCESS)."""
        order_id = f"order_scen_005_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_005_{self.rng.randint(1000, 9999)}"
        upi_id = f"upi_scen_005_{self.rng.randint(1000, 9999)}"
        rrn = f"{self.rng.randint(100000000000, 999999999999)}"
        setl_id = f"setl_scen_005_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_005_p_{self.rng.randint(1000, 9999)}"
        utr = f"KOTAKN{self.rng.randint(1000000000, 9999999999)}"

        amount = 350000  # ₹3,500
        fee = 7000
        tax = 1260
        net_pay = amount - fee - tax

        orders.append(Order(id=order_id, amount=amount, created_at=t))
        payments.append(
            Payment(
                id=pay_id,
                amount=amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_id,
                method="upi",
                vpa="customer@okaxis",
                fee=fee,
                tax=tax,
                net_amount=net_pay,
                acquirer_data={"rrn": rrn},
                created_at=t,
                captured_at=t + timedelta(minutes=27),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )

        upi_txns.append(
            UPITransaction(
                upi_transaction_id=upi_id,
                payment_id=pay_id,
                order_id=order_id,
                rrn=rrn,
                amount=amount,
                vpa="customer@okaxis",
                initiated_at=t,
                current_observed_status=NormalizedObservedStatus.CAPTURED,
                final_determined_status=FinalDeterminedStatus.LATE_SUCCESS,
                debit_observed=True,
                reversal_status=ReversalStatus.NONE,
                financial_effect_status=FinancialEffectStatus.DETERMINED,
                financial_effect_amount=amount,
                provider=self.provider,
            )
        )

        # State transitions: INITIATED -> PENDING -> FAILED -> CAPTURED (Late Auth)
        upi_events.append(
            UPIEvent(
                event_id=f"upievt_005_1_{self.rng.randint(1000, 9999)}",
                upi_transaction_id=upi_id,
                timestamp=t,
                previous_state=NormalizedObservedStatus.INITIATED,
                new_state=NormalizedObservedStatus.PENDING,
                event_type="UPI_INTENT_SENT",
                amount=amount,
                rrn=rrn,
            )
        )
        upi_events.append(
            UPIEvent(
                event_id=f"upievt_005_2_{self.rng.randint(1000, 9999)}",
                upi_transaction_id=upi_id,
                timestamp=t + timedelta(minutes=5),
                previous_state=NormalizedObservedStatus.PENDING,
                new_state=NormalizedObservedStatus.FAILED,
                event_type="BANK_TIMEOUT_RESPONSE",
                amount=amount,
                rrn=rrn,
            )
        )
        upi_events.append(
            UPIEvent(
                event_id=f"upievt_005_3_{self.rng.randint(1000, 9999)}",
                upi_transaction_id=upi_id,
                timestamp=t + timedelta(minutes=27),
                previous_state=NormalizedObservedStatus.FAILED,
                new_state=NormalizedObservedStatus.CAPTURED,
                event_type="LATE_AUTHORIZATION_CALLBACK",
                amount=amount,
                rrn=rrn,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_id,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_id,
            amount=amount,
            fee=fee,
            tax=tax,
            net_amount=net_pay,
            event_timestamp=t + timedelta(minutes=27),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.append(sl_pay)

        settlements.append(
            Settlement(
                id=setl_id,
                amount=net_pay,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=amount,
                expected_amount=net_pay,
                variance=0,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_005_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=net_pay,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-005",
            settlement_id=setl_id,
            scenario=ScenarioType.UPI_LATE_SUCCESS,
            expected_variance=0,
            true_causes=[
                GroundTruthCause(
                    entity_type="upi_transaction",
                    entity_id=upi_id,
                    settlement_line_id=line_pay_id,
                    amount=net_pay,
                )
            ],
            explained_amount=net_pay,
            unexplained_amount=0,
            expected_outcome=ExpectedOutcome.RESOLVED,
            notes="UPI transaction initially failed but achieved late success at T+27m; event history confirms settlement inclusion.",
        )

    def _inject_var_006_upi_debit_reversal(
        self, t: datetime, orders, payments, upi_txns, upi_events
    ) -> CaseGroundTruth:
        """VAR-006: UPI failed with customer debit followed by confirmed reversal (net financial effect = 0)."""
        order_id = f"order_scen_006_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_006_{self.rng.randint(1000, 9999)}"
        upi_id = f"upi_scen_006_{self.rng.randint(1000, 9999)}"
        rrn = f"{self.rng.randint(100000000000, 999999999999)}"

        amount = 500000  # ₹5,000

        orders.append(Order(id=order_id, amount=amount, created_at=t))
        payments.append(
            Payment(
                id=pay_id,
                amount=amount,
                status="failed",
                normalized_status=NormalizedObservedStatus.FAILED,
                order_id=order_id,
                method="upi",
                vpa="payer@okhdfcbank",
                fee=0,
                tax=0,
                net_amount=0,
                error_code="BAD_REQUEST_ERROR",
                error_description="Transaction failed at bank switch",
                acquirer_data={"rrn": rrn},
                created_at=t,
                settled=False,
                provider=self.provider,
            )
        )

        upi_txns.append(
            UPITransaction(
                upi_transaction_id=upi_id,
                payment_id=pay_id,
                order_id=order_id,
                rrn=rrn,
                amount=amount,
                vpa="payer@okhdfcbank",
                initiated_at=t,
                current_observed_status=NormalizedObservedStatus.FAILED,
                final_determined_status=FinalDeterminedStatus.FAILED,
                debit_observed=True,
                reversal_status=ReversalStatus.SUCCESS,
                reversal_amount=amount,
                reversal_at=t + timedelta(minutes=15),
                financial_effect_status=FinancialEffectStatus.DETERMINED,
                financial_effect_amount=0,  # Net financial effect is 0
                provider=self.provider,
            )
        )

        upi_events.append(
            UPIEvent(
                event_id=f"upievt_006_1_{self.rng.randint(1000, 9999)}",
                upi_transaction_id=upi_id,
                timestamp=t,
                previous_state=NormalizedObservedStatus.INITIATED,
                new_state=NormalizedObservedStatus.FAILED,
                event_type="PAYER_DEBITED_GATEWAY_TIMEOUT",
                amount=amount,
                rrn=rrn,
            )
        )
        upi_events.append(
            UPIEvent(
                event_id=f"upievt_006_2_{self.rng.randint(1000, 9999)}",
                upi_transaction_id=upi_id,
                timestamp=t + timedelta(minutes=15),
                previous_state=NormalizedObservedStatus.FAILED,
                new_state=NormalizedObservedStatus.FAILED,
                event_type="AUTO_REVERSAL_CONFIRMATION",
                amount=amount,
                rrn=rrn,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-006",
            settlement_id="N/A",
            scenario=ScenarioType.UPI_DEBIT_REVERSAL,
            expected_variance=0,
            true_causes=[],
            decoys=[
                GroundTruthDecoy(
                    decoy_type="reversal_net_zero",
                    entity_type="upi_transaction",
                    entity_id=upi_id,
                    amount=amount,
                    rejection_reason="Customer was debited but auto-reversal completed at T+15m. Net financial effect = 0, so cannot explain settlement deficit.",
                )
            ],
            explained_amount=0,
            unexplained_amount=0,
            expected_outcome=ExpectedOutcome.RESOLVED,
            notes="Failed UPI payment with debit and confirmed reversal produces net financial effect of ₹0.",
        )

    def _inject_var_007_delayed_bank_credit(
        self, t: datetime, orders, payments, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-007: Settlement processed by gateway but bank credit in transit within allowable clearing window."""
        order_id = f"order_scen_007_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_007_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_007_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_007_p_{self.rng.randint(1000, 9999)}"
        utr = f"BARBN{self.rng.randint(1000000000, 9999999999)}"

        gross_amount = 2000000  # ₹20,000
        fee = 40000
        tax = 7200
        net_payment = gross_amount - fee - tax  # 1952800

        orders.append(Order(id=order_id, amount=gross_amount, created_at=t))
        payments.append(
            Payment(
                id=pay_id,
                amount=gross_amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_id,
                fee=fee,
                tax=tax,
                net_amount=net_payment,
                created_at=t,
                captured_at=t + timedelta(minutes=1),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_id,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_id,
            amount=gross_amount,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            event_timestamp=t + timedelta(minutes=1),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.append(sl_pay)

        # Settlement created at T+1, bank credit posted at T+2 (1.5 days later)
        settlements.append(
            Settlement(
                id=setl_id,
                amount=net_payment,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=gross_amount,
                expected_amount=net_payment,
                variance=0,
                recon_status=SettlementReconStatus.PENDING_BANK_CREDIT,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )

        # Bank credit arrives 36 hours later (within standard T+2 clearing window)
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_007_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=net_payment,
                value_date=t + timedelta(days=2, hours=14),
                transaction_date=t + timedelta(days=2, hours=14),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-007",
            settlement_id=setl_id,
            scenario=ScenarioType.DELAYED_BANK_CREDIT,
            expected_variance=0,
            true_causes=[],
            explained_amount=net_payment,
            unexplained_amount=0,
            expected_outcome=ExpectedOutcome.VALID_DELAYED_CREDIT,
            notes="Settlement processed at gateway; bank credit arrived 36 hours later within normal clearing window.",
        )

    def _inject_var_008_wrong_date_decoy(
        self, t: datetime, orders, payments, refunds, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-008: Matching-amount event exists but occurred outside valid temporal relationship."""
        order_id = f"order_scen_008_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_008_{self.rng.randint(1000, 9999)}"
        rfnd_decoy = f"rfnd_scen_008_decoy_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_008_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_008_p_{self.rng.randint(1000, 9999)}"
        utr = f"PUNBN{self.rng.randint(1000000000, 9999999999)}"

        gross_amount = 1200000  # ₹12,000
        fee = 24000
        tax = 4320
        net_payment = gross_amount - fee - tax  # 1171680
        shortfall = 400000  # ₹4,000 variance

        orders.append(Order(id=order_id, amount=gross_amount, created_at=t))
        payments.append(
            Payment(
                id=pay_id,
                amount=gross_amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_id,
                fee=fee,
                tax=tax,
                net_amount=net_payment,
                created_at=t,
                captured_at=t + timedelta(minutes=1),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )

        # Decoy refund with exact matching amount (₹4,000) but processed 20 days AFTER settlement batch
        refunds.append(
            Refund(
                id=rfnd_decoy,
                amount=shortfall,
                payment_id=pay_id,
                status=RefundStatus.PROCESSED,
                created_at=t + timedelta(days=21),
                processed_at=t + timedelta(days=21, hours=2),
                settlement_id="setl_future_batch",
                provider=self.provider,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_id,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_id,
            amount=gross_amount,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            event_timestamp=t + timedelta(minutes=1),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.append(sl_pay)

        actual_settled = net_payment - shortfall  # Unexplained shortfall at T+1
        settlements.append(
            Settlement(
                id=setl_id,
                amount=actual_settled,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=gross_amount,
                expected_amount=net_payment,
                variance=shortfall,
                recon_status=SettlementReconStatus.VARIANCE_DETECTED,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_008_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=actual_settled,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-008",
            settlement_id=setl_id,
            scenario=ScenarioType.WRONG_DATE_DECOY,
            expected_variance=shortfall,
            true_causes=[],
            decoys=[
                GroundTruthDecoy(
                    decoy_type="wrong_date",
                    entity_type="refund",
                    entity_id=rfnd_decoy,
                    amount=shortfall,
                    rejection_reason="Refund processed on T+21 days, well after batch settlement cutoff at T+1 day.",
                )
            ],
            explained_amount=0,
            unexplained_amount=shortfall,
            expected_outcome=ExpectedOutcome.ESCALATE,
            notes="Decoy refund matches ₹4,000 amount but occurred 20 days after settlement cutoff; must be rejected.",
        )

    def _inject_var_009_wrong_payment_decoy(
        self, t: datetime, orders, payments, disputes, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-009: Matching dispute belongs to another payment/settlement (entity decoy)."""
        order_1 = f"order_scen_009_1_{self.rng.randint(1000, 9999)}"
        order_2 = f"order_scen_009_2_{self.rng.randint(1000, 9999)}"
        pay_1 = f"pay_scen_009_1_{self.rng.randint(1000, 9999)}"
        pay_2 = f"pay_scen_009_2_{self.rng.randint(1000, 9999)}"
        disp_decoy = f"disp_scen_009_decoy_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_009_{self.rng.randint(1000, 9999)}"
        setl_other = f"setl_scen_009_other_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_009_p_{self.rng.randint(1000, 9999)}"
        utr = f"UNIONN{self.rng.randint(1000000000, 9999999999)}"

        gross_amount = 900000  # ₹9,000
        fee = 18000
        tax = 3240
        net_payment = gross_amount - fee - tax  # 878760
        variance_amount = 350000  # ₹3,500 shortfall

        orders.append(Order(id=order_1, amount=gross_amount, created_at=t))
        orders.append(Order(id=order_2, amount=gross_amount, created_at=t))

        payments.append(
            Payment(
                id=pay_1,
                amount=gross_amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_1,
                fee=fee,
                tax=tax,
                net_amount=net_payment,
                created_at=t,
                captured_at=t + timedelta(minutes=1),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )
        payments.append(
            Payment(
                id=pay_2,
                amount=gross_amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_2,
                fee=fee,
                tax=tax,
                net_amount=net_payment,
                created_at=t,
                captured_at=t + timedelta(minutes=1),
                settled=True,
                settlement_id=setl_other,
                provider=self.provider,
            )
        )

        # Decoy dispute of ₹3,500 attached to pay_2 and setl_other
        disputes.append(
            Dispute(
                id=disp_decoy,
                payment_id=pay_2,
                amount=variance_amount,
                amount_deducted=variance_amount,
                status=DisputeStatus.OPEN,
                phase=DisputePhase.CHARGEBACK,
                created_at=t + timedelta(hours=5),
                settlement_id=setl_other,
                provider=self.provider,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_1,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_1,
            amount=gross_amount,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            event_timestamp=t + timedelta(minutes=1),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.append(sl_pay)

        actual_settled = net_payment - variance_amount
        settlements.append(
            Settlement(
                id=setl_id,
                amount=actual_settled,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=gross_amount,
                expected_amount=net_payment,
                variance=variance_amount,
                recon_status=SettlementReconStatus.VARIANCE_DETECTED,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_009_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=actual_settled,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-009",
            settlement_id=setl_id,
            scenario=ScenarioType.WRONG_PAYMENT_DECOY,
            expected_variance=variance_amount,
            true_causes=[],
            decoys=[
                GroundTruthDecoy(
                    decoy_type="wrong_payment",
                    entity_type="dispute",
                    entity_id=disp_decoy,
                    amount=variance_amount,
                    rejection_reason="Dispute belongs to pay_2 and settlement setl_scen_009_other, not pay_1 in target settlement.",
                )
            ],
            explained_amount=0,
            unexplained_amount=variance_amount,
            expected_outcome=ExpectedOutcome.ESCALATE,
            notes="Dispute of ₹3,500 belongs to a different payment; case has no valid cause and must be escalated.",
        )

    def _inject_var_010_completely_unexplained(
        self, t: datetime, orders, payments, settlement_lines, settlements, bank_txns
    ) -> CaseGroundTruth:
        """VAR-010: Genuine variance with no supporting event anywhere in dataset (must ESCALATE)."""
        order_id = f"order_scen_010_{self.rng.randint(1000, 9999)}"
        pay_id = f"pay_scen_010_{self.rng.randint(1000, 9999)}"
        setl_id = f"setl_scen_010_{self.rng.randint(1000, 9999)}"
        line_pay_id = f"line_scen_010_p_{self.rng.randint(1000, 9999)}"
        utr = f"IDBIN0{self.rng.randint(1000000000, 9999999999)}"

        gross_amount = 3000000  # ₹30,000
        fee = 60000
        tax = 10800
        net_payment = gross_amount - fee - tax  # 2929200
        unexplained_variance = 1500000  # ₹15,000 massive deficit

        orders.append(Order(id=order_id, amount=gross_amount, created_at=t))
        payments.append(
            Payment(
                id=pay_id,
                amount=gross_amount,
                status="captured",
                normalized_status=NormalizedObservedStatus.CAPTURED,
                order_id=order_id,
                fee=fee,
                tax=tax,
                net_amount=net_payment,
                created_at=t,
                captured_at=t + timedelta(minutes=1),
                settled=True,
                settlement_id=setl_id,
                provider=self.provider,
            )
        )

        sl_pay = SettlementLine(
            settlement_line_id=line_pay_id,
            settlement_id=setl_id,
            source_event_id=pay_id,
            source_event_type=SourceEventType.PAYMENT,
            payment_id=pay_id,
            amount=gross_amount,
            fee=fee,
            tax=tax,
            net_amount=net_payment,
            event_timestamp=t + timedelta(minutes=1),
            settlement_timestamp=t + timedelta(days=1),
            provider=self.provider,
        )
        settlement_lines.append(sl_pay)

        actual_settled = net_payment - unexplained_variance
        settlements.append(
            Settlement(
                id=setl_id,
                amount=actual_settled,
                status=SettlementStatus.PROCESSED,
                fees=fee,
                tax=tax,
                utr=utr,
                gross_amount=gross_amount,
                expected_amount=net_payment,
                variance=unexplained_variance,
                recon_status=SettlementReconStatus.VARIANCE_DETECTED,
                created_at=t + timedelta(days=1),
                settled_at=t + timedelta(days=1, hours=2),
                provider=self.provider,
            )
        )
        bank_txns.append(
            BankTransaction(
                bank_txn_id=f"bank_scen_010_{self.rng.randint(1000, 9999)}",
                utr=utr,
                credit_amount=actual_settled,
                value_date=t + timedelta(days=1, hours=3),
                transaction_date=t + timedelta(days=1, hours=3),
                raw_description=f"CMS/NEFT/{utr}/RAZORPAY",
                parsed_utr=utr,
            )
        )

        return CaseGroundTruth(
            case_id="CASE-010",
            settlement_id=setl_id,
            scenario=ScenarioType.COMPLETELY_UNEXPLAINED,
            expected_variance=unexplained_variance,
            true_causes=[],
            explained_amount=0,
            unexplained_amount=unexplained_variance,
            expected_outcome=ExpectedOutcome.ESCALATE,
            notes="Completely unexplained ₹15,000 variance with zero supporting records; system must honestly escalate without guessing.",
        )

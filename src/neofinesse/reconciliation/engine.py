from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.models.base import EvidenceLevel, FinalDeterminedStatus, SourceEventType
from neofinesse.reconciliation.audit import AuditRecordBuilder, CaseAuditRecord
from neofinesse.reconciliation.candidates import CandidateRetriever
from neofinesse.reconciliation.classifier import ReconciliationClassifier
from neofinesse.reconciliation.joins import BankJoinEngine, BankJoinResult, BankJoinStatus
from neofinesse.reconciliation.solver import (
    MultiConstraintAttributionSolver,
    VerifiedCause,
)
from neofinesse.reconciliation.upi_state import UPIStateReconstructor


class ReconciliationRunResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_records: List[CaseAuditRecord] = Field(default_factory=list)
    total_settlements: int = 0
    matched_settlements: int = 0
    variance_cases: int = 0
    resolved_cases: int = 0
    partially_resolved_cases: int = 0
    escalated_cases: int = 0
    delayed_credit_cases: int = 0


class DeterministicReconciliationEngine:
    """End-to-end deterministic reconciliation engine executing bank joins, candidate pruning, and variance attribution."""

    def __init__(self, max_clearing_window_hours: float = 48.0):
        self.bank_join_engine = BankJoinEngine(max_clearing_window_hours)
        self.upi_reconstructor = UPIStateReconstructor()
        self.candidate_retriever = CandidateRetriever()
        self.attribution_solver = MultiConstraintAttributionSolver()
        self.classifier = ReconciliationClassifier()

    def run(self, dataset: IngestedDataset) -> ReconciliationRunResult:
        """Executes full deterministic reconciliation over the ingested dataset."""
        # 1. Match Settlements to Bank Transactions via UTR
        bank_joins = self.bank_join_engine.match_settlements_to_bank(
            dataset.settlements, dataset.bank_transactions
        )

        # 2. Pre-reconstruct UPI states
        reconstructed_upi = {}
        for u in dataset.upi_transactions:
            reconstructed_upi[u.upi_transaction_id] = self.upi_reconstructor.reconstruct(
                u, dataset.upi_events
            )

        # 3. Reconcile each settlement
        case_records: List[CaseAuditRecord] = []
        case_counter = 1

        for s in dataset.settlements:
            # Calculate mathematical expected amount from settlement lines
            batch_lines = [l for l in dataset.settlement_lines if l.settlement_id == s.id]
            expected_amount = sum(l.net_amount for l in batch_lines)
            actual_amount = s.amount

            # Check if there is an explicit variance or deductions in the settlement
            deductions = -(s.refund_total + abs(s.adjustment_total) + s.dispute_total)
            if s.variance != 0:
                effective_variance = s.variance
            elif deductions != 0:
                effective_variance = deductions
            else:
                effective_variance = expected_amount - actual_amount

            bank_join = bank_joins.get(s.id)
            bank_amount = bank_join.bank_amount if bank_join else None
            bank_credit_matched = (bank_join.join_status in (BankJoinStatus.EXACT_UTR_MATCH, BankJoinStatus.DELAYED_BANK_CREDIT)) if bank_join else False

            case_id = f"CASE-{case_counter:03d}"
            case_counter += 1

            audit_trail = [
                {
                    "timestamp": s.created_at.isoformat(),
                    "action": "SETTLEMENT_INGESTION",
                    "settlement_id": s.id,
                    "line_count": len(batch_lines),
                    "expected_amount_inr": expected_amount / 100.0,
                    "actual_amount_inr": actual_amount / 100.0,
                    "variance_inr": effective_variance / 100.0,
                },
                {
                    "timestamp": s.created_at.isoformat(),
                    "action": "BANK_UTR_JOIN",
                    "utr": s.utr,
                    "join_status": bank_join.join_status if bank_join else "NO_JOIN",
                    "bank_credit_inr": (bank_amount / 100.0) if bank_amount is not None else None,
                },
            ]

            # Case A: Delayed bank credit within window (VAR-007)
            if bank_join and bank_join.join_status == BankJoinStatus.DELAYED_BANK_CREDIT:
                status, level, rationale = self.classifier.classify_case(
                    expected_amount, actual_amount, bank_join, self.attribution_solver.solve(s, 0, [])
                )
                case_records.append(
                    AuditRecordBuilder.build_case_record(
                        case_id=case_id,
                        settlement_id=s.id,
                        expected_amount=expected_amount,
                        actual_amount=actual_amount,
                        bank_amount=bank_amount,
                        variance_amount=0,
                        status=status,
                        explained_amount=expected_amount,
                        unexplained_amount=0,
                        verified_causes=[],
                        rejected_candidates=[],
                        evidence_level=level,
                        utr=s.utr,
                        bank_credit_matched=True,
                        escalation_reason=None,
                        audit_trail=audit_trail,
                    )
                )
                continue

            # Case B: Check for UPI Late Success in batch lines (VAR-005)
            batch_payment_ids = {l.source_event_id for l in batch_lines if l.source_event_type == SourceEventType.PAYMENT}
            late_upi_causes = []
            for p_id in batch_payment_ids:
                u_recon = next((u for u in reconstructed_upi.values() if u.payment_id == p_id and u.determined_status == FinalDeterminedStatus.LATE_SUCCESS), None)
                if u_recon:
                    orig_upi = next(u for u in dataset.upi_transactions if u.upi_transaction_id == u_recon.upi_transaction_id)
                    sl = next((l for l in batch_lines if l.source_event_id == p_id), None)
                    late_upi_causes.append(
                        VerifiedCause(
                            entity_type="upi_transaction",
                            entity_id=u_recon.upi_transaction_id,
                            settlement_line_id=sl.settlement_line_id if sl else None,
                            amount=sl.net_amount if sl else u_recon.amount,
                            net_financial_effect=sl.net_amount if sl else u_recon.amount,
                            relationship_path=f"Settlement({s.id}) → SettlementLine({sl.settlement_line_id if sl else ''}) → UPITransaction({u_recon.upi_transaction_id})",
                            evidence_level=EvidenceLevel.L5,
                            provenance=orig_upi.provenance,
                            verification_chain=[
                                f"UPI state reconstructed: {u_recon.reconstruction_notes}",
                                f"Late authorization confirmed capture at {u_recon.latest_event_timestamp}",
                            ],
                        )
                    )

            if effective_variance == 0 and late_upi_causes:
                case_records.append(
                    AuditRecordBuilder.build_case_record(
                        case_id=case_id,
                        settlement_id=s.id,
                        expected_amount=expected_amount,
                        actual_amount=actual_amount,
                        bank_amount=bank_amount,
                        variance_amount=0,
                        status="RESOLVED",
                        explained_amount=sum(c.amount for c in late_upi_causes),
                        unexplained_amount=0,
                        verified_causes=late_upi_causes,
                        rejected_candidates=[],
                        evidence_level=EvidenceLevel.L5,
                        utr=s.utr,
                        bank_credit_matched=bank_credit_matched,
                        escalation_reason=None,
                        audit_trail=audit_trail,
                    )
                )
                continue

            # Case C: Clean zero-variance matched settlement (no deductions, no late UPI)
            has_deductions = (s.refund_total > 0 or s.adjustment_total != 0 or s.dispute_total > 0)
            if effective_variance == 0 and not has_deductions and bank_credit_matched:
                status, level, rationale = self.classifier.classify_case(
                    expected_amount, actual_amount, bank_join, self.attribution_solver.solve(s, 0, [])
                )
                case_records.append(
                    AuditRecordBuilder.build_case_record(
                        case_id=case_id,
                        settlement_id=s.id,
                        expected_amount=expected_amount,
                        actual_amount=actual_amount,
                        bank_amount=bank_amount,
                        variance_amount=0,
                        status=status,
                        explained_amount=expected_amount,
                        unexplained_amount=0,
                        verified_causes=[],
                        rejected_candidates=[],
                        evidence_level=level,
                        utr=s.utr,
                        bank_credit_matched=True,
                        escalation_reason=None,
                        audit_trail=audit_trail,
                    )
                )
                continue

            # Case D: Variance detected OR deductions requiring attribution investigation
            candidates = self.candidate_retriever.retrieve_candidates_for_settlement(
                settlement=s,
                settlement_lines=dataset.settlement_lines,
                payments=dataset.payments,
                refunds=dataset.refunds,
                disputes=dataset.disputes,
                adjustments=dataset.adjustments,
                transfers=dataset.transfers,
                upi_txns=dataset.upi_transactions,
            )

            attribution = self.attribution_solver.solve(s, effective_variance, candidates)
            status, level, rationale = self.classifier.classify_case(
                expected_amount, actual_amount, bank_join, attribution
            )

            escalation_reason = None
            if status == "ESCALATE":
                escalation_reason = f"Unexplained variance of ₹{abs(effective_variance)/100:.2f} has no valid supporting evidence."
            elif status == "PARTIALLY_RESOLVED":
                escalation_reason = f"Shortfall of ₹{attribution.unexplained_amount/100:.2f} remains unverified."

            case_records.append(
                AuditRecordBuilder.build_case_record(
                    case_id=case_id,
                    settlement_id=s.id,
                    expected_amount=expected_amount,
                    actual_amount=actual_amount,
                    bank_amount=bank_amount,
                    variance_amount=effective_variance,
                    status=status,
                    explained_amount=attribution.explained_amount,
                    unexplained_amount=attribution.unexplained_amount,
                    verified_causes=attribution.verified_causes,
                    rejected_candidates=attribution.rejected_candidates,
                    evidence_level=level,
                    utr=s.utr,
                    bank_credit_matched=bank_credit_matched,
                    escalation_reason=escalation_reason,
                    audit_trail=audit_trail,
                )
            )

        # 4. Compute aggregate metrics
        total_s = len(dataset.settlements)
        matched_s = sum(1 for c in case_records if c.status == "MATCHED")
        resolved_s = sum(1 for c in case_records if c.status == "RESOLVED")
        partial_s = sum(1 for c in case_records if c.status == "PARTIALLY_RESOLVED")
        escalated_s = sum(1 for c in case_records if c.status == "ESCALATE")
        delayed_s = sum(1 for c in case_records if c.status == "VALID_DELAYED_CREDIT")
        variance_s = total_s - matched_s

        return ReconciliationRunResult(
            case_records=case_records,
            total_settlements=total_s,
            matched_settlements=matched_s,
            variance_cases=variance_s,
            resolved_cases=resolved_s,
            partially_resolved_cases=partial_s,
            escalated_cases=escalated_s,
            delayed_credit_cases=delayed_s,
        )

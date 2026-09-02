from typing import Tuple
from neofinesse.models.base import EvidenceLevel
from neofinesse.reconciliation.joins import BankJoinResult, BankJoinStatus
from neofinesse.reconciliation.solver import AttributionResult


class ReconciliationClassifier:
    """Classifies reconciliation and variance cases into standardized outcomes with evidence levels."""

    @staticmethod
    def classify_case(
        expected_amount: int,
        actual_amount: int,
        bank_join: BankJoinResult,
        attribution: AttributionResult,
    ) -> Tuple[str, EvidenceLevel, str]:
        """Returns (final_status, evidence_level, rationale)."""
        variance = expected_amount - actual_amount

        # Case 1: Valid Delayed Bank Credit
        if bank_join.join_status == BankJoinStatus.DELAYED_BANK_CREDIT:
            return (
                "VALID_DELAYED_CREDIT",
                EvidenceLevel.L5,
                f"Settlement processed at gateway and bank credit cleared within allowable window ({bank_join.clearing_delay_hours:.1f}h).",
            )

        # Case 2: Clean Matched Settlement (Zero Variance + Exact Bank Credit + No Deductions)
        if variance == 0 and len(attribution.verified_causes) == 0 and bank_join.join_status == BankJoinStatus.EXACT_UTR_MATCH:
            return (
                "MATCHED",
                EvidenceLevel.L5,
                "Settlement line sum exactly matches settled amount and bank credit confirmed via UTR.",
            )

        # Case 3: Variance or Deductions Attributed & Solved
        if attribution.solver_status == "RESOLVED":
            level = EvidenceLevel.L5 if bank_join.join_status in (BankJoinStatus.EXACT_UTR_MATCH, BankJoinStatus.DELAYED_BANK_CREDIT) else EvidenceLevel.L4
            return (
                "RESOLVED",
                level,
                f"Variance of {abs(variance)} paise fully explained by {len(attribution.verified_causes)} verified causal events.",
            )

        # Case 4: Partially Resolved
        if attribution.solver_status == "PARTIALLY_RESOLVED":
            return (
                "PARTIALLY_RESOLVED",
                EvidenceLevel.L3,
                f"Explained {attribution.explained_amount} paise; residual {attribution.unexplained_amount} paise escalated for review.",
            )

        # Case 5: Unexplained / Escalated
        return (
            "ESCALATE",
            EvidenceLevel.L0,
            f"Variance of {abs(variance)} paise has no valid supporting evidence in available dataset.",
        )

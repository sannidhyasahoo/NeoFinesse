from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from neofinesse.ai_investigation.investigator import AIEvidenceConstrainedInvestigator
from neofinesse.ai_investigation.llm_client import BaseLLMClient
from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.investigation.investigator import VarianceInvestigator
from neofinesse.investigation.models import InvestigationStatus
from neofinesse.models.ground_truth import CaseGroundTruth, ExpectedOutcome


class InvestigationComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    case_id: str
    settlement_id: str
    target_variance_inr: float
    expected_outcome: str
    phase5_outcome: str
    phase6_ai_recommendation: Optional[str]
    phase6_verified_outcome: str
    phase5_match: bool
    phase6_match: bool
    ai_helped: bool
    verifier_corrected_ai: bool
    conflicts_count: int
    missing_evidence_count: int
    phase5_latency_ms: float
    phase6_total_latency_ms: float
    phase6_llm_latency_ms: float
    phase6_verif_latency_ms: float


class PhaseComparisonSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_cases: int
    phase5_accuracy_pct: float
    phase6_accuracy_pct: float
    phase5_false_closures: int
    phase6_false_closures: int
    phase5_false_closure_rate_pct: float
    phase6_false_closure_rate_pct: float
    total_conflicts_surfaced: int
    total_missing_evidence_surfaced: int
    verifier_corrections_count: int
    ai_helped_count: int
    avg_phase5_latency_ms: float
    avg_phase6_latency_ms: float
    comparison_rows: List[InvestigationComparisonRow] = Field(default_factory=list)


class InvestigationComparator:
    """Performs side-by-side comparison between Phase 5 Deterministic Investigator and Phase 6 AI Investigator."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.phase5_investigator = VarianceInvestigator()
        self.phase6_investigator = AIEvidenceConstrainedInvestigator(llm_client=llm_client)

    def compare_cases(
        self, dataset: IngestedDataset, ground_truths: List[CaseGroundTruth]
    ) -> PhaseComparisonSummary:
        rows: List[InvestigationComparisonRow] = []

        p5_correct = 0
        p6_correct = 0
        p5_false_closures = 0
        p6_false_closures = 0
        total_conflicts = 0
        total_missing = 0
        verifier_corrections = 0
        ai_helped_count = 0
        p5_latencies: List[float] = []
        p6_latencies: List[float] = []

        for gt in ground_truths:
            target_var = (
                -(abs(gt.explained_amount) + abs(gt.unexplained_amount))
                if gt.expected_outcome == ExpectedOutcome.PARTIALLY_RESOLVED
                else gt.expected_variance
            )

            # 1. Run Phase 5 Deterministic Investigator
            p5_res = self.phase5_investigator.investigate(
                case_id=gt.case_id,
                settlement_id=gt.settlement_id,
                target_variance=target_var,
                dataset=dataset,
                scenario_id=gt.scenario.value,
            )
            p5_latencies.append(p5_res.investigation_latency_ms)

            # 2. Run Phase 6 AI Investigator
            p6_res = self.phase6_investigator.investigate(
                case_id=gt.case_id,
                settlement_id=gt.settlement_id,
                target_variance=target_var,
                dataset=dataset,
                scenario_id=gt.scenario.value,
            )
            p6_latencies.append(p6_res.total_latency_ms)

            # Match checking
            p5_match = (
                (gt.expected_outcome == ExpectedOutcome.RESOLVED and p5_res.final_status == InvestigationStatus.RESOLVED)
                or (gt.expected_outcome == ExpectedOutcome.PARTIALLY_RESOLVED and p5_res.final_status == InvestigationStatus.PARTIALLY_RESOLVED)
                or (gt.expected_outcome == ExpectedOutcome.VALID_DELAYED_CREDIT and p5_res.final_status == InvestigationStatus.VALID_DELAYED_CREDIT)
                or (gt.expected_outcome == ExpectedOutcome.ESCALATE and p5_res.final_status == InvestigationStatus.ESCALATE)
            )
            if p5_match:
                p5_correct += 1

            p6_match = (
                (gt.expected_outcome == ExpectedOutcome.RESOLVED and p6_res.final_status == InvestigationStatus.RESOLVED)
                or (gt.expected_outcome == ExpectedOutcome.PARTIALLY_RESOLVED and p6_res.final_status == InvestigationStatus.PARTIALLY_RESOLVED)
                or (gt.expected_outcome == ExpectedOutcome.VALID_DELAYED_CREDIT and p6_res.final_status == InvestigationStatus.VALID_DELAYED_CREDIT)
                or (gt.expected_outcome == ExpectedOutcome.ESCALATE and p6_res.final_status == InvestigationStatus.ESCALATE)
            )
            if p6_match:
                p6_correct += 1

            # Check false closure rates
            if gt.expected_outcome == ExpectedOutcome.ESCALATE:
                if p5_res.final_status == InvestigationStatus.RESOLVED:
                    p5_false_closures += 1
                if p6_res.final_status == InvestigationStatus.RESOLVED:
                    p6_false_closures += 1

            ai_rec = p6_res.ai_response.recommended_hypothesis_id if p6_res.ai_response else None
            conf_count = len(p6_res.conflicts_detected)
            miss_count = len(p6_res.missing_evidence_detected)
            total_conflicts += conf_count
            total_missing += miss_count

            if p6_res.verifier_corrected_ai:
                verifier_corrections += 1
            if p6_res.ai_helped:
                ai_helped_count += 1

            rows.append(
                InvestigationComparisonRow(
                    scenario_id=gt.scenario.value,
                    case_id=gt.case_id,
                    settlement_id=gt.settlement_id,
                    target_variance_inr=target_var / 100.0,
                    expected_outcome=gt.expected_outcome.value,
                    phase5_outcome=p5_res.final_status.value,
                    phase6_ai_recommendation=ai_rec,
                    phase6_verified_outcome=p6_res.final_status.value,
                    phase5_match=p5_match,
                    phase6_match=p6_match,
                    ai_helped=p6_res.ai_helped,
                    verifier_corrected_ai=p6_res.verifier_corrected_ai,
                    conflicts_count=conf_count,
                    missing_evidence_count=miss_count,
                    phase5_latency_ms=p5_res.investigation_latency_ms,
                    phase6_total_latency_ms=p6_res.total_latency_ms,
                    phase6_llm_latency_ms=p6_res.llm_latency_ms,
                    phase6_verif_latency_ms=p6_res.verification_latency_ms,
                )
            )

        n = len(ground_truths) if ground_truths else 1
        return PhaseComparisonSummary(
            total_cases=len(ground_truths),
            phase5_accuracy_pct=(p5_correct / n) * 100.0,
            phase6_accuracy_pct=(p6_correct / n) * 100.0,
            phase5_false_closures=p5_false_closures,
            phase6_false_closures=p6_false_closures,
            phase5_false_closure_rate_pct=(p5_false_closures / n) * 100.0,
            phase6_false_closure_rate_pct=(p6_false_closures / n) * 100.0,
            total_conflicts_surfaced=total_conflicts,
            total_missing_evidence_surfaced=total_missing,
            verifier_corrections_count=verifier_corrections,
            ai_helped_count=ai_helped_count,
            avg_phase5_latency_ms=sum(p5_latencies) / n if p5_latencies else 0.0,
            avg_phase6_latency_ms=sum(p6_latencies) / n if p6_latencies else 0.0,
            comparison_rows=rows,
        )

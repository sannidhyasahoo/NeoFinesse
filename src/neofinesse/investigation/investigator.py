import time
from typing import Optional

from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.investigation.audit import InvestigationAuditBuilder
from neofinesse.investigation.generator import HypothesisGenerator
from neofinesse.investigation.models import (
    HypothesisStatus,
    InvestigationResult,
    InvestigationStatus,
)
from neofinesse.investigation.scorer import HypothesisScorer
from neofinesse.investigation.verifier import HypothesisVerifier
from neofinesse.retrieval.base import InvestigationTaskCategory, RetrievalStrategy
from neofinesse.retrieval.direct_id import DirectIdRetrievalStrategy
from neofinesse.retrieval.evaluator import get_scenario_task_category
from neofinesse.retrieval.temporal import TemporalRelationshipRetrievalStrategy
from neofinesse.retrieval.upi_event import UPIEventRetrievalStrategy


class VarianceInvestigator:
    """Orchestrates deterministic financial investigation: retrieval -> hypotheses -> verification -> audit."""

    def __init__(self):
        self.temporal_retriever = TemporalRelationshipRetrievalStrategy()
        self.upi_retriever = UPIEventRetrievalStrategy()
        self.direct_id_retriever = DirectIdRetrievalStrategy()

    def investigate(
        self,
        case_id: str,
        settlement_id: str,
        target_variance: int,
        dataset: IngestedDataset,
        scenario_id: Optional[str] = None,
        task_category: Optional[InvestigationTaskCategory] = None,
    ) -> InvestigationResult:
        start_time = time.perf_counter()

        if task_category is None:
            if scenario_id:
                task_category = get_scenario_task_category(scenario_id)
            else:
                task_category = InvestigationTaskCategory.SETTLEMENT_RCA

        # 1. Select and invoke the strongest applicable Phase 4 retrieval strategy
        if task_category == InvestigationTaskCategory.UPI_STATE_INVESTIGATION:
            retrieval_res = self.upi_retriever.retrieve(
                case_id=case_id,
                settlement_id=settlement_id,
                target_variance=target_variance,
                dataset=dataset,
                task_category=task_category,
            )
        elif task_category == InvestigationTaskCategory.BANK_SETTLEMENT_STATE:
            retrieval_res = self.direct_id_retriever.retrieve(
                case_id=case_id,
                settlement_id=settlement_id,
                target_variance=target_variance,
                dataset=dataset,
                task_category=task_category,
            )
        else:
            # Settlement RCA: use Strategy 5 (TEMPORAL_RELATIONSHIP)
            retrieval_res = self.temporal_retriever.retrieve(
                case_id=case_id,
                settlement_id=settlement_id,
                target_variance=target_variance,
                dataset=dataset,
                task_category=task_category,
            )

        # 2. Generate candidate hypotheses
        raw_hypotheses = HypothesisGenerator.generate_hypotheses(
            case_id=case_id,
            target_variance=target_variance,
            retrieval_result=retrieval_res,
            task_category=task_category,
        )

        # 3. Verify all hypotheses against deterministic constraints
        verified_hypotheses = [
            HypothesisVerifier.verify(
                hypothesis=h,
                settlement_id=settlement_id,
                target_variance=target_variance,
                dataset=dataset,
            )
            for h in raw_hypotheses
        ]

        # 4. Rank surviving hypotheses
        ranked_hypotheses = HypothesisScorer.rank_hypotheses(verified_hypotheses, target_variance)
        winning_hypothesis = HypothesisScorer.select_winning_hypothesis(ranked_hypotheses)

        rejected_hypotheses = [
            h for h in ranked_hypotheses if h.status == HypothesisStatus.REJECTED
        ]

        # 5. Determine final investigation status
        if winning_hypothesis:
            explained = winning_hypothesis.explained_amount
            unexplained = winning_hypothesis.unexplained_amount

            if task_category == InvestigationTaskCategory.BANK_SETTLEMENT_STATE:
                final_status = InvestigationStatus.VALID_DELAYED_CREDIT
            elif winning_hypothesis.status == HypothesisStatus.VERIFIED:
                final_status = InvestigationStatus.RESOLVED
            else:
                final_status = InvestigationStatus.PARTIALLY_RESOLVED
        else:
            explained = 0
            unexplained = target_variance
            final_status = InvestigationStatus.ESCALATE

        # 6. Build audit record
        audit_record = InvestigationAuditBuilder.build_audit_record(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance=target_variance,
            final_status=final_status,
            winning_hypothesis=winning_hypothesis,
            rejected_hypotheses=rejected_hypotheses,
        )

        latency = (time.perf_counter() - start_time) * 1000.0

        return InvestigationResult(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance=target_variance,
            task_category=task_category,
            hypotheses=ranked_hypotheses,
            winning_hypothesis=winning_hypothesis,
            explained_amount=explained,
            unexplained_amount=unexplained,
            final_status=final_status,
            rejected_hypotheses=rejected_hypotheses,
            audit_record=audit_record,
            investigation_latency_ms=latency,
        )

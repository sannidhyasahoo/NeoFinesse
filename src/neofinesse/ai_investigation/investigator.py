import time
from typing import List, Optional

from neofinesse.ai_investigation.evidence_pack import EvidencePackBuilder
from neofinesse.ai_investigation.llm_client import BaseLLMClient, MockLLMClient
from neofinesse.ai_investigation.models import (
    AIInvestigationResponse,
    AIRejectionReason,
    ConflictItem,
    MissingEvidenceItem,
    VerifiedAIInvestigationResult,
)
from neofinesse.ai_investigation.parser import AIResponseParser
from neofinesse.ai_investigation.prompts import SYSTEM_PROMPT, build_user_prompt
from neofinesse.ai_investigation.validator import AIResponseValidator
from neofinesse.ai_investigation.verifier_bridge import AIVerifierBridge
from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.investigation.audit import InvestigationAuditBuilder
from neofinesse.investigation.models import CauseType, Hypothesis, HypothesisStatus, InvestigationStatus
from neofinesse.investigation.scorer import HypothesisScorer
from neofinesse.retrieval.base import InvestigationTaskCategory, RetrievalResult
from neofinesse.retrieval.evaluator import get_scenario_task_category
from neofinesse.retrieval.direct_id import DirectIdRetrievalStrategy
from neofinesse.retrieval.temporal import TemporalRelationshipRetrievalStrategy
from neofinesse.retrieval.upi_event import UPIEventRetrievalStrategy


class AIEvidenceConstrainedInvestigator:
    """End-to-end AI-driven, evidence-constrained, verifier-guarded financial investigator."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or MockLLMClient()
        self.temporal_retriever = TemporalRelationshipRetrievalStrategy()
        self.upi_retriever = UPIEventRetrievalStrategy()
        self.direct_id_retriever = DirectIdRetrievalStrategy()

    def investigate(
        self,
        case_id: str,
        settlement_id: str,
        target_variance: int,
        dataset: IngestedDataset,
        task_category: Optional[InvestigationTaskCategory] = None,
        scenario_id: Optional[str] = None,
    ) -> VerifiedAIInvestigationResult:
        total_start = time.perf_counter()

        # 1. Infer Task Category
        if task_category is None:
            if scenario_id:
                task_category = get_scenario_task_category(scenario_id)
            else:
                task_category = InvestigationTaskCategory.SETTLEMENT_RCA

        # 2. Phase 4 Evidence Retrieval
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
            retrieval_res = self.temporal_retriever.retrieve(
                case_id=case_id,
                settlement_id=settlement_id,
                target_variance=target_variance,
                dataset=dataset,
                task_category=task_category,
            )

        # 3. Build Evidence Pack
        pack = EvidencePackBuilder.build_pack(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance=target_variance,
            dataset=dataset,
            retrieval_result=retrieval_res,
            task_category=task_category,
        )

        user_prompt = build_user_prompt(pack)

        # 4. LLM Generation
        llm_start = time.perf_counter()
        raw_llm_text = self.llm_client.generate_investigation(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            evidence_pack=pack,
        )
        llm_latency = (time.perf_counter() - llm_start) * 1000.0

        # 5. Parse LLM Output
        ai_resp, parse_error = AIResponseParser.parse_response(raw_llm_text)
        all_rejections: List[AIRejectionReason] = []
        conflicts: List[ConflictItem] = []
        missing_evidence: List[MissingEvidenceItem] = []

        if parse_error or not ai_resp:
            all_rejections.append(
                AIRejectionReason(
                    hypothesis_id="GLOBAL_PARSE_FAILURE",
                    rejection_stage="SCHEMA_VALIDATION",
                    reasons=[parse_error or "Unknown parse error"],
                )
            )
            validated_ai_hypotheses = []
        else:
            # Collect conflicts & missing evidence from AI response
            for h in ai_resp.hypotheses:
                conflicts.extend(h.conflicts)
                missing_evidence.extend(h.missing_evidence)

            # 6. Validate Evidence IDs & Recalculate Arithmetic
            validated_ai_hypotheses, val_rejections = AIResponseValidator.validate_hypotheses(ai_resp, pack)
            all_rejections.extend(val_rejections)

        # 7. Bridge & Execute Phase 5 Deterministic Verification
        verif_start = time.perf_counter()
        verified_hypotheses, verif_rejections = AIVerifierBridge.verify_ai_hypotheses(
            ai_hypotheses=validated_ai_hypotheses,
            pack=pack,
            retrieval_result=retrieval_res,
            settlement_id=settlement_id,
            target_variance=target_variance,
            dataset=dataset,
        )
        all_rejections.extend(verif_rejections)
        verif_latency = (time.perf_counter() - verif_start) * 1000.0

        # 8. Score & Select Winning Hypothesis
        ranked_hypotheses = HypothesisScorer.rank_hypotheses(verified_hypotheses, target_variance)
        winning_hypothesis = HypothesisScorer.select_winning_hypothesis(ranked_hypotheses)

        # 9. Determine Final Outcome
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

        # 10. Check AI Helpfulness and Verifier Correction
        ai_recommended_id = ai_resp.recommended_hypothesis_id if ai_resp else None
        ai_helped = False
        verifier_corrected_ai = False

        if ai_recommended_id:
            if not winning_hypothesis:
                # AI recommended resolution, but verifier rejected it and escalated -> Verifier saved from false closure!
                verifier_corrected_ai = True
            elif winning_hypothesis.hypothesis_id != ai_recommended_id:
                # Verifier chose a different, strictly valid hypothesis
                verifier_corrected_ai = True
            else:
                ai_helped = True
        elif ai_resp and ai_resp.recommended_hypothesis_id is None and final_status == InvestigationStatus.ESCALATE:
            # AI correctly identified escalation requirement
            ai_helped = True

        # Check if AI surfaced non-empty conflicts or missing evidence
        if conflicts or missing_evidence:
            ai_helped = True

        # 11. Build Audit Record
        rejected_hypotheses = [h for h in verified_hypotheses if h != winning_hypothesis]
        audit_rec = InvestigationAuditBuilder.build_audit_record(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance=target_variance,
            final_status=final_status,
            winning_hypothesis=winning_hypothesis,
            rejected_hypotheses=rejected_hypotheses,
        )

        total_latency = (time.perf_counter() - total_start) * 1000.0

        return VerifiedAIInvestigationResult(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance=target_variance,
            ai_raw_response=raw_llm_text,
            ai_response=ai_resp,
            validated_hypotheses=verified_hypotheses,
            rejected_ai_hypotheses=all_rejections,
            winning_hypothesis=winning_hypothesis,
            final_status=final_status,
            explained_amount=explained,
            unexplained_amount=unexplained,
            audit_record=audit_rec,
            ai_helped=ai_helped,
            verifier_corrected_ai=verifier_corrected_ai,
            conflicts_detected=conflicts,
            missing_evidence_detected=missing_evidence,
            llm_latency_ms=llm_latency,
            verification_latency_ms=verif_latency,
            total_latency_ms=total_latency,
        )

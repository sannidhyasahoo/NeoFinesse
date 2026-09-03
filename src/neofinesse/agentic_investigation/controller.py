import time
from typing import Dict, List, Optional

from neofinesse.agentic_investigation.audit import AgenticAuditBuilder
from neofinesse.agentic_investigation.evidence_manager import AgentEvidenceManager
from neofinesse.agentic_investigation.models import (
    AgentInvestigationStatus,
    AgentRoundResponse,
    AgenticInvestigationResult,
    InvestigationBudget,
    ToolRequest,
    ToolResult,
)
from neofinesse.agentic_investigation.parser import AgentResponseParser
from neofinesse.agentic_investigation.planner import BaseAgentPlanner, MockAgentPlanner
from neofinesse.agentic_investigation.prompts import AGENTIC_SYSTEM_PROMPT, build_agentic_round_prompt
from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.agentic_investigation.tool_registry import ToolRegistry
from neofinesse.agentic_investigation.tool_validator import ToolRequestValidator
from neofinesse.agentic_investigation.validator import AgentResponseValidator
from neofinesse.ingestion.pipeline import IngestedDataset
from neofinesse.investigation.models import Hypothesis, HypothesisStatus, InvestigationStatus
from neofinesse.investigation.scorer import HypothesisScorer
from neofinesse.investigation.verifier import HypothesisVerifier
from neofinesse.retrieval.base import InvestigationTaskCategory, RetrievalResult
from neofinesse.retrieval.direct_id import DirectIdRetrievalStrategy
from neofinesse.retrieval.evaluator import get_scenario_task_category
from neofinesse.retrieval.temporal import TemporalRelationshipRetrievalStrategy
from neofinesse.retrieval.upi_event import UPIEventRetrievalStrategy


class AgenticInvestigationController:
    """Orchestrates multi-round adaptive evidence investigation with strict deterministic verification."""

    def __init__(
        self,
        planner: Optional[BaseAgentPlanner] = None,
        registry: Optional[ToolRegistry] = None,
        budget: Optional[InvestigationBudget] = None,
    ):
        self.planner = planner or MockAgentPlanner()
        self.registry = registry or ToolRegistry()
        self.default_budget = budget or InvestigationBudget()

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
        budget: Optional[InvestigationBudget] = None,
    ) -> AgenticInvestigationResult:
        start_time = time.perf_counter()
        active_budget = budget or self.default_budget

        # 1. Infer Task Category
        if task_category is None:
            if scenario_id:
                task_category = get_scenario_task_category(scenario_id)
            else:
                task_category = InvestigationTaskCategory.SETTLEMENT_RCA

        # 2. Initialize State
        state = InvestigationState(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance=target_variance,
            task_category=task_category.value,
            round_number=1,
        )

        # 3. Phase 4 Initial Retrieval
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

        # 4. Seed Initial Evidence
        AgentEvidenceManager.initialize_evidence(
            state=state,
            dataset=dataset,
            retrieval_result=retrieval_res,
            task_category=task_category,
        )

        tool_descs = self.registry.get_all_tool_descriptions()
        winning_hypothesis: Optional[Hypothesis] = None
        final_status = InvestigationStatus.ESCALATE
        budget_exhausted = False
        revisions_count = 0
        all_verified_hypotheses: List[Hypothesis] = []

        # 5. Multi-Round Investigation Loop
        for round_num in range(1, active_budget.max_investigation_rounds + 1):
            state.round_number = round_num

            # Build round evidence pack
            pack = AgentEvidenceManager.build_round_evidence_pack(state, dataset)
            round_prompt = build_agentic_round_prompt(state, pack, tool_descs)

            # LLM Planner
            raw_planner_text = self.planner.plan_round(
                system_prompt=AGENTIC_SYSTEM_PROMPT,
                user_prompt=round_prompt,
                state=state,
                pack=pack,
            )

            # Parse response
            agent_resp, parse_error = AgentResponseParser.parse_response(raw_planner_text)
            if parse_error or not agent_resp:
                state.record_round_snapshot(
                    round_number=round_num,
                    agent_response=None,
                    tool_requests=[],
                    tool_results=[],
                    verified_hypotheses=[],
                    rejected_reasons=[{"stage": "PARSE_ERROR", "error": parse_error}],
                )
                final_status = InvestigationStatus.ESCALATE
                break

            # Check conflicts & missing evidence
            if agent_resp.conflicts:
                state.conflicts.extend(agent_resp.conflicts)
                revisions_count += 1
            if agent_resp.missing_evidence:
                state.missing_evidence.extend(agent_resp.missing_evidence)

            # Validate hypotheses & arithmetic
            bridged_hypotheses, val_rejections = AgentResponseValidator.validate_and_bridge_hypotheses(
                response=agent_resp,
                state=state,
            )

            # --- BRANCH A: AGENT REQUESTS TOOLS (NEEDS_EVIDENCE) ---
            if agent_resp.status == AgentInvestigationStatus.NEEDS_EVIDENCE:
                executed_requests: List[ToolRequest] = []
                round_tool_results: List[ToolResult] = []

                for req in agent_resp.investigation_requests:
                    is_valid, val_err = ToolRequestValidator.validate_request(
                        request=req,
                        registry=self.registry,
                        state=state,
                        budget=active_budget,
                    )

                    if not is_valid:
                        res = ToolResult(
                            request_id=req.request_id,
                            tool=req.tool,
                            success=False,
                            output={},
                            evidence_items=[],
                            error=val_err,
                        )
                    else:
                        next_idx = len(state.current_evidence) + len(round_tool_results) + 1
                        res = self.registry.execute_tool(
                            request=req,
                            dataset=dataset,
                            next_ev_idx=next_idx,
                        )
                        state.completed_requests.append(req)
                        executed_requests.append(req)

                    state.tool_results.append(res)
                    round_tool_results.append(res)

                # Merge new evidence into state
                AgentEvidenceManager.merge_tool_evidence(state, round_tool_results)

                # Snapshot round
                state.record_round_snapshot(
                    round_number=round_num,
                    agent_response=agent_resp,
                    tool_requests=executed_requests,
                    tool_results=round_tool_results,
                    verified_hypotheses=[],
                    rejected_reasons=val_rejections,
                )

                # Continue to next round
                continue

            # --- BRANCH B: AGENT PROPOSES RESOLUTION (SUFFICIENT) ---
            if agent_resp.status == AgentInvestigationStatus.SUFFICIENT:
                verified_round_hypotheses: List[Hypothesis] = []
                round_rejections: List[Dict[str, Any]] = list(val_rejections)

                for bh in bridged_hypotheses:
                    verified_hyp = HypothesisVerifier.verify(
                        hypothesis=bh,
                        settlement_id=settlement_id,
                        target_variance=target_variance,
                        dataset=dataset,
                    )

                    if verified_hyp.status in (HypothesisStatus.VERIFIED, HypothesisStatus.PARTIALLY_VERIFIED):
                        verified_round_hypotheses.append(verified_hyp)
                        all_verified_hypotheses.append(verified_hyp)
                    else:
                        round_rejections.append(
                            {
                                "hypothesis_id": bh.hypothesis_id,
                                "stage": "PHASE5_CONSTRAINTS",
                                "results": [cr.model_dump() for cr in verified_hyp.constraint_results],
                            }
                        )

                # Score & Rank
                ranked = HypothesisScorer.rank_hypotheses(verified_round_hypotheses, target_variance)
                winner = HypothesisScorer.select_winning_hypothesis(ranked)

                if winner:
                    winning_hypothesis = winner
                    if task_category == InvestigationTaskCategory.BANK_SETTLEMENT_STATE:
                        final_status = InvestigationStatus.VALID_DELAYED_CREDIT
                    elif winner.status == HypothesisStatus.VERIFIED:
                        final_status = InvestigationStatus.RESOLVED
                    else:
                        final_status = InvestigationStatus.PARTIALLY_RESOLVED

                    state.winning_hypothesis = winner
                    state.final_status = final_status

                    state.record_round_snapshot(
                        round_number=round_num,
                        agent_response=agent_resp,
                        tool_requests=[],
                        tool_results=[],
                        verified_hypotheses=verified_round_hypotheses,
                        rejected_reasons=round_rejections,
                    )
                    break
                else:
                    # Hypotheses failed constraints
                    state.record_round_snapshot(
                        round_number=round_num,
                        agent_response=agent_resp,
                        tool_requests=[],
                        tool_results=[],
                        verified_hypotheses=verified_round_hypotheses,
                        rejected_reasons=round_rejections,
                    )
                    # If rounds remain, continue; otherwise escalate
                    continue

            # --- BRANCH C: ESCALATION (ESCALATE) ---
            if agent_resp.status == AgentInvestigationStatus.ESCALATE:
                final_status = InvestigationStatus.ESCALATE
                state.final_status = final_status
                state.record_round_snapshot(
                    round_number=round_num,
                    agent_response=agent_resp,
                    tool_requests=[],
                    tool_results=[],
                    verified_hypotheses=[],
                    rejected_reasons=val_rejections,
                )
                break

        # 6. Check Budget Exhaustion
        if final_status == InvestigationStatus.ESCALATE and not winning_hypothesis:
            if len(state.rounds) >= active_budget.max_investigation_rounds:
                budget_exhausted = True

        # 7. Final Accounting
        if winning_hypothesis:
            explained = winning_hypothesis.explained_amount
            unexplained = winning_hypothesis.unexplained_amount
        else:
            explained = 0
            unexplained = target_variance

        # 8. Build Full Audit Record
        rejected_hyps = [h for h in all_verified_hypotheses if h != winning_hypothesis]
        audit_rec = AgenticAuditBuilder.build_agentic_audit_record(
            state=state,
            winning_hypothesis=winning_hypothesis,
            final_status=final_status,
            explained_amount=explained,
            unexplained_amount=unexplained,
            rejected_hypotheses=rejected_hyps,
        )

        latency = (time.perf_counter() - start_time) * 1000.0

        return AgenticInvestigationResult(
            case_id=case_id,
            settlement_id=settlement_id,
            target_variance=target_variance,
            final_status=final_status,
            winning_hypothesis=winning_hypothesis,
            explained_amount=explained,
            unexplained_amount=unexplained,
            total_rounds=state.round_number,
            total_tool_calls=len(state.completed_requests),
            total_evidence_collected=len(state.current_evidence),
            budget_exhausted=budget_exhausted,
            revisions_count=revisions_count,
            audit_record=audit_rec,
            state_snapshot=state.model_dump(mode="json"),
            investigation_latency_ms=latency,
        )

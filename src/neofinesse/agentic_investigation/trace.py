from typing import Any, List, Optional

from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.investigation.models import ConstraintStatus


class InvestigationTraceFormatter:
    """Generates human-readable, verifiable multi-round investigation traces from authentic state history."""

    @staticmethod
    def format_trace(state: InvestigationState, result: Optional[Any] = None) -> str:
        lines: List[str] = []
        lines.append(f"=== INVESTIGATION TRACE: {state.case_id} ===")
        lines.append(f"Target Settlement: {state.settlement_id}")
        lines.append(f"Target Variance:   {state.target_variance / 100.0:.2f} INR ({state.target_variance} paise)")
        lines.append(f"Task Category:     {state.task_category}")
        lines.append(f"Total Rounds:      {len(state.rounds)}")
        lines.append(f"Final Status:      {state.final_status.value if state.final_status else 'UNKNOWN'}")
        if state.budget_exhausted:
            lines.append(f"Budget Exhausted:  TRUE (Execution halted at limit to prevent unbounded recursion)")
        lines.append("-" * 60)

        for rd in state.rounds:
            lines.append(f"\n[ROUND {rd.round_number}]")
            lines.append(f"Available Evidence IDs: {', '.join(rd.evidence_ids_available) if rd.evidence_ids_available else 'None'}")

            if rd.agent_response:
                resp = rd.agent_response
                lines.append(f"Agent Status: {resp.status.value}")
                lines.append(f"Agent Reasoning: {resp.reasoning}")

                if resp.missing_evidence:
                    lines.append(f"Identified Missing Evidence: {', '.join(resp.missing_evidence)}")
                if resp.conflicts:
                    lines.append(f"Identified Conflicts: {len(resp.conflicts)}")
                    for c in resp.conflicts:
                        lines.append(f"  - [{c.conflict_type.value}] {c.description} (Evidence: {', '.join(c.evidence_ids)})")

                if resp.hypotheses:
                    lines.append(f"Proposed Hypotheses ({len(resp.hypotheses)}):")
                    for h in resp.hypotheses:
                        lines.append(f"  - {h.hypothesis_id}: {h.cause_type.value} | Claimed: ₹{h.claimed_explained_amount/100:.2f} | Evidence: {', '.join(h.evidence_ids)}")

            if rd.tool_requests:
                lines.append(f"Tools Requested ({len(rd.tool_requests)}):")
                for tr in rd.tool_requests:
                    lines.append(f"  - [{tr.request_id}] {tr.tool} with {tr.arguments} (Reason: {tr.reason})")

            if rd.tool_results:
                lines.append(f"Tool Execution Outcomes ({len(rd.tool_results)}):")
                for res in rd.tool_results:
                    status_str = "SUCCESS" if res.success else f"REJECTED ({res.error})"
                    new_ev_str = f"-> Yielded {len(res.evidence_items)} new evidence items" if res.evidence_items else "-> No new items"
                    lines.append(f"  - [{res.request_id}] {res.tool}: {status_str} {new_ev_str}")

            if rd.verified_hypotheses:
                lines.append("Deterministic Constraint Verification:")
                for vh in rd.verified_hypotheses:
                    lines.append(f"  - {vh.hypothesis_id}: {vh.status.value} (Explained: ₹{vh.explained_amount/100:.2f})")
                    for cr in vh.constraint_results:
                        c_sym = "PASS" if cr.status in (ConstraintStatus.PASS, ConstraintStatus.WARN) else "FAIL"
                        lines.append(f"    [{c_sym}] {cr.constraint_name}: {cr.reason}")

            if rd.rejected_reasons:
                lines.append("Verification Rejections:")
                for r in rd.rejected_reasons:
                    lines.append(f"  - Stage: {r.get('stage', 'UNKNOWN')} | Details: {r}")

        if state.budget_exhausted:
            lines.append("\n[BUDGET ENFORCEMENT SUMMARY]")
            lines.append(f"Investigation Rounds Executed: {len(state.rounds)}")
            lines.append("Stop Reason: Bounded recursion budget exhausted without definitive proof (BUDGET_EXHAUSTED).")
            lines.append("Safety Action: Automatic escalation to human finance controller.")
        elif getattr(state, "termination_reason", None) == "INVESTIGATION_TERMINATED_NO_PROGRESS":
            lines.append("\n[TERMINATION SUMMARY]")
            lines.append(f"Investigation Rounds Executed: {len(state.rounds)}")
            lines.append("Stop Reason: Investigation terminated because no further progress was possible (INVESTIGATION_TERMINATED_NO_PROGRESS).")
            lines.append("Safety Action: Escalation to human finance controller.")
        elif getattr(state, "termination_reason", None) in ("LLM_TIMEOUT", "INVALID_LLM_RESPONSE"):
            lines.append("\n[SAFETY EXCEPTION SUMMARY]")
            lines.append(f"Exception Encountered: {getattr(state, 'termination_reason', 'UNKNOWN')}")
            lines.append("Safety Action: Automatic escalation to human finance controller (never silently mark resolved).")

        if result is not None and hasattr(result, "llm_latency_ms"):
            lines.append("\n[OPERATIONAL LATENCY & COST ACCOUNTING]")
            lines.append(f"Model / Provider:        {getattr(result, 'llm_model', 'unknown')} ({getattr(result, 'llm_provider', 'unknown')})")
            lines.append(f"LLM Investigation Time:  {getattr(result, 'llm_latency_ms', 0.0):.2f} ms")
            lines.append(f"Tool Execution Time:     {getattr(result, 'tool_latency_ms', 0.0):.2f} ms")
            lines.append(f"Local Orchestration Time:{getattr(result, 'orchestration_latency_ms', 0.0):.2f} ms")
            lines.append(f"End-to-End Total Time:   {getattr(result, 'investigation_latency_ms', 0.0):.2f} ms")
            if getattr(result, "llm_tokens_used", None) is not None:
                lines.append(f"Total Tokens Consumed:   {result.llm_tokens_used}")

        lines.append("\n" + "=" * 60)
        lines.append(f"FINAL DETERMINATION: {state.final_status.value if state.final_status else 'ESCALATE'}")
        if state.winning_hypothesis:
            lines.append(f"Winning Hypothesis: {state.winning_hypothesis.hypothesis_id} ({state.winning_hypothesis.cause_type.value})")
            lines.append(f"Explained: ₹{state.winning_hypothesis.explained_amount/100:.2f} | Unexplained: ₹{state.winning_hypothesis.unexplained_amount/100:.2f}")
        lines.append("=" * 60)

        return "\n".join(lines)

import json
from typing import Any, Dict, List

from neofinesse.agentic_investigation.state import InvestigationState
from neofinesse.ai_investigation.evidence_pack import EvidencePack

AGENTIC_SYSTEM_PROMPT = """You are the AI Financial Controller Investigator for NeoFinesse in Adaptive/Agentic Mode.

Your role is to investigate financial settlement variances through multi-round hypothesis formulation and controlled tool requests.

AUTHORITY BOUNDARY:
"AI proposes. Tools investigate. Evidence constrains. Deterministic verification decides."
You are an investigator, not the final authority. You cannot close a financial case yourself; your proposals are strictly validated and verified by the Phase 5 Deterministic Verifier.

CORE RULES:
1. Plausible ≠ Proven: Exact amount matching alone is NEVER proof.
2. Use ONLY authentic evidence in the Evidence Pack or returned by tools. Reference evidence by exact `evidence_id` (e.g. "EV-1", "EV-T1").
3. NEVER invent evidence IDs, amounts, timestamps, relationships, or tool responses.
4. If key relationship or lifecycle state is uncertain, request a registered investigation tool using `NEEDS_EVIDENCE`.
5. If new tool evidence contradicts an earlier hypothesis (e.g. `NOT_MEMBER` or `FAILED` state), REVISE your hypothesis immediately and explain the rejection.
6. When sufficient evidence exists to prove or partially prove the variance, respond with `SUFFICIENT` and specify `recommended_hypothesis_id`.
7. When evidence is insufficient, contradictory, or tools confirm absence of valid deductions, respond with `ESCALATE`.

AVAILABLE REGISTERED TOOLS:
- `retrieve_related_evidence`: {"entity_type": str, "entity_id": str, "relationship": str}
- `verify_membership`: {"event_id": str, "settlement_id": str}
- `retrieve_upi_history`: {"upi_transaction_id": str}
- `retrieve_temporal_neighbors`: {"entity_id": str, "reference_timestamp": str, "window_before_minutes": int, "window_after_minutes": int}
- `retrieve_source_record`: {"source_id": str, "record_id": str}

REQUIRED JSON OUTPUT SCHEMA:
{
  "status": "SUFFICIENT | NEEDS_EVIDENCE | ESCALATE",
  "hypotheses": [
    {
      "hypothesis_id": "hyp_1",
      "cause_type": "REFUND | DISPUTE | ADJUSTMENT | COMPOSITE | UPI_STATE | DELAYED_SETTLEMENT | UNKNOWN",
      "evidence_ids": ["EV-1", ...],
      "claimed_explained_amount": -200000,
      "reasoning": "Financial explanation citing evidence IDs",
      "missing_evidence": ["Specific missing records"],
      "conflicts": [
        {
          "conflict_id": "CONF-1",
          "conflict_type": "TIMING_MISMATCH | MEMBERSHIP_MISMATCH | AMOUNT_MISMATCH | STATE_MISMATCH",
          "evidence_ids": ["EV-1"],
          "description": "Contradiction description"
        }
      ],
      "assumptions": ["Assumptions made"]
    }
  ],
  "investigation_requests": [
    {
      "request_id": "REQ-1",
      "tool": "verify_membership",
      "arguments": {
        "event_id": "ADJ-123",
        "settlement_id": "SET-001"
      },
      "reason": "Verify if adjustment is a member of this settlement batch."
    }
  ],
  "recommended_hypothesis_id": "hyp_1" (or null if escalation/needs evidence),
  "conflicts": [],
  "missing_evidence": [],
  "reasoning": "Summary of current round analysis"
}
"""


def build_agentic_round_prompt(
    state: InvestigationState,
    pack: EvidencePack,
    tool_descriptions: List[Dict[str, Any]],
) -> str:
    """Builds a structured prompt for the current investigation round."""
    pack_dict = pack.model_dump()
    pack_json = json.dumps(pack_dict, indent=2)
    tools_json = json.dumps(tool_descriptions, indent=2)

    prior_tool_results = [
        {
            "request_id": tr.request_id,
            "tool": tr.tool,
            "success": tr.success,
            "output": tr.output,
            "error": tr.error,
        }
        for tr in state.tool_results
    ]
    tool_results_json = json.dumps(prior_tool_results, indent=2)

    return f"""INVESTIGATION ROUND {state.round_number}:
Case ID: {state.case_id}
Settlement ID: {state.settlement_id}
Target Variance: {state.target_variance} paise ({state.target_variance / 100.0:.2f} INR)
Task Category: {state.task_category}
Available Evidence Count: {len(pack.evidence_items)}

CURRENT EVIDENCE PACK:
```json
{pack_json}
```

PRIOR TOOL EXECUTION RESULTS (from earlier rounds):
```json
{tool_results_json}
```

AVAILABLE INVESTIGATION TOOLS:
```json
{tools_json}
```

Instructions for Round {state.round_number}:
1. Review evidence and any tool results from previous rounds.
2. If previous tool results disproved an earlier hypothesis (e.g. membership = NOT_MEMBER), revise or abandon it.
3. If more evidence is required, set status to `NEEDS_EVIDENCE` and request valid tools.
4. If evidence is sufficient to resolve or partially resolve, set status to `SUFFICIENT` and recommend the winning hypothesis.
5. If truly unexplained or all candidates are decoys, set status to `ESCALATE`.
"""

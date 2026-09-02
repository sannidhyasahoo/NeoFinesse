from pathlib import Path
import pytest

from neofinesse.ai_investigation.benchmark import AIBenchmarkRunner
from neofinesse.ai_investigation.evidence_pack import EvidenceItem, EvidencePack, EvidencePackBuilder
from neofinesse.ai_investigation.investigator import AIEvidenceConstrainedInvestigator
from neofinesse.ai_investigation.llm_client import MockLLMClient, MockMode
from neofinesse.ai_investigation.models import (
    AIHypothesis,
    AIInvestigationResponse,
    ConflictItem,
    ConflictType,
    MissingEvidenceCriticality,
    MissingEvidenceItem,
)
from neofinesse.ai_investigation.parser import AIResponseParser
from neofinesse.ai_investigation.validator import AIResponseValidator
from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.exporter import DataExporter
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.ingestion.pipeline import IngestionPipeline
from neofinesse.investigation.models import CauseType, InvestigationStatus
from neofinesse.retrieval.base import EvidenceCandidate, InvestigationTaskCategory, RetrievalResult, RetrievalStrategy


@pytest.fixture(scope="module")
def ai_test_env(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("phase6_env")
    data_dir = temp_dir / "data"
    gt_dir = temp_dir / "ground_truth"
    exp_dir = temp_dir / "experiments"

    config = GeneratorConfig(
        seed=42,
        num_orders=80,
        num_payments=80,
        num_settlements=8,
        num_refunds=10,
        num_disputes=5,
        num_adjustments=5,
        num_transfers=3,
        output_dir=str(data_dir),
        ground_truth_dir=str(gt_dir),
    )

    world = FinancialDataGenerator(config).generate()
    exporter = DataExporter(world, config)
    export_meta = exporter.export_all()

    pipeline = IngestionPipeline(data_dir=str(data_dir))
    dataset = pipeline.run()

    return {
        "dataset": dataset,
        "gt_path": export_meta["ground_truth_path"],
        "exp_dir": str(exp_dir),
        "data_dir": str(data_dir),
    }


# ==========================================
# 1. Parser & Schema Validation Tests
# ==========================================

def test_parser_extracts_markdown_json():
    raw_markdown = """
    Here is my financial analysis:
    ```json
    {
      "case_id": "CASE-100",
      "hypotheses": [
        {
          "hypothesis_id": "hyp_1",
          "cause_type": "REFUND",
          "evidence_ids": ["EV-1"],
          "claimed_explained_amount": -5000,
          "reasoning": "Standard refund deducted from batch.",
          "missing_evidence": [],
          "conflicts": [],
          "assumptions": []
        }
      ],
      "recommended_hypothesis_id": "hyp_1",
      "investigation_summary": "Case resolved by refund.",
      "confidence_assessment": "HIGH"
    }
    ```
    """
    resp, err = AIResponseParser.parse_response(raw_markdown)
    assert err is None
    assert resp is not None
    assert resp.case_id == "CASE-100"
    assert len(resp.hypotheses) == 1
    assert resp.hypotheses[0].claimed_explained_amount == -5000


def test_parser_handles_malformed_json_gracefully():
    malformed = "This is not json at all."
    resp, err = AIResponseParser.parse_response(malformed)
    assert resp is None
    assert "JSON syntax error" in err


# ==========================================
# 2. Hallucination & Arithmetic Validator Tests
# ==========================================

def test_validator_rejects_hallucinated_evidence_id():
    ev_item = EvidenceItem(
        evidence_id="EV-1",
        candidate_id="c1",
        entity_id="rfnd_1",
        entity_type="refund",
        amount_paise=200000,
        amount_inr=2000.0,
        net_financial_effect_paise=-200000,
        net_financial_effect_inr=-2000.0,
        relationship_path="Settlement -> Line -> Refund",
        source_id="SRC-1",
        source_file="refunds.csv",
        source_row=10,
        source_hash="hash1",
        record_hash="hash2",
    )
    pack = EvidencePack(
        case_id="CASE-001",
        settlement_id="setl_1",
        target_variance_paise=-200000,
        target_variance_inr=-2000.0,
        task_category="SETTLEMENT_RCA",
        evidence_items=[ev_item],
        total_evidence_count=1,
    )

    # Hypothesis referencing non-existent EV-999
    bad_hyp = AIHypothesis(
        hypothesis_id="hyp_bad",
        cause_type=CauseType.REFUND,
        evidence_ids=["EV-999"],
        claimed_explained_amount=-200000,
        reasoning="Hallucinated ID",
    )
    resp = AIInvestigationResponse(
        case_id="CASE-001",
        hypotheses=[bad_hyp],
        recommended_hypothesis_id="hyp_bad",
        investigation_summary="Summary",
    )

    validated, rejections = AIResponseValidator.validate_hypotheses(resp, pack)
    assert len(validated) == 0
    assert len(rejections) == 1
    assert rejections[0].rejection_stage == "HALLUCINATION_CHECK"
    assert "EV-999" in rejections[0].reasons[0]


def test_validator_recalculates_arithmetic_independently():
    ev_item = EvidenceItem(
        evidence_id="EV-1",
        candidate_id="c1",
        entity_id="rfnd_1",
        entity_type="refund",
        amount_paise=300000,
        amount_inr=3000.0,
        net_financial_effect_paise=-300000,
        net_financial_effect_inr=-3000.0,
        relationship_path="Settlement -> Line -> Refund",
        source_id="SRC-1",
        source_file="refunds.csv",
        source_row=10,
        source_hash="hash1",
        record_hash="hash2",
    )
    pack = EvidencePack(
        case_id="CASE-001",
        settlement_id="setl_1",
        target_variance_paise=-300000,
        target_variance_inr=-3000.0,
        task_category="SETTLEMENT_RCA",
        evidence_items=[ev_item],
        total_evidence_count=1,
    )

    # LLM incorrectly claims -100000 paise
    hyp = AIHypothesis(
        hypothesis_id="hyp_wrong_math",
        cause_type=CauseType.REFUND,
        evidence_ids=["EV-1"],
        claimed_explained_amount=-100000,
        reasoning="Bad math",
    )
    resp = AIInvestigationResponse(
        case_id="CASE-001",
        hypotheses=[hyp],
        recommended_hypothesis_id="hyp_wrong_math",
        investigation_summary="Summary",
    )

    validated, rejections = AIResponseValidator.validate_hypotheses(resp, pack)
    assert len(validated) == 1
    # Recalculated amount must be the authentic -300,000 paise
    assert validated[0].recalculated_explained_amount == -300000
    assert any("Arithmetic corrected" in a for a in validated[0].assumptions)


# ==========================================
# 3. Conflict & Missing Evidence Tests
# ==========================================

def test_conflict_and_missing_evidence_surfacing():
    conf = ConflictItem(
        conflict_id="CONF-1",
        conflict_type=ConflictType.MEMBERSHIP_MISMATCH,
        evidence_ids=["EV-2"],
        description="Decoy belongs to another batch.",
    )
    miss = MissingEvidenceItem(
        missing_id="MISS-1",
        entity_type="refund",
        criticality=MissingEvidenceCriticality.HIGH,
        description="Missing pre-cutoff deduction event.",
    )
    hyp = AIHypothesis(
        hypothesis_id="hyp_conflict",
        cause_type=CauseType.REFUND,
        evidence_ids=[],
        claimed_explained_amount=0,
        reasoning="No valid candidates",
        conflicts=[conf],
        missing_evidence=[miss],
    )
    assert hyp.conflicts[0].conflict_type == ConflictType.MEMBERSHIP_MISMATCH
    assert hyp.missing_evidence[0].criticality == MissingEvidenceCriticality.HIGH


# ==========================================
# 4. Verifier Safety: Unsupported Closure Blocked
# ==========================================

def test_unsupported_closure_attempt_blocked_by_verifier(ai_test_env):
    """Safety Test: If AI hallucinates or attempts unsupported closure on decoy, deterministic verifier forces ESCALATE."""
    dataset = ai_test_env["dataset"]

    # Use MockLLMClient in UNSUPPORTED_CLOSURE mode
    mock_client = MockLLMClient(mode=MockMode.UNSUPPORTED_CLOSURE)
    investigator = AIEvidenceConstrainedInvestigator(llm_client=mock_client)

    target_setl = next(s for s in dataset.settlements if "scen_008" in s.id)
    res = investigator.investigate(
        case_id="CASE-008",
        settlement_id=target_setl.id,
        target_variance=400000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    # Verifier MUST block closure and force ESCALATE
    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None
    assert res.verifier_corrected_ai is True


# ==========================================
# 5. AI Adversarial Scenarios (AI-001 - AI-008)
# ==========================================

def test_ai_001_conflicting_evidence_handled(ai_test_env):
    """AI-001: Surfacing contradictory evidence in VAR-002 same-amount decoy."""
    dataset = ai_test_env["dataset"]
    investigator = AIEvidenceConstrainedInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_002" in s.id)
    res = investigator.investigate(
        case_id="CASE-002",
        settlement_id=target_setl.id,
        target_variance=-250000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.winning_hypothesis is not None
    assert len(res.conflicts_detected) >= 1
    assert res.conflicts_detected[0].conflict_type == ConflictType.MEMBERSHIP_MISMATCH


def test_ai_003_partial_explanation_with_missing_evidence(ai_test_env):
    """AI-003: Identifying partial explanation and explicitly surfacing missing residual deduction."""
    dataset = ai_test_env["dataset"]
    investigator = AIEvidenceConstrainedInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_003" in s.id)
    res = investigator.investigate(
        case_id="CASE-003",
        settlement_id=target_setl.id,
        target_variance=-500000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.PARTIALLY_RESOLVED
    assert len(res.missing_evidence_detected) >= 1
    assert res.missing_evidence_detected[0].entity_type == "adjustment"


def test_ai_006_composite_explanation_verified(ai_test_env):
    """AI-006: AI synthesizes composite multi-event subset and passes Phase 5 verifier."""
    dataset = ai_test_env["dataset"]
    investigator = AIEvidenceConstrainedInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_004" in s.id)
    res = investigator.investigate(
        case_id="CASE-004",
        settlement_id=target_setl.id,
        target_variance=-100000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.RESOLVED
    assert res.winning_hypothesis is not None
    assert res.winning_hypothesis.cause_type == CauseType.COMPOSITE
    assert res.explained_amount == -100000


def test_ai_008_unexplained_variance_escalated(ai_test_env):
    """AI-008: Genuinely unexplained variance with no deduction records escalated safely."""
    dataset = ai_test_env["dataset"]
    investigator = AIEvidenceConstrainedInvestigator()

    target_setl = next(s for s in dataset.settlements if "scen_010" in s.id)
    res = investigator.investigate(
        case_id="CASE-010",
        settlement_id=target_setl.id,
        target_variance=-1500000,
        dataset=dataset,
        task_category=InvestigationTaskCategory.SETTLEMENT_RCA,
    )

    assert res.final_status == InvestigationStatus.ESCALATE
    assert res.winning_hypothesis is None
    assert len(res.missing_evidence_detected) >= 1


# ==========================================
# 6. Full Benchmark & Comparison Test
# ==========================================

def test_phase6_benchmark_and_comparison_scorecard(ai_test_env):
    """Full Benchmark: Phase 5 vs Phase 6 comparative evaluation produces 100% accuracy, 0% false closures."""
    dataset = ai_test_env["dataset"]
    gt_path = ai_test_env["gt_path"]
    exp_dir = ai_test_env["exp_dir"]

    runner = AIBenchmarkRunner()
    summary = runner.run_benchmark(dataset, gt_path, export_dir=exp_dir)

    assert summary.total_cases == 10
    assert summary.phase5_accuracy_pct == 100.0
    assert summary.phase6_accuracy_pct == 100.0
    assert summary.phase5_false_closures == 0
    assert summary.phase6_false_closures == 0
    assert summary.phase5_false_closure_rate_pct == 0.0
    assert summary.phase6_false_closure_rate_pct == 0.0
    assert summary.total_conflicts_surfaced > 0
    assert summary.total_missing_evidence_surfaced > 0
    assert summary.ai_helped_count > 0

    assert (Path(exp_dir) / "results.json").exists()
    assert (Path(exp_dir) / "results.csv").exists()

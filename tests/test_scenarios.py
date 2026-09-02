from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.models.ground_truth import ExpectedOutcome, ScenarioType


def test_all_10_failure_scenarios_generated():
    """Test 7: Ground truth correctly registers all 10 failure injection scenarios."""
    config = GeneratorConfig(seed=42, num_orders=100, num_settlements=10)
    world = FinancialDataGenerator(config).generate()

    assert len(world.ground_truths) == 10

    scenarios = [gt.scenario for gt in world.ground_truths]
    expected_scenarios = [
        ScenarioType.REFUND_VARIANCE,
        ScenarioType.SAME_AMOUNT_DECOY,
        ScenarioType.PARTIAL_EXPLANATION,
        ScenarioType.MULTIPLE_EVENT_EXPLANATION,
        ScenarioType.UPI_LATE_SUCCESS,
        ScenarioType.UPI_DEBIT_REVERSAL,
        ScenarioType.DELAYED_BANK_CREDIT,
        ScenarioType.WRONG_DATE_DECOY,
        ScenarioType.WRONG_PAYMENT_DECOY,
        ScenarioType.COMPLETELY_UNEXPLAINED,
    ]

    for esc in expected_scenarios:
        assert esc in scenarios, f"Missing scenario {esc}"


def test_ground_truth_scenario_outcomes():
    """Test scenario specific outcomes and cause attributions."""
    config = GeneratorConfig(seed=42, num_orders=100, num_settlements=10)
    world = FinancialDataGenerator(config).generate()
    gt_map = {gt.scenario: gt for gt in world.ground_truths}

    # VAR-001: Refund variance -> RESOLVED
    gt1 = gt_map[ScenarioType.REFUND_VARIANCE]
    assert gt1.expected_outcome == ExpectedOutcome.RESOLVED
    assert len(gt1.true_causes) == 1
    assert gt1.true_causes[0].entity_type == "refund"

    # VAR-002: Same amount decoy -> RESOLVED (with decoy rejection reason)
    gt2 = gt_map[ScenarioType.SAME_AMOUNT_DECOY]
    assert gt2.expected_outcome == ExpectedOutcome.RESOLVED
    assert len(gt2.decoys) == 1
    assert gt2.decoys[0].decoy_type == "same_amount"

    # VAR-003: Partial explanation -> PARTIALLY_RESOLVED
    gt3 = gt_map[ScenarioType.PARTIAL_EXPLANATION]
    assert gt3.expected_outcome == ExpectedOutcome.PARTIALLY_RESOLVED
    assert gt3.explained_amount > 0
    assert gt3.unexplained_amount > 0

    # VAR-004: Multiple event -> RESOLVED (joint causes)
    gt4 = gt_map[ScenarioType.MULTIPLE_EVENT_EXPLANATION]
    assert gt4.expected_outcome == ExpectedOutcome.RESOLVED
    assert len(gt4.true_causes) == 2

    # VAR-005: UPI late success -> RESOLVED
    gt5 = gt_map[ScenarioType.UPI_LATE_SUCCESS]
    assert gt5.expected_outcome == ExpectedOutcome.RESOLVED

    # VAR-007: Delayed bank credit -> VALID_DELAYED_CREDIT
    gt7 = gt_map[ScenarioType.DELAYED_BANK_CREDIT]
    assert gt7.expected_outcome == ExpectedOutcome.VALID_DELAYED_CREDIT

    # VAR-008: Wrong date decoy -> ESCALATE
    gt8 = gt_map[ScenarioType.WRONG_DATE_DECOY]
    assert gt8.expected_outcome == ExpectedOutcome.ESCALATE

    # VAR-009: Wrong payment decoy -> ESCALATE
    gt9 = gt_map[ScenarioType.WRONG_PAYMENT_DECOY]
    assert gt9.expected_outcome == ExpectedOutcome.ESCALATE

    # VAR-010: Completely unexplained -> ESCALATE
    gt10 = gt_map[ScenarioType.COMPLETELY_UNEXPLAINED]
    assert gt10.expected_outcome == ExpectedOutcome.ESCALATE
    assert len(gt10.true_causes) == 0

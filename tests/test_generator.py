from datetime import datetime
import pytest

from neofinesse.generator.config import GeneratorConfig
from neofinesse.generator.synthetic import FinancialDataGenerator
from neofinesse.models.base import NormalizedObservedStatus, SourceEventType


def test_generator_reproducibility():
    """Test 1: Same seed produces identical, reproducible data."""
    config1 = GeneratorConfig(seed=42, num_orders=50, num_settlements=5)
    config2 = GeneratorConfig(seed=42, num_orders=50, num_settlements=5)

    world1 = FinancialDataGenerator(config1).generate()
    world2 = FinancialDataGenerator(config2).generate()

    assert len(world1.orders) == len(world2.orders)
    assert len(world1.payments) == len(world2.payments)
    assert len(world1.settlement_lines) == len(world2.settlement_lines)
    assert len(world1.settlements) == len(world2.settlements)

    # Check identical IDs and amounts
    for o1, o2 in zip(world1.orders, world2.orders):
        assert o1.id == o2.id
        assert o1.amount == o2.amount

    for s1, s2 in zip(world1.settlements, world2.settlements):
        assert s1.id == s2.id
        assert s1.amount == s2.amount
        assert s1.utr == s2.utr


def test_unique_entity_ids():
    """Test 2: Generated IDs are valid and unique across sets."""
    config = GeneratorConfig(seed=123, num_orders=60, num_settlements=6)
    world = FinancialDataGenerator(config).generate()

    order_ids = [o.id for o in world.orders]
    assert len(order_ids) == len(set(order_ids))

    pay_ids = [p.id for p in world.payments]
    assert len(pay_ids) == len(set(pay_ids))

    line_ids = [l.settlement_line_id for l in world.settlement_lines]
    assert len(line_ids) == len(set(line_ids))

    setl_ids = [s.id for s in world.settlements]
    assert len(setl_ids) == len(set(setl_ids))


def test_relationship_internal_consistency():
    """Test 3: Entity relationships are internally consistent."""
    config = GeneratorConfig(seed=77, num_orders=80, num_settlements=8)
    world = FinancialDataGenerator(config).generate()

    order_map = {o.id: o for o in world.orders}
    pay_map = {p.id: p for p in world.payments}
    setl_map = {s.id: s for s in world.settlements}

    # Every payment with order_id references a valid order
    for p in world.payments:
        if p.order_id:
            assert p.order_id in order_map

    # Every refund references a valid payment
    for r in world.refunds:
        assert r.payment_id in pay_map

    # Every dispute references a valid payment
    for d in world.disputes:
        assert d.payment_id in pay_map

    # Every settlement line references a valid settlement
    for l in world.settlement_lines:
        assert l.settlement_id in setl_map


def test_settlement_line_sum_equals_expected_amount():
    """Test 4 & 5: Expected settlement amount equals exact sum of signed SettlementLines."""
    config = GeneratorConfig(seed=99, num_orders=100, num_settlements=10)
    world = FinancialDataGenerator(config).generate()

    lines_by_setl = {}
    for l in world.settlement_lines:
        lines_by_setl.setdefault(l.settlement_id, []).append(l)

    for s in world.settlements:
        batch_lines = lines_by_setl.get(s.id, [])
        computed_expected = sum(line.net_amount for line in batch_lines)
        assert s.expected_amount == computed_expected, f"Settlement {s.id} expected amount mismatch"


def test_upi_event_ordering():
    """Test 6: UPI state history events are chronologically ordered."""
    config = GeneratorConfig(seed=55, num_orders=50)
    world = FinancialDataGenerator(config).generate()

    events_by_upi = {}
    for e in world.upi_events:
        events_by_upi.setdefault(e.upi_transaction_id, []).append(e)

    for upi_id, events in events_by_upi.items():
        assert len(events) >= 1
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp

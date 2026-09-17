"""Tests for edge cases specified in Section 3.4 of the specification."""

import pytest
from src.loader import load_deliveries
from src.models import Delivery
from src.planner import RoutePlanner


def test_edge_case_empty_deliveries() -> None:
    """Empty input should produce an empty plan with 0 trips and not raise errors."""
    planner = RoutePlanner(max_capacity=10.0)
    plan = planner.plan([])
    assert len(plan.trips) == 0
    assert len(plan.undeliverable) == 0
    assert plan.metrics is not None
    assert plan.metrics.total_trips == 0
    assert plan.metrics.delivered_count == 0


def test_edge_case_overweight_package() -> None:
    """Packages exceeding vehicle capacity must be segregated into undeliverable."""
    planner = RoutePlanner(max_capacity=10.0)
    deliveries = [
        Delivery(id="NORMAL-1", area="Dokki", priority=1, weight=5.0),
        Delivery(id="OVERWEIGHT-1", area="Dokki", priority=1, weight=12.5),
        Delivery(id="NORMAL-2", area="Dokki", priority=2, weight=4.0),
    ]
    plan = planner.plan(deliveries)

    # Overweight item should be quarantined
    assert len(plan.undeliverable) == 1
    assert plan.undeliverable[0].id == "OVERWEIGHT-1"
    assert "exceeds maximum vehicle capacity" in plan.undeliverable[0].reason

    # Normal items should be scheduled in a trip
    assert len(plan.trips) == 1
    assert plan.trips[0].total_weight == 9.0
    assert [d.id for d in plan.trips[0].deliveries] == ["NORMAL-1", "NORMAL-2"]


def test_edge_case_same_priority_ties() -> None:
    """Multiple deliveries having the same priority should be handled deterministically."""
    planner = RoutePlanner(max_capacity=10.0)
    deliveries = [
        Delivery(id="A", area="Giza", priority=1, weight=3.0),
        Delivery(id="B", area="Giza", priority=1, weight=4.0),
        Delivery(id="C", area="Giza", priority=1, weight=2.0),
    ]
    plan = planner.plan(deliveries)

    # All fit into one trip of 9.0 kg
    assert len(plan.trips) == 1
    assert plan.trips[0].total_weight == 9.0
    assert len(plan.trips[0].deliveries) == 3


def test_edge_case_capacity_saturation_and_overflow() -> None:
    """Adding next package would exceed capacity: must start a new trip."""
    planner = RoutePlanner(max_capacity=10.0)
    # Total weight = 6.0 + 5.0 + 3.0 = 14.0 kg > 10.0 kg in Heliopolis
    deliveries = [
        Delivery(id=1, area="Heliopolis", priority=1, weight=6.0),
        Delivery(id=2, area="Heliopolis", priority=1, weight=5.0),
        Delivery(id=3, area="Heliopolis", priority=2, weight=3.0),
    ]
    plan = planner.plan(deliveries)

    # Must be split into 2 trips
    assert len(plan.trips) == 2
    for trip in plan.trips:
        assert trip.total_weight <= 10.0
        assert trip.areas == ["Heliopolis"]

    # Package 1 (6kg) + Package 3 (3kg) = 9kg in Trip 1
    # Package 2 (5kg) in Trip 2
    total_delivered = sum(t.total_weight for t in plan.trips)
    assert total_delivered == 14.0


def test_edge_case_exact_capacity_boundary() -> None:
    """Package with exact capacity (10.0 kg) must fit exactly."""
    planner = RoutePlanner(max_capacity=10.0)
    deliveries = [
        Delivery(id="EXACT-10", area="Tagamoa", priority=1, weight=10.0),
        Delivery(id="EXTRA-2", area="Tagamoa", priority=2, weight=2.0),
    ]
    plan = planner.plan(deliveries)

    assert len(plan.trips) == 2
    assert plan.trips[0].total_weight == 10.0
    assert plan.trips[0].utilization_rate == 100.0
    assert plan.trips[1].total_weight == 2.0


def test_edge_case_floating_point_precision() -> None:
    """Ensure floating point additions do not cause premature capacity rejection."""
    planner = RoutePlanner(max_capacity=10.0)
    deliveries = [
        Delivery(id=1, area="Maadi", priority=1, weight=3.3),
        Delivery(id=2, area="Maadi", priority=1, weight=3.3),
        Delivery(id=3, area="Maadi", priority=1, weight=3.4),
    ]
    # 3.3 + 3.3 + 3.4 == 10.0 exactly
    plan = planner.plan(deliveries)

    assert len(plan.trips) == 1
    assert plan.trips[0].total_weight == 10.0
    assert plan.trips[0].utilization_rate == 100.0


def test_edge_cases_file_integration() -> None:
    """Test full integration with the edge_cases.csv file."""
    loader_res = load_deliveries("data/edge_cases.csv")
    planner = RoutePlanner(max_capacity=10.0)
    plan = planner.plan(loader_res.deliveries, loader_res.rejected_items)

    assert len(plan.undeliverable) == 1
    assert plan.undeliverable[0].id in (101, "101")
    assert len(plan.trips) == 4
    for trip in plan.trips:
        assert trip.total_weight <= 10.0

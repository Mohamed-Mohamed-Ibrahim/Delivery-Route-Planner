"""Unit tests for domain models."""

import pytest
from src.models import Delivery, PlanMetrics, RoutePlan, Trip, UndeliverableItem


def test_delivery_creation_and_validation() -> None:
    d = Delivery(id=1, area="Maadi", priority=1, weight=2.5)
    assert d.id == 1
    assert d.area == "Maadi"
    assert d.priority == 1
    assert d.weight == 2.5
    assert d.to_dict() == {"id": 1, "area": "Maadi", "priority": 1, "weight": 2.5}


def test_delivery_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="Delivery ID cannot be empty"):
        Delivery(id=" ", area="Maadi", priority=1, weight=2.0)

    with pytest.raises(ValueError, match="Area cannot be empty"):
        Delivery(id=1, area="", priority=1, weight=2.0)

    with pytest.raises(ValueError, match="Priority must be a positive integer"):
        Delivery(id=1, area="Maadi", priority=0, weight=2.0)

    with pytest.raises(ValueError, match="Package weight must be greater than 0"):
        Delivery(id=1, area="Maadi", priority=1, weight=-1.0)


def test_trip_capacity_and_utilization() -> None:
    trip = Trip(trip_id=1, max_capacity=10.0)
    assert trip.total_weight == 0.0
    assert trip.remaining_capacity == 10.0
    assert trip.utilization_rate == 0.0
    assert trip.stops_count == 0

    d1 = Delivery(id=1, area="Maadi", priority=2, weight=4.0)
    trip.add_delivery(d1)
    assert trip.total_weight == 4.0
    assert trip.remaining_capacity == 6.0
    assert trip.utilization_rate == 40.0
    assert trip.highest_priority == 2

    d2 = Delivery(id=2, area="Maadi", priority=1, weight=3.5)
    trip.add_delivery(d2)
    assert trip.total_weight == 7.5
    assert trip.remaining_capacity == 2.5
    assert trip.utilization_rate == 75.0
    assert trip.highest_priority == 1


def test_trip_capacity_exceeded() -> None:
    trip = Trip(trip_id=1, max_capacity=10.0)
    d1 = Delivery(id=1, area="Maadi", priority=1, weight=7.0)
    trip.add_delivery(d1)

    d2 = Delivery(id=2, area="Maadi", priority=1, weight=4.0)
    assert not trip.can_fit(d2)
    with pytest.raises(ValueError, match="exceeds capacity"):
        trip.add_delivery(d2)


def test_trip_max_stops_constraint() -> None:
    trip = Trip(trip_id=1, max_capacity=10.0)
    d1 = Delivery(id=1, area="Maadi", priority=1, weight=1.0)
    d2 = Delivery(id=2, area="Maadi", priority=2, weight=1.0)
    d3 = Delivery(id=3, area="Maadi", priority=3, weight=1.0)

    assert trip.can_fit(d1, max_stops=2)
    trip.add_delivery(d1, max_stops=2)
    assert trip.can_fit(d2, max_stops=2)
    trip.add_delivery(d2, max_stops=2)

    assert not trip.can_fit(d3, max_stops=2)
    with pytest.raises(ValueError, match="exceeds capacity"):
        trip.add_delivery(d3, max_stops=2)


def test_undeliverable_item_dict() -> None:
    item = UndeliverableItem(id="X1", area="Dokki", priority=1, weight=15.0, reason="Too heavy")
    d = item.to_dict()
    assert d["id"] == "X1"
    assert d["weight"] == 15.0
    assert d["reason"] == "Too heavy"


def test_plan_metrics_and_route_plan_dict() -> None:
    metrics = PlanMetrics(
        total_deliveries=1,
        delivered_count=1,
        undelivered_count=0,
        total_trips=1,
        total_weight_delivered=3.0,
        average_utilization_pct=30.0,
        area_trip_counts={"Maadi": 1},
        priority_counts={1: 1},
    )
    trip = Trip(trip_id=1, max_capacity=10.0)
    trip.add_delivery(Delivery(id=1, area="Maadi", priority=1, weight=3.0))
    plan = RoutePlan(trips=[trip], undeliverable=[], metrics=metrics)

    data = plan.to_dict()
    assert len(data["trips"]) == 1
    assert data["metrics"]["total_weight_delivered"] == 3.0

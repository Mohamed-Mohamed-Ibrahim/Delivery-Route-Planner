"""Unit tests for RoutePlanner core algorithmic logic."""

import pytest
from src.loader import load_deliveries
from src.models import Delivery
from src.planner import RoutePlanner


def test_planner_sample_deliveries_pdf_requirements() -> None:
    loader_result = load_deliveries("data/sample_deliveries.csv")
    planner = RoutePlanner(max_capacity=10.0)
    plan = planner.plan(loader_result.deliveries)

    # 1. Total trips check: exactly 3 trips formed
    assert len(plan.trips) == 3
    assert len(plan.undeliverable) == 0
    assert plan.metrics is not None
    assert plan.metrics.delivered_count == 5

    # 2. Capacity invariant check: no trip exceeds 10.0 kg
    for trip in plan.trips:
        assert trip.total_weight <= 10.0
        assert trip.total_weight > 0

    # 3. Area grouping check: deliveries going to the same area are grouped together
    for trip in plan.trips:
        assert len(trip.areas) == 1  # each trip serves exactly one primary area

    # Map areas to their assigned packages
    area_deliveries = {trip.areas[0]: [str(d.id) for d in trip.deliveries] for trip in plan.trips}
    assert set(area_deliveries["Maadi"]) == {"2", "5"}
    assert set(area_deliveries["Nasr City"]) == {"1", "3"}
    assert set(area_deliveries["Zamalek"]) == {"4"}

    # 4. Priority ordering check:
    # Lower priority numbers represent more urgent deliveries and should be dispatched first
    # Trip 1 and Trip 2 must contain Priority 1 packages; Trip 3 must be Priority 2/3
    assert plan.trips[0].highest_priority == 1
    assert plan.trips[1].highest_priority == 1
    assert plan.trips[2].highest_priority == 2

    # Inside Trip 2 (Maadi), ID 2 (Priority 1) should be scheduled before ID 5 (Priority 2)
    maadi_trip = [t for t in plan.trips if "Maadi" in t.areas][0]
    assert maadi_trip.deliveries[0].id in (2, "2")
    assert maadi_trip.deliveries[1].id in (5, "5")

    # 5. Complete assignment check: Every delivery appears in exactly one trip
    assigned_ids = [str(d.id) for trip in plan.trips for d in trip.deliveries]
    assert sorted(assigned_ids) == ["1", "2", "3", "4", "5"]


def test_planner_with_max_stops() -> None:
    # 4 packages for Maadi, each 1.0 kg
    deliveries = [
        Delivery(id=f"M{i}", area="Maadi", priority=1, weight=1.0)
        for i in range(1, 5)
    ]
    planner = RoutePlanner(max_capacity=10.0, max_stops=2)
    plan = planner.plan(deliveries)

    # Even though total weight is 4.0 kg <= 10 kg, max 2 stops per trip forces 2 trips
    assert len(plan.trips) == 2
    for trip in plan.trips:
        assert trip.stops_count <= 2


def test_planner_allow_multi_area() -> None:
    # 3 small packages in 3 different areas
    deliveries = [
        Delivery(id=1, area="Maadi", priority=1, weight=2.0),
        Delivery(id=2, area="Dokki", priority=2, weight=2.0),
        Delivery(id=3, area="Zamalek", priority=3, weight=2.0),
    ]
    # By default, single area grouping creates 3 trips
    planner_single = RoutePlanner(max_capacity=10.0, allow_multi_area=False)
    plan_single = planner_single.plan(deliveries)
    assert len(plan_single.trips) == 3

    # With allow_multi_area=True, they consolidate into 1 trip of 6.0 kg
    planner_multi = RoutePlanner(max_capacity=10.0, allow_multi_area=True)
    plan_multi = planner_multi.plan(deliveries)
    assert len(plan_multi.trips) == 1
    assert plan_multi.trips[0].total_weight == 6.0
    assert len(plan_multi.trips[0].areas) == 3

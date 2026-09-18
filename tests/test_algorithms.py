"""Unit tests for the Strategy Design Pattern and algorithm versions (v1 vs v3)."""

import pytest
from src.algorithms import (
    DEFAULT_ALGORITHM,
    STRATEGY_REGISTRY,
    BasePlannerStrategy,
    MinHeapPlannerV3,
    PriorityGreedyPlannerV1,
    get_strategy,
)
from src.models import Delivery, PlanMetrics, Trip
from src.planner import RoutePlanner
from main import run


def test_strategy_factory_and_defaults() -> None:
    """Verify that get_strategy returns expected strategy instances and handles defaults."""
    assert DEFAULT_ALGORITHM == "v3_minheap"

    # Default strategy
    default_strat = get_strategy()
    assert isinstance(default_strat, MinHeapPlannerV3)
    assert default_strat.algorithm_name == "v3_minheap"

    # Explicit v1
    v1_strat = get_strategy("v1_priority_greedy")
    assert isinstance(v1_strat, PriorityGreedyPlannerV1)
    assert v1_strat.algorithm_name == "v1_priority_greedy"

    # Explicit v3
    v3_strat = get_strategy("v3_minheap")
    assert isinstance(v3_strat, MinHeapPlannerV3)
    assert v3_strat.algorithm_name == "v3_minheap"

    # Alias lookups
    assert isinstance(get_strategy("v1"), PriorityGreedyPlannerV1)
    assert isinstance(get_strategy("greedy"), PriorityGreedyPlannerV1)
    assert isinstance(get_strategy("v3"), MinHeapPlannerV3)
    assert isinstance(get_strategy("minheap"), MinHeapPlannerV3)
    assert isinstance(get_strategy("v3_heap"), MinHeapPlannerV3)
    assert isinstance(get_strategy("heap"), MinHeapPlannerV3)

    # Unknown strategy
    with pytest.raises(ValueError, match="Unknown algorithm 'unsupported'"):
        get_strategy("unsupported")


def test_plan_metrics_algorithm_version_argument() -> None:
    """Verify PlanMetrics algorithm_version argument defaults to v3_minheap and accepts custom."""
    # 1. Default should be v3_minheap
    metrics_default = PlanMetrics(
        total_deliveries=5,
        delivered_count=5,
        undelivered_count=0,
        total_trips=3,
        total_weight_delivered=18.2,
        average_utilization_pct=60.7,
        area_trip_counts={"Maadi": 1},
        priority_counts={1: 2},
    )
    assert metrics_default.algorithm_version == "v3_minheap"
    assert metrics_default.to_dict()["algorithm_version"] == "v3_minheap"

    # 2. Explicit v1
    metrics_v1 = PlanMetrics(
        total_deliveries=5,
        delivered_count=5,
        undelivered_count=0,
        total_trips=3,
        total_weight_delivered=18.2,
        average_utilization_pct=60.7,
        area_trip_counts={"Maadi": 1},
        priority_counts={1: 2},
        algorithm_version="v1_priority_greedy",
    )
    assert metrics_v1.algorithm_version == "v1_priority_greedy"
    assert metrics_v1.to_dict()["algorithm_version"] == "v1_priority_greedy"


def test_route_planner_strategy_selection() -> None:
    """Verify RoutePlanner correctly switches between v3 and v1 strategies."""
    deliveries = [
        Delivery(id=1, area="Maadi", priority=1, weight=2.0),
        Delivery(id=2, area="Maadi", priority=2, weight=3.5),
    ]

    # Default planner uses v3
    planner_default = RoutePlanner()
    assert planner_default.algorithm_version == "v3_minheap"
    plan_default = planner_default.plan(deliveries)
    assert plan_default.metrics is not None
    assert plan_default.metrics.algorithm_version == "v3_minheap"

    # Explicit v1 planner
    planner_v1 = RoutePlanner(algorithm_version="v1_priority_greedy")
    assert planner_v1.algorithm_version == "v1_priority_greedy"
    plan_v1 = planner_v1.plan(deliveries)
    assert plan_v1.metrics is not None
    assert plan_v1.metrics.algorithm_version == "v1_priority_greedy"


def test_cli_algorithm_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI accepts --algorithm flag and outputs chosen algorithm version."""
    exit_code_v1 = run(["data/sample_deliveries.csv", "-a", "v1_greedy"])
    assert exit_code_v1 == 0
    out_v1 = capsys.readouterr().out
    assert "Algorithm Strategy      : v1_priority_greedy" in out_v1

    exit_code_v3 = run(["data/sample_deliveries.csv", "-a", "v3_minheap"])
    assert exit_code_v3 == 0
    out_v3 = capsys.readouterr().out
    assert "Algorithm Strategy      : v3_minheap" in out_v3

    exit_code_v3_alias = run(["data/sample_deliveries.csv", "-a", "minheap"])
    assert exit_code_v3_alias == 0
    out_v3_alias = capsys.readouterr().out
    assert "Algorithm Strategy      : v3_minheap" in out_v3_alias


def test_minheap_sample_deliveries() -> None:
    """Verify MinHeapPlannerV3 correctly schedules the Section 3.1 sample deliveries."""
    deliveries = [
        Delivery(id=1, area="Nasr City", priority=2, weight=4.5),
        Delivery(id=2, area="Maadi", priority=1, weight=2.0),
        Delivery(id=3, area="Nasr City", priority=3, weight=1.2),
        Delivery(id=4, area="Zamalek", priority=1, weight=7.0),
        Delivery(id=5, area="Maadi", priority=2, weight=3.5),
    ]
    planner = RoutePlanner(max_capacity=10.0, algorithm_version="v3_minheap")
    plan = planner.plan(deliveries)

    assert len(plan.trips) == 3
    assert plan.metrics is not None
    assert plan.metrics.delivered_count == 5
    assert plan.metrics.undelivered_count == 0
    assert plan.metrics.total_weight_delivered == 18.2
    assert plan.metrics.algorithm_version == "v3_minheap"

    # Verify dispatch order: highest priority packages depart first
    # Trip 1 and Trip 2 both have Priority 1 packages; Zamalek (7.0kg) > Maadi (5.5kg)
    assert plan.trips[0].highest_priority == 1
    assert plan.trips[0].areas == ["Zamalek"]
    assert plan.trips[1].highest_priority == 1
    assert plan.trips[1].areas == ["Maadi"]
    assert plan.trips[2].highest_priority == 2
    assert plan.trips[2].areas == ["Nasr City"]


def test_minheap_max_stops_constraint() -> None:
    """Verify MinHeapPlannerV3 strictly respects max_stops constraint."""
    deliveries = [
        Delivery(id=1, area="Maadi", priority=1, weight=1.0),
        Delivery(id=2, area="Maadi", priority=1, weight=1.0),
        Delivery(id=3, area="Maadi", priority=1, weight=1.0),
        Delivery(id=4, area="Maadi", priority=1, weight=1.0),
    ]
    planner = RoutePlanner(max_capacity=10.0, max_stops=2, algorithm_version="v3_minheap")
    plan = planner.plan(deliveries)

    assert len(plan.trips) == 2
    for trip in plan.trips:
        assert trip.stops_count <= 2


def test_minheap_multi_area() -> None:
    """Verify MinHeapPlannerV3 supports allow_multi_area filling."""
    deliveries = [
        Delivery(id=1, area="Maadi", priority=1, weight=6.0),
        Delivery(id=2, area="Dokki", priority=2, weight=3.0),
    ]
    # Without multi-area: 2 trips
    planner_single = RoutePlanner(max_capacity=10.0, allow_multi_area=False, algorithm_version="v3_minheap")
    plan_single = planner_single.plan(deliveries)
    assert len(plan_single.trips) == 2

    # With multi-area: 1 combined trip
    planner_multi = RoutePlanner(max_capacity=10.0, allow_multi_area=True, algorithm_version="v3_minheap")
    plan_multi = planner_multi.plan(deliveries)
    assert len(plan_multi.trips) == 1
    assert plan_multi.trips[0].total_weight == 9.0
    assert set(plan_multi.trips[0].areas) == {"Maadi", "Dokki"}


def test_minheap_empty_and_branch_coverage() -> None:
    """Verify MinHeapPlannerV3 handles empty inputs and edge cases."""
    strategy = MinHeapPlannerV3()
    assert strategy.plan_trips([]) == []

    # Multi-trip same area: 15kg in Maadi splits into 2 trips
    deliveries_heavy = [
        Delivery(id=1, area="Maadi", priority=1, weight=6.0),
        Delivery(id=2, area="Maadi", priority=2, weight=5.0),
        Delivery(id=3, area="Maadi", priority=3, weight=4.0),
    ]
    planner = RoutePlanner(max_capacity=10.0, algorithm_version="v3_minheap")
    plan = planner.plan(deliveries_heavy)
    assert len(plan.trips) == 2

    # Multi-area with max_stops and item that does not fit in other area
    deliveries_multi = [
        Delivery(id=1, area="Maadi", priority=1, weight=5.0),
        Delivery(id=2, area="Dokki", priority=2, weight=6.0),  # doesn't fit in Trip 1
        Delivery(id=3, area="Dokki", priority=3, weight=2.0),  # fits in Trip 1
        Delivery(id=4, area="Heliopolis", priority=1, weight=2.0),
    ]
    planner_multi_stops = RoutePlanner(
        max_capacity=10.0, max_stops=2, allow_multi_area=True, algorithm_version="v3_minheap"
    )
    plan_multi_stops = planner_multi_stops.plan(deliveries_multi)
    assert all(t.stops_count <= 2 for t in plan_multi_stops.trips)


def test_minheap_large_dataset_scaling() -> None:
    """Verify MinHeapPlannerV3 processes a larger dataset rapidly with all invariants intact."""
    deliveries = [
        Delivery(
            id=f"pkg_{i}",
            area=f"Zone_{i % 8}",
            priority=(i % 5) + 1,
            weight=round(((i * 7) % 50 + 10) / 10.0, 2),  # weights between 1.0 and 5.9 kg
        )
        for i in range(500)
    ]
    planner = RoutePlanner(max_capacity=10.0, algorithm_version="v3_minheap")
    plan = planner.plan(deliveries)

    assert plan.metrics is not None
    assert plan.metrics.delivered_count == 500
    assert plan.metrics.undelivered_count == 0
    # Invariant checks are executed inside planner.plan() automatically




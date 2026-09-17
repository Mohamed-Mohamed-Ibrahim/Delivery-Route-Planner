"""Unit tests for the Strategy Design Pattern and algorithm versions (v1 vs v2)."""

import pytest
from src.algorithms import (
    DEFAULT_ALGORITHM,
    STRATEGY_REGISTRY,
    BasePlannerStrategy,
    KnapsackPlannerV2,
    PriorityGreedyPlannerV1,
    get_strategy,
)
from src.models import Delivery, PlanMetrics, Trip
from src.planner import RoutePlanner
from main import run


def test_strategy_factory_and_defaults() -> None:
    """Verify that get_strategy returns expected strategy instances and handles defaults."""
    assert DEFAULT_ALGORITHM == "v2_knapsack"

    # Default strategy
    default_strat = get_strategy()
    assert isinstance(default_strat, KnapsackPlannerV2)
    assert default_strat.algorithm_name == "v2_knapsack"

    # Explicit v1
    v1_strat = get_strategy("v1_priority_greedy")
    assert isinstance(v1_strat, PriorityGreedyPlannerV1)
    assert v1_strat.algorithm_name == "v1_priority_greedy"

    # Alias lookups
    assert isinstance(get_strategy("v1"), PriorityGreedyPlannerV1)
    assert isinstance(get_strategy("greedy"), PriorityGreedyPlannerV1)
    assert isinstance(get_strategy("v2"), KnapsackPlannerV2)
    assert isinstance(get_strategy("knapsack"), KnapsackPlannerV2)

    # Unknown strategy
    with pytest.raises(ValueError, match="Unknown algorithm 'unsupported'"):
        get_strategy("unsupported")


def test_plan_metrics_algorithm_version_argument() -> None:
    """Verify PlanMetrics algorithm_version argument defaults to v2_knapsack and accepts custom."""
    # 1. Default should be v2_knapsack
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
    assert metrics_default.algorithm_version == "v2_knapsack"
    assert metrics_default.to_dict()["algorithm_version"] == "v2_knapsack"

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
    """Verify RoutePlanner correctly switches between v1 and v2 strategies."""
    deliveries = [
        Delivery(id=1, area="Maadi", priority=1, weight=2.0),
        Delivery(id=2, area="Maadi", priority=2, weight=3.5),
    ]

    # Default planner uses v2
    planner_default = RoutePlanner()
    assert planner_default.algorithm_version == "v2_knapsack"
    plan_v2 = planner_default.plan(deliveries)
    assert plan_v2.metrics is not None
    assert plan_v2.metrics.algorithm_version == "v2_knapsack"

    # Explicit v1 planner
    planner_v1 = RoutePlanner(algorithm_version="v1_priority_greedy")
    assert planner_v1.algorithm_version == "v1_priority_greedy"
    plan_v1 = planner_v1.plan(deliveries)
    assert plan_v1.metrics is not None
    assert plan_v1.metrics.algorithm_version == "v1_priority_greedy"


def test_knapsack_superior_packing_demonstration() -> None:
    """Test the classic bin packing scenario [6.0, 5.0, 5.0, 4.0] kg (all Priority 2).

    - Greedy First-Fit (v1) packs 6+4=10kg, leaving 5kg and 5kg in separate trips -> 3 trips.
    - 0/1 Knapsack DP (v2) pairs 5+5=10kg and 6+4=10kg -> 2 trips (optimal!).
    """
    deliveries = [
        Delivery(id="D1", area="Dokki", priority=2, weight=5.0),
        Delivery(id="D2", area="Dokki", priority=2, weight=4.0),
        Delivery(id="D3", area="Dokki", priority=2, weight=5.0),
        Delivery(id="D4", area="Dokki", priority=2, weight=6.0),
    ]

    # 1. Run v1 Greedy Planner
    planner_v1 = RoutePlanner(max_capacity=10.0, algorithm_version="v1_greedy")
    plan_v1 = planner_v1.plan(deliveries)

    # 2. Run v2 Knapsack Planner
    planner_v2 = RoutePlanner(max_capacity=10.0, algorithm_version="v2_knapsack")
    plan_v2 = planner_v2.plan(deliveries)

    # Knapsack achieves optimal 2 trips (100% vehicle utilization across both trips)
    assert len(plan_v2.trips) == 2
    assert plan_v2.trips[0].total_weight == 10.0
    assert plan_v2.trips[1].total_weight == 10.0
    assert plan_v2.metrics is not None
    assert plan_v2.metrics.average_utilization_pct == 100.0

    # In contrast, Greedy produces 3 trips due to lack of combinatorial lookahead
    assert len(plan_v1.trips) == 3


def test_cli_algorithm_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI accepts --algorithm flag and outputs chosen algorithm version."""
    exit_code_v1 = run(["data/sample_deliveries.csv", "-a", "v1_greedy"])
    assert exit_code_v1 == 0
    out_v1 = capsys.readouterr().out
    assert "Algorithm Strategy      : v1_priority_greedy" in out_v1

    exit_code_v2 = run(["data/sample_deliveries.csv", "--algorithm", "v2_knapsack"])
    assert exit_code_v2 == 0
    out_v2 = capsys.readouterr().out
    assert "Algorithm Strategy      : v2_knapsack" in out_v2

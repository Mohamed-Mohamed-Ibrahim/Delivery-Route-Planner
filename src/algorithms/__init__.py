"""Route planning algorithms package using the Strategy Design Pattern."""

from __future__ import annotations

from typing import Dict, Type

from src.algorithms.base import BasePlannerStrategy
from src.algorithms.v1_priority_greedy import PriorityGreedyPlannerV1
from src.algorithms.v2_knapsack import KnapsackPlannerV2
from src.algorithms.v3_minheap import MinHeapPlannerV3

DEFAULT_ALGORITHM: str = "v2_knapsack"

STRATEGY_REGISTRY: Dict[str, Type[BasePlannerStrategy]] = {
    "v1_priority_greedy": PriorityGreedyPlannerV1,
    "v1_greedy": PriorityGreedyPlannerV1,
    "v1": PriorityGreedyPlannerV1,
    "greedy": PriorityGreedyPlannerV1,
    "v2_knapsack": KnapsackPlannerV2,
    "v2": KnapsackPlannerV2,
    "knapsack": KnapsackPlannerV2,
    "v3_minheap": MinHeapPlannerV3,
    "v3_heap": MinHeapPlannerV3,
    "v3": MinHeapPlannerV3,
    "minheap": MinHeapPlannerV3,
    "heap": MinHeapPlannerV3,
}


def get_strategy(name: str | None = None) -> BasePlannerStrategy:
    """Factory to retrieve a strategy instance by name or return the default strategy."""
    key = (name or DEFAULT_ALGORITHM).strip().lower()
    strategy_cls = STRATEGY_REGISTRY.get(key)
    if strategy_cls is None:
        available = ", ".join(sorted(set(STRATEGY_REGISTRY.keys())))
        raise ValueError(f"Unknown algorithm '{name}'. Available strategies: {available}")
    return strategy_cls()


__all__ = [
    "BasePlannerStrategy",
    "PriorityGreedyPlannerV1",
    "KnapsackPlannerV2",
    "MinHeapPlannerV3",
    "DEFAULT_ALGORITHM",
    "STRATEGY_REGISTRY",
    "get_strategy",
]

"""Core route planning coordinator and Strategy Context."""

from __future__ import annotations

from typing import Dict, List, Optional

from src.algorithms import BasePlannerStrategy, get_strategy
from src.models import Delivery, PlanMetrics, RoutePlan, Trip, UndeliverableItem


class RoutePlanner:
    """Strategy Context coordinating delivery route planning, validation, and safety invariants."""

    def __init__(
        self,
        max_capacity: float = 10.0,
        max_stops: Optional[int] = None,
        allow_multi_area: int = 0,
        algorithm_version: Optional[str] = None,
    ) -> None:
        if max_capacity <= 0:
            raise ValueError(f"Vehicle capacity must be positive, got {max_capacity}")
        if max_stops is not None and max_stops < 1:
            raise ValueError(f"Max stops must be at least 1, got {max_stops}")

        self.max_capacity = max_capacity
        self.max_stops = max_stops
        self.allow_multi_area = max(0, allow_multi_area)
        self.strategy: BasePlannerStrategy = get_strategy(algorithm_version)
        self.algorithm_version: str = self.strategy.algorithm_name

    def plan(
        self,
        deliveries: List[Delivery],
        initial_undeliverable: Optional[List[UndeliverableItem]] = None,
    ) -> RoutePlan:
        """Generate an optimized route plan from a list of deliveries using the selected strategy."""
        undeliverable: List[UndeliverableItem] = list(initial_undeliverable or [])
        valid_deliveries: List[Delivery] = []

        # 1. Quarantine packages exceeding vehicle capacity
        for d in deliveries:
            if round(d.weight, 4) > self.max_capacity:
                undeliverable.append(
                    UndeliverableItem(
                        id=d.id,
                        area=d.area,
                        priority=d.priority,
                        weight=d.weight,
                        reason=(
                            f"Package weight ({d.weight} kg) exceeds "
                            f"maximum vehicle capacity ({self.max_capacity} kg)."
                        ),
                    )
                )
            else:
                valid_deliveries.append(d)

        # Handle empty case
        if not valid_deliveries:
            metrics = self._calculate_metrics(
                total_input=len(deliveries) + len(initial_undeliverable or []),
                trips=[],
                undeliverable=undeliverable,
                algorithm_version=self.algorithm_version,
            )
            return RoutePlan(trips=[], undeliverable=undeliverable, metrics=metrics)

        # 2. Delegate trip generation to the chosen algorithm strategy
        trips = self.strategy.plan_trips(
            deliveries=valid_deliveries,
            max_capacity=self.max_capacity,
            max_stops=self.max_stops,
            allow_multi_area=self.allow_multi_area,
        )

        # 3. Post-condition safety invariant verification
        self._verify_invariants(valid_deliveries, trips)

        # 4. Compute analytics metrics
        metrics = self._calculate_metrics(
            total_input=len(deliveries) + len(initial_undeliverable or []),
            trips=trips,
            undeliverable=undeliverable,
            algorithm_version=self.algorithm_version,
        )

        return RoutePlan(trips=trips, undeliverable=undeliverable, metrics=metrics)

    def _verify_invariants(self, valid_deliveries: List[Delivery], trips: List[Trip]) -> None:
        """Ensure all domain and safety invariants hold."""
        delivered_ids = []
        for t in trips:
            # Capacity check
            if t.total_weight > self.max_capacity + 1e-6:
                raise AssertionError(
                    f"Trip {t.trip_id} exceeds capacity: {t.total_weight} > {self.max_capacity}"
                )
            if self.max_stops is not None and t.stops_count > self.max_stops:
                raise AssertionError(
                    f"Trip {t.trip_id} exceeds max stops: {t.stops_count} > {self.max_stops}"
                )
            for d in t.deliveries:
                delivered_ids.append(d.id)

        # Complete assignment check
        expected_ids = {d.id for d in valid_deliveries}
        actual_ids = set(delivered_ids)
        if len(delivered_ids) != len(actual_ids):
            raise AssertionError("Duplicate delivery assignment detected across trips.")
        if expected_ids != actual_ids:
            missing = expected_ids - actual_ids
            raise AssertionError(f"Not all valid deliveries were assigned to trips. Missing: {missing}")

    def _calculate_metrics(
        self,
        total_input: int,
        trips: List[Trip],
        undeliverable: List[UndeliverableItem],
        algorithm_version: Optional[str] = None,
    ) -> PlanMetrics:
        """Calculate comprehensive route and fleet analytics."""
        delivered_count = sum(t.stops_count for t in trips)
        total_weight = round(sum(t.total_weight for t in trips), 4)

        if trips:
            avg_utilization = round(sum(t.utilization_rate for t in trips) / len(trips), 2)
        else:
            avg_utilization = 0.0

        area_counts: Dict[str, int] = {}
        for t in trips:
            for area in t.areas:
                area_counts[area] = area_counts.get(area, 0) + 1

        priority_counts: Dict[int, int] = {}
        for t in trips:
            for d in t.deliveries:
                priority_counts[d.priority] = priority_counts.get(d.priority, 0) + 1

        return PlanMetrics(
            total_deliveries=total_input,
            delivered_count=delivered_count,
            undelivered_count=len(undeliverable),
            total_trips=len(trips),
            total_weight_delivered=total_weight,
            average_utilization_pct=avg_utilization,
            area_trip_counts=area_counts,
            priority_counts=priority_counts,
            algorithm_version=algorithm_version or self.algorithm_version,
        )

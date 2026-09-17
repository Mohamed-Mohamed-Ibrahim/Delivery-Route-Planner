"""Core route planning algorithm and optimization logic."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from src.models import Delivery, PlanMetrics, RoutePlan, Trip, UndeliverableItem


class RoutePlanner:
    """Plans vehicle delivery trips adhering to capacity, urgency, and area clustering."""

    def __init__(
        self,
        max_capacity: float = 10.0,
        max_stops: Optional[int] = None,
        allow_multi_area: bool = False,
    ) -> None:
        if max_capacity <= 0:
            raise ValueError(f"Vehicle capacity must be positive, got {max_capacity}")
        if max_stops is not None and max_stops < 1:
            raise ValueError(f"Max stops must be at least 1, got {max_stops}")

        self.max_capacity = max_capacity
        self.max_stops = max_stops
        self.allow_multi_area = allow_multi_area

    def plan(
        self,
        deliveries: List[Delivery],
        initial_undeliverable: Optional[List[UndeliverableItem]] = None,
    ) -> RoutePlan:
        """Generate an optimized route plan from a list of deliveries."""
        undeliverable: List[UndeliverableItem] = list(initial_undeliverable or [])
        valid_deliveries: List[Delivery] = []

        # 1. Filter out packages exceeding vehicle capacity
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
            )
            return RoutePlan(trips=[], undeliverable=undeliverable, metrics=metrics)

        # 2. Organize remaining deliveries
        # We track unassigned deliveries using a list or pool
        unassigned = list(valid_deliveries)
        trips: List[Trip] = []
        trip_counter = 1

        # While unassigned deliveries remain:
        while unassigned:
            # Pick the most urgent delivery in the pending pool
            # Tie-breaking: (priority asc, str(id) asc)
            unassigned.sort(key=lambda d: (d.priority, str(d.id)))
            seed_delivery = unassigned[0]
            primary_area = seed_delivery.area

            # Create a new trip for this area
            current_trip = Trip(trip_id=trip_counter, max_capacity=self.max_capacity)
            current_trip.add_delivery(seed_delivery, max_stops=self.max_stops)
            unassigned.remove(seed_delivery)

            # Greedily search remaining unassigned deliveries for same-area candidates
            # Prioritize higher urgency (lower priority number), then larger weight to maximize bin utilization
            i = 0
            while i < len(unassigned):
                candidate = unassigned[i]
                if candidate.area == primary_area and current_trip.can_fit(candidate, max_stops=self.max_stops):
                    current_trip.add_delivery(candidate, max_stops=self.max_stops)
                    unassigned.pop(i)
                else:
                    i += 1

            # Optional: If multi-area is allowed and trip still has capacity and stops left
            if self.allow_multi_area and current_trip.remaining_capacity > 0:
                i = 0
                while i < len(unassigned):
                    candidate = unassigned[i]
                    if current_trip.can_fit(candidate, max_stops=self.max_stops):
                        current_trip.add_delivery(candidate, max_stops=self.max_stops)
                        unassigned.pop(i)
                    else:
                        i += 1

            # Order drop-offs within the trip by priority (most urgent first)
            current_trip.deliveries.sort(key=lambda d: (d.priority, str(d.id)))
            trips.append(current_trip)
            trip_counter += 1

        # 3. Sequence trips for dispatch:
        # Lower priority number (more urgent) trips depart first.
        # Tie-breaker: total weight descending (better utilized vehicle departs first), then trip_id
        trips.sort(key=lambda t: (t.highest_priority, -t.total_weight, t.trip_id))

        # Re-index trip IDs sequentially after dispatch ordering
        for idx, t in enumerate(trips, start=1):
            t.trip_id = idx

        # 4. Invariant Verification
        self._verify_invariants(valid_deliveries, trips)

        # 5. Compute Metrics
        metrics = self._calculate_metrics(
            total_input=len(deliveries) + len(initial_undeliverable or []),
            trips=trips,
            undeliverable=undeliverable,
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
        )

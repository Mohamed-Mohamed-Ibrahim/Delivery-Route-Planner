"""Version 1 Strategy: Priority-Driven Greedy First-Fit Route Planning."""

from __future__ import annotations

from typing import List, Optional

from src.algorithms.base import BasePlannerStrategy
from src.models import Delivery, Trip


class PriorityGreedyPlannerV1(BasePlannerStrategy):
    """Version 1 Strategy: Priority-Driven Greedy First-Fit Heuristic.

    Process:
    1. Sorts pending deliveries by urgency (priority asc, ID asc).
    2. Seeds a vehicle trip with the most urgent unassigned package, establishing the primary area.
    3. Greedily scans remaining packages in urgency order, packing any that match the primary area
       and fit within the remaining vehicle capacity and optional max stops.
    4. If multi-area is enabled, fills remaining spare capacity across other areas.
    5. Orders drop-offs within each trip by priority and sequences trips by highest urgency.
    """

    @property
    def algorithm_name(self) -> str:
        return "v1_priority_greedy"

    def plan_trips(
        self,
        deliveries: List[Delivery],
        max_capacity: float = 10.0,
        max_stops: Optional[int] = None,
        allow_multi_area: bool = False,
    ) -> List[Trip]:
        if not deliveries:
            return []

        # Sort upfront by urgency (priority asc, str(id) asc)
        unassigned = sorted(deliveries, key=lambda d: (d.priority, str(d.id)))
        trips: List[Trip] = []
        trip_counter = 1

        while unassigned:
            # Pick the most urgent delivery in the pending pool
            seed_delivery = unassigned[0]
            primary_area = seed_delivery.area

            # Create a new trip for this area
            current_trip = Trip(trip_id=trip_counter, max_capacity=max_capacity)
            current_trip.add_delivery(seed_delivery, max_stops=max_stops)
            unassigned.pop(0)

            # Greedily search remaining unassigned deliveries for same-area candidates
            i = 0
            while i < len(unassigned):
                candidate = unassigned[i]
                if candidate.area == primary_area and current_trip.can_fit(candidate, max_stops=max_stops):
                    current_trip.add_delivery(candidate, max_stops=max_stops)
                    unassigned.pop(i)
                else:
                    i += 1

            # Optional: If multi-area is allowed and trip still has capacity and stops left
            if allow_multi_area and current_trip.remaining_capacity > 0:
                i = 0
                while i < len(unassigned):
                    candidate = unassigned[i]
                    if current_trip.can_fit(candidate, max_stops=max_stops):
                        current_trip.add_delivery(candidate, max_stops=max_stops)
                        unassigned.pop(i)
                    else:
                        i += 1

            # Order drop-offs within the trip by priority (most urgent first)
            current_trip.deliveries.sort(key=lambda d: (d.priority, str(d.id)))
            trips.append(current_trip)
            trip_counter += 1

        # Sequence trips for dispatch:
        # Lower priority number (more urgent) trips depart first.
        # Tie-breaker: total weight descending, then original trip_id
        trips.sort(key=lambda t: (t.highest_priority, -t.total_weight, t.trip_id))

        # Re-index trip IDs sequentially after dispatch ordering
        for idx, t in enumerate(trips, start=1):
            t.trip_id = idx

        return trips

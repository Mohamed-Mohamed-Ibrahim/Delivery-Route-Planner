"""Version 2 Strategy: 0/1 Knapsack Dynamic Programming Route Planning."""

from __future__ import annotations

from typing import List, Optional, Tuple

from src.algorithms.base import BasePlannerStrategy
from src.models import Delivery, Trip


class KnapsackPlannerV2(BasePlannerStrategy):
    """Version 2 Strategy: 0/1 Knapsack Dynamic Programming approach.

    Process:
    1. Sorts pending deliveries by urgency (priority asc, ID asc).
    2. Seeds a vehicle trip with the most urgent unassigned package, establishing the primary area.
    3. Given the remaining capacity W' = max_capacity - seed.weight and remaining stops budget,
       formulates and solves a 0/1 Bounded Knapsack DP problem over candidates in the primary area.
    4. Package value prioritizes urgency (higher priority = much higher value) combined with
       weight fill to find the optimal subset that strictly honors urgency SLAs while maximizing
       vehicle capacity utilization.
    5. If multi-area is enabled, runs another 0/1 Knapsack step across other areas with remaining space.
    6. Orders drop-offs within each trip by priority and sequences trips by highest urgency.
    """

    SCALE: int = 100  # Scaling factor for weight precision (0.01 kg resolution)

    @property
    def algorithm_name(self) -> str:
        return "v2_knapsack"

    def _solve_01_knapsack(
        self,
        candidates: List[Delivery],
        capacity_kg: float,
        stops_limit: Optional[int] = None,
    ) -> List[Delivery]:
        """Solve bounded 0/1 Knapsack via Dynamic Programming."""
        cap_int = int(round(capacity_kg * self.SCALE))
        if cap_int <= 0 or not candidates:
            return []

        # Filter candidates that can fit individually
        valid: List[Tuple[Delivery, int, int]] = []
        for c in candidates:
            w_int = int(round(c.weight * self.SCALE))
            if 0 < w_int <= cap_int:
                # Value function: High priority weight + package weight
                # Priority 1 gets higher value than Priority 2, etc.
                urgency_val = (100 - min(c.priority, 99)) * 100000
                val = urgency_val + w_int
                valid.append((c, w_int, val))

        if not valid:
            return []

        n = len(valid)
        max_k = n if stops_limit is None else min(n, stops_limit)
        if max_k <= 0:
            return []

        if stops_limit is None:
            # 1D DP array with parent tracking for memory efficiency
            dp = [0] * (cap_int + 1)
            parent: List[List[Delivery]] = [[] for _ in range(cap_int + 1)]

            for c, w, val in valid:
                for weight in range(cap_int, w - 1, -1):
                    new_val = dp[weight - w] + val
                    if new_val > dp[weight]:
                        dp[weight] = new_val
                        parent[weight] = parent[weight - w] + [c]

            best_w = max(range(cap_int + 1), key=lambda w: dp[w])
            return parent[best_w]
        else:
            # 2D DP array: dp[weight][k_stops]
            dp_2d = [[0] * (max_k + 1) for _ in range(cap_int + 1)]
            parent_2d: List[List[List[Delivery]]] = [
                [[[] for _ in range(max_k + 1)] for _ in range(cap_int + 1)]
            ][0]

            for c, w, val in valid:
                for weight in range(cap_int, w - 1, -1):
                    for k in range(max_k, 0, -1):
                        new_val = dp_2d[weight - w][k - 1] + val
                        if new_val > dp_2d[weight][k]:
                            dp_2d[weight][k] = new_val
                            parent_2d[weight][k] = parent_2d[weight - w][k - 1] + [c]

            best_w, best_k = 0, 0
            best_v = -1
            for weight in range(cap_int + 1):
                for k in range(max_k + 1):
                    if dp_2d[weight][k] > best_v:
                        best_v = dp_2d[weight][k]
                        best_w, best_k = weight, k

            return parent_2d[best_w][best_k]

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

            # Candidates for same primary area
            same_area_candidates = [d for d in unassigned if d.area == primary_area]
            stops_limit = (max_stops - current_trip.stops_count) if max_stops is not None else None

            chosen = self._solve_01_knapsack(
                candidates=same_area_candidates,
                capacity_kg=current_trip.remaining_capacity,
                stops_limit=stops_limit,
            )

            for d in chosen:
                if current_trip.can_fit(d, max_stops=max_stops):
                    current_trip.add_delivery(d, max_stops=max_stops)
                    unassigned.remove(d)

            # Optional: If multi-area is allowed and trip still has capacity and stops left
            if allow_multi_area and current_trip.remaining_capacity > 0:
                multi_stops_limit = (max_stops - current_trip.stops_count) if max_stops is not None else None
                if multi_stops_limit is None or multi_stops_limit > 0:
                    other_candidates = list(unassigned)
                    chosen_multi = self._solve_01_knapsack(
                        candidates=other_candidates,
                        capacity_kg=current_trip.remaining_capacity,
                        stops_limit=multi_stops_limit,
                    )
                    for d in chosen_multi:
                        if current_trip.can_fit(d, max_stops=max_stops):
                            current_trip.add_delivery(d, max_stops=max_stops)
                            unassigned.remove(d)

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

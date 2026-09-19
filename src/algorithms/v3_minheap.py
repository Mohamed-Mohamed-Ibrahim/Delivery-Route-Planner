"""Version 3 Strategy: Priority Min-Heap Route Planning."""

from __future__ import annotations

import heapq
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple

from src.algorithms.base import BasePlannerStrategy
from src.models import Delivery, Trip


class MinHeapPlannerV3(BasePlannerStrategy):
    """Version 3 Strategy: Priority Min-Heap Route Planning.

    This algorithm addresses the O(N^2) linear scan bottleneck of Version 1
    by partitioning deliveries into area-specific min-heaps and coordinating
    trip dispatch via an area urgency scheduler heap.

    Process:
    1. Deliveries are bucketed by geographic area into individual min-heaps.
       Packages within each area heap are ordered by (priority, weight, str(id)).
    2. An area scheduler min-heap tracks the highest urgency package available
       across all areas: (min_priority, package_weight, str(id), area_name).
    3. The most urgent area is popped from the scheduler heap. The most urgent
       package seeds a new vehicle trip.
    4. Remaining packages in the same area are popped from its min-heap. Packages
       that fit within the remaining capacity and optional max stops are added to
       the trip; packages that do not fit are held in a temporary buffer and pushed
       back onto the area's min-heap once packing completes.
    5. If multi-area is enabled and vehicle capacity remains, other areas in the
       scheduler are similarly probed for fitting packages.
    6. If the area still contains packages, it is pushed back into the scheduler
       heap with its new top priority.
    7. Drop-offs within each trip are sequenced by priority (and ID), and completed
       trips are ordered for dispatch by highest priority, total weight descending,
       and trip ID.
    """

    @property
    def algorithm_name(self) -> str:
        return "v3_minheap"

    # @staticmethod
    # def _build_scheduler(
    #     area_heaps: Dict[str, List[Tuple[int, float, str, Delivery]]],
    #     exclude_area: Optional[str] = None,
    # ) -> List[Tuple[int, float, str, str]]:
    #     """Build or re-synchronize the area urgency scheduler min-heap."""
    #     scheduler: List[Tuple[int, float, str, str]] = [
    #         (heap[0][0], heap[0][1], heap[0][2], area)
    #         for area, heap in area_heaps.items()
    #         if heap and (exclude_area is None or area != exclude_area)
    #     ]
    #     heapq.heapify(scheduler)
    #     return scheduler

    def plan_trips(
        self,
        deliveries: List[Delivery],
        max_capacity: float = 10.0,
        max_stops: Optional[int] = None,
        allow_multi_area: int = 0,
    ) -> List[Trip]:
        if not deliveries:
            return []

        allow_multi_area = max(0, allow_multi_area)

        # 1. Bucket deliveries by area into priority min-heaps
        # Heap item: (priority, weight, id_str, delivery)
        area_heaps: Dict[str, List[Tuple[int, float, str, Delivery]]] = defaultdict(
            list
        )
        min_priority = 0
        for d in deliveries:
            heapq.heappush(area_heaps[d.area], (d.priority, d.weight, str(d.id), d))
            min_priority = max(min_priority, d.priority)

        # 2. Build area scheduler min-heap
        # Scheduler item: (top_priority, top_weight, top_id_str, area_name)
        # area_scheduler = self._build_scheduler(area_heaps)
        area_scheduler = []
        cnt = Counter()
        for area in area_heaps.keys():
            cnt = Counter([d.priority for _, _, _, d in area_heaps[area]])
            tasks = [0 for _ in range(min_priority + 1)]
            for k, v in cnt.items():
                tasks[k] = -v
            tasks.append(area)
            heapq.heappush(area_scheduler, tasks)

        trips: List[Trip] = []
        trip_counter = 1

        # 3. Process trips until all area heaps are empty
        while area_scheduler:
            tasks = heapq.heappop(area_scheduler)
            primary_area = tasks[-1]
            primary_heap = area_heaps[primary_area]

            if not primary_heap:
                continue

            # Seed the trip with the most urgent package from this area
            _, _, _, seed_delivery = heapq.heappop(primary_heap)
            current_trip = Trip(
                trip_id=trip_counter,
                max_capacity=max_capacity,
                max_stops=max_stops,
            )
            current_trip.add_delivery(seed_delivery)

            # Greedily pack additional packages from the same area using the min-heap
            temp_buffer: List[Tuple[int, float, str, Delivery]] = []
            while primary_heap and current_trip.remaining_capacity > 0:
                if max_stops is not None and current_trip.stops_count >= max_stops:
                    break

                entry = heapq.heappop(primary_heap)
                candidate = entry[3]
                if current_trip.can_fit(candidate):
                    current_trip.add_delivery(candidate)
                    tasks[candidate.priority] += 1
                else:
                    temp_buffer.append(entry)

            # Restore non-fitting packages back to the primary area heap
            for item in temp_buffer:
                heapq.heappush(primary_heap, item)

            if allow_multi_area > 0 and current_trip.remaining_capacity > 0:
                if max_stops is None or current_trip.stops_count < max_stops:
                    # Probe only the top K most urgent candidate areas from the scheduler heap
                    # Optimization in next version to choose the nearest area based on gps or location
                    candidate_areas = [
                        entry
                        for entry in heapq.nsmallest(allow_multi_area, area_scheduler)
                    ]
                    rebuild_scheduler = False

                    for other_tasks in candidate_areas:
                        other_area = other_tasks[-1]
                        if current_trip.remaining_capacity <= 0:
                            break
                        if (
                            max_stops is not None
                            and current_trip.stops_count >= max_stops
                        ):
                            break

                        other_heap = area_heaps[other_area]
                        other_temp: List[Tuple[int, float, str, Delivery]] = []
                        packed_from_other = False

                        while other_heap and current_trip.remaining_capacity > 0:
                            if (
                                max_stops is not None
                                and current_trip.stops_count >= max_stops
                            ):
                                break

                            entry = heapq.heappop(other_heap)
                            candidate = entry[3]
                            if current_trip.can_fit(candidate):
                                current_trip.add_delivery(candidate)
                                other_tasks[candidate.priority] += 1
                                packed_from_other = True
                            else:
                                other_temp.append(entry)

                        for item in other_temp:
                            heapq.heappush(other_heap, item)

                        if packed_from_other:
                            heapq.heappush(area_scheduler, other_tasks)

                    # Re-sync the scheduler heap if items were removed from other areas
                    # if rebuild_scheduler:
                    #     area_scheduler = self._build_scheduler(
                    #         area_heaps, exclude_area=primary_area
                    #     )

            # If primary area still has packages, push back into scheduler heap
            if primary_heap:
                heapq.heappush(area_scheduler, tasks)

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

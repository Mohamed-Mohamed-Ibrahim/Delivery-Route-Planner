"""Domain models for Delivery Route Planner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass(frozen=True)
class Delivery:
    """Represents an individual delivery request."""

    id: Any
    area: str
    priority: int
    weight: float

    def __post_init__(self) -> None:
        if not str(self.id).strip():
            raise ValueError("Delivery ID cannot be empty.")
        if not self.area or not self.area.strip():
            raise ValueError(f"Delivery {self.id}: Area cannot be empty.")
        if not isinstance(self.priority, int) or self.priority < 1:
            raise ValueError(f"Delivery {self.id}: Priority must be a positive integer (>= 1), got {self.priority}.")
        if self.weight <= 0:
            raise ValueError(f"Delivery {self.id}: Package weight must be greater than 0, got {self.weight}.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "area": self.area,
            "priority": self.priority,
            "weight": round(self.weight, 4),
        }


@dataclass
class Trip:
    """Represents a single vehicle trip carrying multiple deliveries."""

    trip_id: int
    deliveries: List[Delivery] = field(default_factory=list)
    max_capacity: float = 10.0

    @property
    def total_weight(self) -> float:
        """Total weight of all packages currently assigned to this trip."""
        return round(sum(d.weight for d in self.deliveries), 4)

    @property
    def remaining_capacity(self) -> float:
        """Remaining capacity available on this trip."""
        return round(max(0.0, self.max_capacity - self.total_weight), 4)

    @property
    def utilization_rate(self) -> float:
        """Percentage of vehicle weight capacity utilized."""
        if self.max_capacity <= 0:
            return 0.0
        return round((self.total_weight / self.max_capacity) * 100.0, 2)

    @property
    def highest_priority(self) -> int:
        """The highest urgency (minimum priority number) among packages in this trip."""
        if not self.deliveries:
            return float("inf")  # type: ignore[return-value]
        return min(d.priority for d in self.deliveries)

    @property
    def areas(self) -> List[str]:
        """Ordered list of unique delivery areas served in this trip."""
        seen = set()
        result = []
        for d in self.deliveries:
            if d.area not in seen:
                seen.add(d.area)
                result.append(d.area)
        return result

    @property
    def stops_count(self) -> int:
        return len(self.deliveries)

    def can_fit(self, delivery: Delivery, max_stops: Optional[int] = None) -> bool:
        """Check if adding delivery violates weight capacity or optional max stops constraint."""
        if max_stops is not None and self.stops_count >= max_stops:
            return False
        return round(self.total_weight + delivery.weight, 4) <= self.max_capacity

    def add_delivery(self, delivery: Delivery, max_stops: Optional[int] = None) -> None:
        """Add a delivery to the trip, enforcing capacity invariants."""
        if not self.can_fit(delivery, max_stops=max_stops):
            raise ValueError(
                f"Cannot add delivery {delivery.id} ({delivery.weight} kg) to Trip {self.trip_id}: "
                f"exceeds capacity ({self.total_weight} + {delivery.weight} > {self.max_capacity} kg)."
            )
        self.deliveries.append(delivery)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "areas": self.areas,
            "total_weight": self.total_weight,
            "max_capacity": self.max_capacity,
            "utilization_pct": self.utilization_rate,
            "highest_priority": self.highest_priority if self.deliveries else None,
            "stops_count": self.stops_count,
            "deliveries": [d.to_dict() for d in self.deliveries],
        }


@dataclass
class UndeliverableItem:
    """Represents a package that cannot be scheduled with diagnostic reason."""

    id: Any
    area: Optional[str]
    priority: Optional[int]
    weight: Optional[float]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "area": self.area,
            "priority": self.priority,
            "weight": self.weight,
            "reason": self.reason,
        }


@dataclass
class PlanMetrics:
    """Fleet and route analytics for a generated route plan."""

    total_deliveries: int
    delivered_count: int
    undelivered_count: int
    total_trips: int
    total_weight_delivered: float
    average_utilization_pct: float
    area_trip_counts: Dict[str, int]
    priority_counts: Dict[int, int]
    algorithm_version: str = "v2_knapsack"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm_version": self.algorithm_version,
            "total_deliveries": self.total_deliveries,
            "delivered_count": self.delivered_count,
            "undelivered_count": self.undelivered_count,
            "total_trips": self.total_trips,
            "total_weight_delivered": self.total_weight_delivered,
            "average_utilization_pct": self.average_utilization_pct,
            "area_trip_counts": self.area_trip_counts,
            "priority_counts": self.priority_counts,
        }


@dataclass
class RoutePlan:
    """The complete schedule of trips and undeliverable items."""

    trips: List[Trip] = field(default_factory=list)
    undeliverable: List[UndeliverableItem] = field(default_factory=list)
    metrics: Optional[PlanMetrics] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trips": [t.to_dict() for t in self.trips],
            "undeliverable": [u.to_dict() for u in self.undeliverable],
            "metrics": self.metrics.to_dict() if self.metrics else None,
        }

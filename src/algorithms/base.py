"""Strategy interface for delivery route planning algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.models import Delivery, Trip


class BasePlannerStrategy(ABC):
    """Abstract strategy for generating vehicle trips from a list of valid deliveries."""

    @property
    @abstractmethod
    def algorithm_name(self) -> str:
        """Machine-readable name and version identifier for this algorithm strategy."""
        raise NotImplementedError

    @abstractmethod
    def plan_trips(
        self,
        deliveries: List[Delivery],
        max_capacity: float = 10.0,
        max_stops: Optional[int] = None,
        allow_multi_area: bool = False,
    ) -> List[Trip]:
        """Plan vehicle trips from valid deliveries.

        Args:
            deliveries: List of valid deliveries (within vehicle weight limit).
            max_capacity: Maximum vehicle weight capacity in kg.
            max_stops: Optional maximum stops allowed per trip.
            allow_multi_area: Whether to allow mixing delivery areas in a trip.

        Returns:
            List of scheduled Trip objects in dispatch order.
        """
        raise NotImplementedError

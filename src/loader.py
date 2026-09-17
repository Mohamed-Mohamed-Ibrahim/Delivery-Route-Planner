"""Data loading and validation module for CSV and JSON inputs."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.models import Delivery, UndeliverableItem


@dataclass
class LoaderResult:
    """Result of loading delivery data from a file."""

    deliveries: List[Delivery]
    rejected_items: List[UndeliverableItem]


def _normalize_key(key: str) -> str:
    """Normalize a dictionary key or CSV header for flexible matching."""
    cleaned = key.strip().lower().replace("_", " ").replace("-", " ")
    # Strip common suffixes like (kg)
    cleaned = cleaned.replace("(kg)", "").strip()
    return cleaned


def _map_fields(record: Dict[str, Any]) -> Tuple[Optional[Any], Optional[str], Optional[Any], Optional[Any]]:
    """Extract (id, area, priority, weight) from record with flexible keys."""
    norm_dict = {_normalize_key(str(k)): v for k, v in record.items()}

    # Extract ID
    item_id = None
    for k in ["id", "delivery id", "deliveryid", "package id", "pkg id"]:
        if k in norm_dict and norm_dict[k] is not None and str(norm_dict[k]).strip() != "":
            item_id = norm_dict[k]
            break

    # Extract Area
    area = None
    for k in ["area", "zone", "destination", "region", "neighborhood"]:
        if k in norm_dict and norm_dict[k] is not None and str(norm_dict[k]).strip() != "":
            area = str(norm_dict[k]).strip()
            break

    # Extract Priority
    priority = None
    for k in ["priority", "urgency", "level"]:
        if k in norm_dict and norm_dict[k] is not None and str(norm_dict[k]).strip() != "":
            priority = norm_dict[k]
            break

    # Extract Weight
    weight = None
    for k in ["package weight", "weight", "pkg weight", "package weight kg", "weight kg"]:
        if k in norm_dict and norm_dict[k] is not None and str(norm_dict[k]).strip() != "":
            weight = norm_dict[k]
            break

    return item_id, area, priority, weight


def _parse_delivery_record(record: Dict[str, Any], row_idx: int) -> Tuple[Optional[Delivery], Optional[UndeliverableItem]]:
    """Validate and parse a single delivery record dictionary."""
    item_id, area, priority_raw, weight_raw = _map_fields(record)

    fallback_id = item_id if item_id is not None else f"Row-{row_idx}"

    if item_id is None:
        return None, UndeliverableItem(
            id=fallback_id,
            area=area,
            priority=None,
            weight=None,
            reason="Missing required field: Delivery ID",
        )

    if not area:
        return None, UndeliverableItem(
            id=item_id,
            area=None,
            priority=None,
            weight=None,
            reason=f"Delivery {item_id}: Missing or empty Area.",
        )

    # Validate Priority
    try:
        priority = int(priority_raw)  # type: ignore[arg-type]
        if priority < 1:
            return None, UndeliverableItem(
                id=item_id,
                area=area,
                priority=priority,
                weight=None,
                reason=f"Delivery {item_id}: Priority must be an integer >= 1 (got {priority}).",
            )
    except (ValueError, TypeError):
        return None, UndeliverableItem(
            id=item_id,
            area=area,
            priority=None,
            weight=None,
            reason=f"Delivery {item_id}: Invalid priority value '{priority_raw}' (must be integer >= 1).",
        )

    # Validate Weight
    try:
        weight = float(weight_raw)  # type: ignore[arg-type]
        if weight <= 0:
            return None, UndeliverableItem(
                id=item_id,
                area=area,
                priority=priority,
                weight=weight,
                reason=f"Delivery {item_id}: Package weight must be greater than 0 kg (got {weight}).",
            )
    except (ValueError, TypeError):
        return None, UndeliverableItem(
            id=item_id,
            area=area,
            priority=priority,
            weight=None,
            reason=f"Delivery {item_id}: Invalid weight value '{weight_raw}' (must be positive number).",
        )

    return Delivery(id=item_id, area=area, priority=priority, weight=round(weight, 4)), None


def load_from_csv(filepath: str) -> LoaderResult:
    """Load deliveries from a CSV file."""
    deliveries: List[Delivery] = []
    rejected: List[UndeliverableItem] = []

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return LoaderResult(deliveries=[], rejected_items=[])

        for idx, row in enumerate(reader, start=1):
            if not any(v.strip() for v in row.values() if v is not None):
                continue  # Skip blank lines
            delivery, error_item = _parse_delivery_record(row, idx)
            if delivery:
                deliveries.append(delivery)
            elif error_item:
                rejected.append(error_item)

    return LoaderResult(deliveries=deliveries, rejected_items=rejected)


def load_from_json(filepath: str) -> LoaderResult:
    """Load deliveries from a JSON file (array of objects)."""
    deliveries: List[Delivery] = []
    rejected: List[UndeliverableItem] = []

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    with open(filepath, mode="r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return LoaderResult(deliveries=[], rejected_items=[])
        data = json.loads(content)

    if not isinstance(data, list):
        raise ValueError("JSON input must contain a top-level array of delivery objects.")

    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            rejected.append(
                UndeliverableItem(
                    id=f"Index-{idx}",
                    area=None,
                    priority=None,
                    weight=None,
                    reason=f"Item at index {idx} is not a valid JSON object.",
                )
            )
            continue
        delivery, error_item = _parse_delivery_record(item, idx)
        if delivery:
            deliveries.append(delivery)
        elif error_item:
            rejected.append(error_item)

    return LoaderResult(deliveries=deliveries, rejected_items=rejected)


def load_deliveries(filepath: str) -> LoaderResult:
    """Auto-detect format (CSV or JSON) and parse delivery requests."""
    _, ext = os.path.splitext(filepath)
    ext_lower = ext.lower()

    if ext_lower == ".json":
        return load_from_json(filepath)
    elif ext_lower == ".csv":
        return load_from_csv(filepath)
    else:
        raise Exception("Unsupported Input Format")

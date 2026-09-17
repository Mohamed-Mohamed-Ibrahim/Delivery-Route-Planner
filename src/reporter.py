"""Reporting, visualization, and manifest export module."""

from __future__ import annotations

import csv
import json
import os
from typing import TextIO

from src.models import RoutePlan


def format_plan_summary(plan: RoutePlan, verbose: bool = False) -> str:
    """Generate a clean, readable text summary of the route plan."""
    lines = []
    lines.append("=" * 72)
    lines.append("                  DELIVERY ROUTE DISPATCH PLAN                  ")
    lines.append("=" * 72)

    metrics = plan.metrics
    if metrics:
        lines.append(f" Total Requests Ingested : {metrics.total_deliveries}")
        lines.append(f" Successfully Scheduled  : {metrics.delivered_count}")
        lines.append(f" Undeliverable / Flagged : {metrics.undelivered_count}")
        lines.append(f" Total Vehicle Trips     : {metrics.total_trips}")
        lines.append(f" Total Delivered Weight  : {metrics.total_weight_delivered:.2f} kg")
        lines.append(f" Avg Fleet Utilization   : {metrics.average_utilization_pct:.1f}%")
        lines.append("-" * 72)

    if not plan.trips:
        lines.append(" No vehicle trips scheduled.")
    else:
        lines.append("SCHEDULED VEHICLE TRIPS (DISPATCH ORDER):")
        lines.append("-" * 72)
        lines.append(
            f"{'Trip':<6}{'Primary Area':<16}{'Stops':<7}{'Weight / Cap':<16}{'Util %':<8}{'Packages (ID: Pri/Wt)'}"
        )
        lines.append("-" * 72)

        for trip in plan.trips:
            area_str = ", ".join(trip.areas)
            weight_str = f"{trip.total_weight:.2f} / {trip.max_capacity:.1f} kg"
            pkg_str = ", ".join(f"#{d.id}(P{d.priority}:{d.weight}kg)" for d in trip.deliveries)
            lines.append(
                f"Trip {trip.trip_id:<3} {area_str:<15} {trip.stops_count:<7} {weight_str:<16} {trip.utilization_rate:>5.1f}%   {pkg_str}"
            )

        if verbose:
            lines.append("\n" + "=" * 72)
            lines.append("DETAILED TRIP MANIFEST (DROP-OFF SEQUENCE):")
            lines.append("=" * 72)
            for trip in plan.trips:
                lines.append(f"\n[TRIP {trip.trip_id}] Area: {', '.join(trip.areas)} | Total Weight: {trip.total_weight:.2f} kg | Capacity: {trip.max_capacity:.1f} kg ({trip.utilization_rate:.1f}%)")
                lines.append(f"  {'Stop':<6}{'Package ID':<14}{'Area':<16}{'Priority':<12}{'Weight (kg)':<12}")
                lines.append("  " + "-" * 60)
                for stop_idx, d in enumerate(trip.deliveries, start=1):
                    lines.append(f"  {stop_idx:<6}{str(d.id):<14}{d.area:<16}Priority {d.priority:<4}{d.weight:.2f} kg")

    if plan.undeliverable:
        lines.append("\n" + "!" * 72)
        lines.append("UNDELIVERABLE / QUARANTINED PACKAGES:")
        lines.append("!" * 72)
        lines.append(f"{'ID':<10}{'Area':<14}{'Priority':<10}{'Weight':<10}{'Reason'}")
        lines.append("-" * 72)
        for item in plan.undeliverable:
            area = item.area or "N/A"
            pri = str(item.priority) if item.priority is not None else "N/A"
            wt = f"{item.weight:.2f} kg" if item.weight is not None else "N/A"
            lines.append(f"{str(item.id):<10}{area:<14}{pri:<10}{wt:<10}{item.reason}")

    lines.append("=" * 72)
    return "\n".join(lines)


def export_json(plan: RoutePlan, filepath: str) -> None:
    """Export the route plan as structured JSON."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)


def export_csv(plan: RoutePlan, filepath: str) -> None:
    """Export the route plan as a flat driver dispatch manifest CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Trip ID",
            "Trip Primary Area",
            "Stop Order",
            "Package ID",
            "Package Area",
            "Package Priority",
            "Package Weight (kg)",
            "Trip Total Weight (kg)",
            "Trip Capacity (kg)",
            "Trip Utilization Pct",
        ])

        for trip in plan.trips:
            primary_area = trip.areas[0] if trip.areas else ""
            for stop_idx, d in enumerate(trip.deliveries, start=1):
                writer.writerow([
                    trip.trip_id,
                    primary_area,
                    stop_idx,
                    d.id,
                    d.area,
                    d.priority,
                    d.weight,
                    trip.total_weight,
                    trip.max_capacity,
                    trip.utilization_rate,
                ])

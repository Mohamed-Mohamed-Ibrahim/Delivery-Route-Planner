#!/usr/bin/env python3
"""Delivery Route Planner CLI Application.

Organizes delivery packages into vehicle trips adhering to weight capacity,
urgency/priority order, and geographical area grouping.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from src.loader import load_deliveries
from src.planner import RoutePlanner
from src.reporter import export_csv, export_json, format_plan_summary


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="delivery-route-planner",
        description=(
            "Delivery Route Planner: Groups delivery requests into capacity-constrained "
            "trips prioritized by urgency and clustered by geographical area."
        ),
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to input delivery file (.csv or .json).",
    )
    parser.add_argument(
        "-c",
        "--capacity",
        type=float,
        default=10.0,
        help="Vehicle weight capacity limit in kg (default: 10.0).",
    )
    parser.add_argument(
        "-s",
        "--max-stops",
        type=int,
        default=None,
        help="Optional maximum number of delivery stops per vehicle trip.",
    )
    parser.add_argument(
        "--allow-multi-area",
        action="store_true",
        default=False,
        help="Allow filling remaining vehicle capacity with packages from other areas.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional output file path to save dispatch manifest.",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["text", "json", "csv"],
        default="text",
        help="Output format for file export (default: text).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Print detailed per-stop manifest breakdown in console output.",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    """Run the CLI application."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1. Load delivery requests
    try:
        loader_result = load_deliveries(args.input_file)
    except FileNotFoundError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1
    except Exception as err:
        sys.stderr.write(f"Error loading file: {err}\n")
        return 1

    # 2. Plan trips
    try:
        planner = RoutePlanner(
            max_capacity=args.capacity,
            max_stops=args.max_stops,
            allow_multi_area=args.allow_multi_area,
        )
        plan = planner.plan(
            deliveries=loader_result.deliveries,
            initial_undeliverable=loader_result.rejected_items,
        )
    except Exception as err:
        sys.stderr.write(f"Planning Error: {err}\n")
        return 1

    # 3. Print console summary
    print(format_plan_summary(plan, verbose=args.verbose))

    # 4. Optional file export
    if args.output:
        fmt = args.format.lower()
        if fmt == "json":
            export_json(plan, args.output)
            print(f"\n[Export] Route plan JSON manifest written to: {args.output}")
        elif fmt == "csv":
            export_csv(plan, args.output)
            print(f"\n[Export] Driver dispatch CSV manifest written to: {args.output}")
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(format_plan_summary(plan, verbose=True))
            print(f"\n[Export] Text manifest written to: {args.output}")

    return 0


def main() -> None:
    """Entry point."""
    sys.exit(run())


if __name__ == "__main__":
    main()

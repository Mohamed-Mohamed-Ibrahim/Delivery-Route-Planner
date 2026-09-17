# Delivery Route Planner

A robust, modular, and test-driven delivery route planning engine developed in Python. The system organizes incoming delivery orders into capacity-constrained vehicle trips, prioritizing high-urgency requests and clustering deliveries destined for the same geographical area.

---

## Table of Contents

- [Overview](#overview)
- [Architecture & Design](#architecture--design)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Program](#running-the-program)
  - [CLI Reference](#cli-reference)
- [Input Formats & Sample Data](#input-formats--sample-data)
- [Running Automated Tests](#running-automated-tests)
  - [Test Coverage Plan](#test-coverage-plan)
- [Reasoning & Technical Reflection](#reasoning--technical-reflection)
  - [1. Solution Approach](#1-explain-your-solution-approach-in-your-own-words)
  - [2. Most Difficult Part](#2-what-was-the-most-difficult-part-of-the-assignment)
  - [3. Suboptimal Grouping Scenarios](#3-are-there-situations-where-your-algorithm-may-not-produce-the-best-possible-grouping-explain)
  - [4. Scaling to 1,000,000 Requests](#4-if-the-input-contained-1000000-delivery-requests-what-part-of-your-solution-might-become-slow-or-memory-intensive)
  - [5. What to Improve with Another Day](#5-what-would-you-improve-if-you-had-another-day-to-work-on-the-solution)
- [Extension: Fleet Efficiency Analytics & Manifest Exporter](#extension-fleet-efficiency-analytics--manifest-exporter)

---

## Overview

In logistics and route planning, dispatchers face a multi-criteria optimization challenge:
1. **Capacity Limit**: A delivery vehicle can carry at most **10.0 kg** per trip.
2. **Urgency First**: Lower priority numbers represent more urgent packages (e.g., Priority 1 before Priority 2).
3. **Geographic Clustering**: Deliveries to the same area should be grouped together where reasonably possible to reduce transit time and prevent redundant trips.
4. **Complete Assignment**: Every valid package must appear in exactly one trip.
5. **Defensive Resilience**: Sensibly handle empty batches, packages exceeding vehicle capacity (> 10 kg), priority ties, and malformed files.

---

## Architecture & Design

The project is structured with strict separation of concerns, zero third-party runtime dependencies (standard library only), and full typing (`mypy`-compatible):

```
Delivery-Route-Planner/
├── data/
│   ├── sample_deliveries.csv        # Section 3.1 sample dataset (5 rows)
│   ├── sample_deliveries.json       # JSON equivalent dataset
│   └── edge_cases.csv               # Overweight items, priority ties, multi-trip area splits
├── docs/
│   └── problem_statement.pdf        # Technical specification
├── src/
│   ├── __init__.py
│   ├── models.py                    # Strongly-typed domain models (Delivery, Trip, RoutePlan, PlanMetrics)
│   ├── loader.py                    # Multi-format reader (CSV/JSON) with schema validation
│   ├── planner.py                   # Strategy context, invariant verification & metrics coordination
│   ├── reporter.py                  # Terminal table formatting and JSON/CSV manifest exporters
│   └── algorithms/                  # Modular Strategy Design Pattern implementations
│       ├── __init__.py              # Strategy registry and factory
│       ├── base.py                  # BasePlannerStrategy interface
│       ├── v1_priority_greedy.py    # Version 1: Priority-Driven Greedy First-Fit
│       ├── v2_knapsack.py           # Version 2: 0/1 Knapsack Dynamic Programming (Default)
│       └── v3_minheap.py            # Version 3: Scalable Priority Min-Heap & Area Scheduler
├── tests/
│   ├── __init__.py
│   ├── test_cli.py                  # End-to-end CLI integration tests
│   ├── test_models.py               # Unit tests for domain models & capacity invariants
│   ├── test_loader.py               # Ingestion, schema validation & corrupted data tests
│   ├── test_planner.py              # Core planning logic & Section 3.1 verification
│   ├── test_edge_cases.py           # Edge cases (empty, >10kg, priority ties, precision)
│   └── test_algorithms.py           # Strategy pattern, v1 vs v2, & Knapsack optimality tests
├── main.py                          # CLI application entry point
├── README.md                        # Documentation and technical reflection
└── .env.example                     # Environment configuration template
```

---

## Getting Started

### Prerequisites
- **Python 3.10+** (uses standard library modules: `argparse`, `csv`, `json`, `dataclasses`, `typing`).
- Optional: `pytest` to run automated test suites.

### Installation

Clone the repository and verify Python availability:
```bash
git clone https://github.com/Mohamed-Mohamed-Ibrahim/Delivery-Route-Planner.git
cd Delivery-Route-Planner
python3 --version
```

To install development and testing dependencies:
```bash
pip install pytest coverage
```

### Running the Program

Run the planner on the provided Section 3.1 sample CSV data:
```bash
python3 main.py data/sample_deliveries.csv
```

#### Output
```text
========================================================================
                  DELIVERY ROUTE DISPATCH PLAN                  
========================================================================
 Total Requests Ingested : 5
 Successfully Scheduled  : 5
 Undeliverable / Flagged : 0
 Total Vehicle Trips     : 3
 Total Delivered Weight  : 18.20 kg
 Avg Fleet Utilization   : 60.7%
------------------------------------------------------------------------
SCHEDULED VEHICLE TRIPS (DISPATCH ORDER):
------------------------------------------------------------------------
Trip  Primary Area    Stops  Weight / Cap    Util %  Packages (ID: Pri/Wt)
------------------------------------------------------------------------
Trip 1   Zamalek         1       7.00 / 10.0 kg    70.0%   #4(P1:7.0kg)
Trip 2   Maadi           2       5.50 / 10.0 kg    55.0%   #2(P1:2.0kg), #5(P2:3.5kg)
Trip 3   Nasr City       2       5.70 / 10.0 kg    57.0%   #1(P2:4.5kg), #3(P3:1.2kg)
========================================================================
```

### CLI Reference

```text
usage: delivery-route-planner [-h] [-c CAPACITY] [-s MAX_STOPS]
                              [-a {v3_minheap,v2_knapsack,v1_greedy}]
                              [--allow-multi-area] [-o OUTPUT] [-f {text,json,csv}] [-v]
                              input_file

positional arguments:
  input_file            Path to input delivery file (.csv or .json).

options:
  -h, --help            Show this help message and exit.
  -c, --capacity        Vehicle weight capacity in kg (default: 10.0).
  -s, --max-stops       Optional maximum delivery stops per vehicle trip.
  -a, --algorithm       Route planning algorithm strategy: 'v3_minheap', 'v2_knapsack', or 'v1_greedy' (default: v2_knapsack).
  --allow-multi-area    Allow filling remaining vehicle capacity across areas.
  -o, --output          Optional output file path to save dispatch manifest.
  -f, --format          Output manifest format: 'text', 'json', or 'csv' (default: text).
  -v, --verbose         Print detailed per-stop drop-off sequence table.
```

#### Examples

1. **Verbose drop-off sequence**:
   ```bash
   python3 main.py data/sample_deliveries.csv -v
   ```

2. **JSON Input**:
   ```bash
   python3 main.py data/sample_deliveries.json
   ```

3. **Exporting driver route manifest (CSV)**:
   ```bash
   python3 main.py data/sample_deliveries.csv -o manifests/driver_sheet.csv -f csv
   ```

4. **Configurable constraints (e.g. 8 kg capacity, max 2 stops per trip)**:
   ```bash
   python3 main.py data/sample_deliveries.csv -c 8.0 -s 2
   ```

5. **Running with edge cases**:
   ```bash
   python3 main.py data/edge_cases.csv -v
   ```

---

## Input Formats & Sample Data

### CSV Format (`data/sample_deliveries.csv`)
Header matching is flexible and case-insensitive:
```csv
ID,Area,Priority,Package Weight (kg)
1,Nasr City,2,4.5
2,Maadi,1,2.0
3,Nasr City,3,1.2
4,Zamalek,1,7.0
5,Maadi,2,3.5
```

### JSON Format (`data/sample_deliveries.json`)
```json
[
  {"id": 1, "area": "Nasr City", "priority": 2, "package_weight": 4.5},
  {"id": 2, "area": "Maadi", "priority": 1, "package_weight": 2.0},
  {"id": 3, "area": "Nasr City", "priority": 3, "package_weight": 1.2},
  {"id": 4, "area": "Zamalek", "priority": 1, "package_weight": 7.0},
  {"id": 5, "area": "Maadi", "priority": 2, "package_weight": 3.5}
]
```

---

## Running Automated Tests

A comprehensive test suite of 34 tests covers unit models, data ingestion, boundary cases, strategy patterns, and end-to-end integration:

```bash
python3 -m pytest -v tests/
```

Test modules:
- `tests/test_models.py`: Domain validations, invariants, utilization calculation, overflow errors.
- `tests/test_loader.py`: CSV/JSON ingestion, header variations, empty files, malformed rows.
- `tests/test_planner.py`: Section 3.1 sample dataset verification, priority ordering, area clustering.
- `tests/test_edge_cases.py`: Empty input, overweight packages (> 10 kg), priority ties, capacity overflow, floating-point precision.
- `tests/test_algorithms.py`: Strategy Design Pattern registration, v1 vs v2 parity, Knapsack optimality demonstration, and CLI algorithm flag.
- `tests/test_cli.py`: CLI invocation, exit codes, output formatting, manifest exports.

### Test Coverage Plan

Measuring test coverage is kept as simple as possible. Only three commands are needed:

```bash
coverage run -m pytest tests/
coverage html
coverage report -m
```

- **`coverage run -m pytest tests/`**: Runs the complete test suite while recording execution metrics.
- **`coverage html`**: Generates a detailed, browsable HTML coverage report inside `htmlcov/index.html`.
- **`coverage report -m`**: Prints an interactive terminal report displaying coverage percentages and missed lines.

---

## Reasoning & Technical Reflection

### 1. Explain your solution approach in your own words.

Our solution implements a **Priority-Driven Area Clustering Heuristic** combining bin-packing principles with urgency-aware dispatch sequencing:

1. **Pre-processing & Quarantine**:
   - The ingestion layer validates inputs against required schema types.
   - Any package with `weight > max_capacity` (10.0 kg) cannot be carried by a single vehicle. Rather than crashing the entire dispatch run or silently dropping records, these are isolated into an `undeliverable` quarantine list with an explicit diagnostic explanation.
2. **Trip Seeding by Urgency**:
   - From the unassigned package pool, the algorithm selects the most urgent package (lowest priority number; ties broken deterministically by ID).
   - This package "seeds" a new trip and establishes the trip's primary target area.
3. **Same-Area Greedy Bin Packing**:
   - Once a trip is initiated for an area, the planner scans remaining unassigned packages *destined for that same area*.
   - Packages are greedily added in order of urgency as long as `trip.total_weight + package.weight <= max_capacity`.
   - This ensures same-area deliveries are grouped together, preventing redundant trips to the same neighborhood when vehicle capacity is available.
4. **Dispatch Sequencing & Stop Ordering**:
   - Trips containing Priority 1 packages are scheduled to depart before trips containing only Priority 2 or 3 packages.
   - Inside each vehicle trip, drop-offs are sorted by priority so drivers deliver the most urgent packages first upon arriving in the destination area.
5. **Invariant Verification**:
   - An automated post-condition check verifies that no trip exceeds 10.0 kg and that every valid delivery is assigned to exactly one trip.

---

### 2. What was the most difficult part of the assignment?

The most difficult challenge was **reconciling the competing trade-offs between three conflicting objectives**:
1. **Urgency (Priority SLA)**: High-priority packages should leave immediately.
2. **Geographic Efficiency (Area Clustering)**: Vehicles should avoid traveling between disjoint areas or making duplicate trips to the same area.
3. **Capacity Utilization (Bin Packing)**: Vehicles should be packed near the 10.0 kg limit to minimize the total number of trips.

#### The Dilemma:
Consider a vehicle initiated for **Area A** to deliver a Priority 1 package (2.0 kg). There is also a Priority 3 package (7.0 kg) for **Area A**, and a Priority 1 package (3.0 kg) for **Area B**.
- If we strictly enforce urgency above all else, we might dispatch the Area A Priority 1 package and immediately dispatch the Area B Priority 1 package in separate vehicles, leaving Area A's Priority 3 package for later. That means two separate trips will eventually visit Area A.
- Conversely, if we group Area A's Priority 3 package into the first vehicle (2.0 kg + 7.0 kg = 9.0 kg), that vehicle departs right away, but it carried a Priority 3 package while Area B's Priority 1 package had to wait for another vehicle.

We resolved this by using urgency to **drive trip creation**, but utilizing spare capacity in that same trip to **bundle same-area packages**. This honors area grouping, eliminates redundant neighborhood visits, and ensures trips containing high-priority packages are dispatched first.

Additionally, managing **floating-point arithmetic precision** in Python (e.g., `3.3 + 3.3 + 3.4 = 10.000000000000002` causing false capacity overflow) required careful rounding to 4 decimal places across all capacity checks.

---

### 3. Are there situations where your algorithm may not produce the best possible grouping? Explain.

Yes. Because Bin Packing is an **NP-hard** problem, any polynomial-time greedy heuristic will produce suboptimal solutions in specific edge scenarios:

#### Scenario A: Suboptimal Bin Packing within an Area (Fragmentation)
Suppose an area has packages with weights: `[6.0 kg, 5.0 kg, 5.0 kg, 4.0 kg]` (all Priority 2).
- The optimal packing is **2 trips**:
  - Trip 1: `6.0 kg + 4.0 kg = 10.0 kg` (100% full)
  - Trip 2: `5.0 kg + 5.0 kg = 10.0 kg` (100% full)
- A pure greedy first-fit heuristic might pack `6.0 kg`, attempt `5.0 kg` (exceeds 10 kg), attempt `5.0 kg` (exceeds), and pack `4.0 kg` (giving Trip 1 = `10.0 kg`). Trip 2 would take `5.0 kg`, and Trip 3 would take `5.0 kg` — resulting in **3 trips instead of 2**.

#### Scenario B: Cross-Area Multi-Stop Fragmentation (Disjoint Leftovers)
Suppose three adjacent areas each have a single 1.0 kg package of low priority.
- Under strict single-area clustering, 3 vehicles are dispatched carrying only 1.0 kg each (10% utilization).
- If geographic distance matrices were available, consolidating those three nearby 1.0 kg packages into 1 vehicle trip would achieve 30% utilization and save two driver shifts.

#### Scenario C: Urgency-Forced Capacity Lockout
Suppose a trip is seeded by a Priority 1 package of 9.0 kg. The remaining 1.0 kg capacity cannot fit any of the remaining 2.0 kg or 3.0 kg packages for that area, forcing them into subsequent trips.

---

### 4. If the input contained 1,000,000 delivery requests, what part of your solution might become slow or memory-intensive?

Processing 1,000,000 deliveries exposes two distinct scaling bottlenecks:

#### Computational Bottlenecks ($O(N^2)$ Greedy Search):
- In our current implementation, when filling a trip, the planner iterates through the remaining unassigned items:
  ```python
  while i < len(unassigned):
      if candidate.area == primary_area and current_trip.can_fit(...): ...
  ```
  In the worst case (e.g. many deliveries in the same area), repeatedly removing items from a list of size $N$ takes $O(N)$ per removal, resulting in an overall time complexity of **$O(N^2)$**.
  For $N = 1,000,000$, $N^2 = 10^{12}$ operations, which would take hours to run.

#### Memory Bottleneck:
- Storing 1,000,000 Python `Delivery` dataclass instances in memory consumes approximately 300–500 MB of RAM. While manageable on modern hardware, reading the entire dataset at once with `json.load()` or `csv.DictReader` requires allocating substantial heap memory simultaneously.

#### How to Scale for 1,000,000 Requests:
1. **Area-Partitioned Bucketing ($O(1)$ Hash Map)**:
   Group deliveries upfront into a hash table partitioned by area: `dict[str, list[Delivery]]`.
   Processing is then isolated per area, reducing complexity from $O(N^2)$ to $\sum O(M_i^2)$ where $M_i \ll N$.
2. **Priority Min-Heaps / Balanced Trees**:
   Store deliveries within each area in a priority queue / balanced search tree keyed by `(priority, weight)`. Extracting the next urgent or fitting package runs in $O(\log M)$.
   *(Note: This design is directly implemented in strategy `v3_minheap` (`src/algorithms/v3_minheap.py`), coordinating area heaps with an area urgency scheduler heap).*
3. **Streaming & Batching**:
   Stream input records using generators and flush completed trip manifests directly to disk (chunked CSV/JSON output) instead of accumulating all trips in memory.

---

### 5. What would you improve if you had another day to work on the solution?

With an additional day, the following enhancements would elevate this tool to production-grade:

1. **Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)**:
   - Integrate **Google OR-Tools** to model real travel time matrices, road network distances, customer delivery time windows (e.g., 9:00 AM – 11:00 AM), and vehicle recharge/refuel stops.
2. **Inter-Area Spatial Proximity Matrix**:
   - Rather than binary matching on `area == area`, incorporate geographic coordinates (latitude/longitude) or a distance matrix between zones. This allows smart consolidation of small packages from adjacent neighborhoods (e.g., Dokki and Mohandessin) when vehicle capacity allows.
3. **Exact Dynamic Programming / 0-1 Knapsack Solver for Trips**:
   - Replace greedy same-area packing with a subset-sum / knapsack solver to guarantee 100% optimal vehicle capacity fill rate when multiple package combinations exist.
4. **Dynamic Real-Time Re-Dispatching**:
   - Provide an event-driven API (FastAPI / Webhooks) that allows incoming rush orders to dynamically update driver manifests before departure.
5. **Interactive Dispatcher Map Visualizer**:
   - Add a lightweight Leaflet / Folium web map rendering routes, trip color-coding, and vehicle fill status.

---

## Extension: Fleet Efficiency Analytics & Manifest Exporter

As required by **Section 5 of the specification**, we implemented **Fleet Efficiency Analytics & Driver Route Manifest Exporter**.

### Why This Feature?
In real logistics operations, an algorithm is only as useful as its operational outputs. Dispatchers need:
1. **Actionable Driver Manifests**: Drivers need clear, sequenced sheets specifying which packages belong to their vehicle and the exact drop-off order.
2. **Fleet Utilization Analytics**: Operations managers need immediate feedback on average vehicle weight capacity utilization, total trips required, and undeliverable quarantine rates to evaluate fleet costs.

### Capabilities Included:
- **CLI Exporter (`-o / --output`, `-f / --format`)**:
  - Export machine-readable **JSON manifests** for API integration.
  - Export structured **CSV driver manifests** containing Trip ID, Area, Stop Order, Package ID, Priority, Package Weight, and Cumulative Vehicle Utilization.
- **Configurable Fleet Constraints**:
  - `--capacity / -c`: Adjust vehicle weight limit (default: 10.0 kg) to model different fleet vehicle sizes (motorcycles, vans, cargo bikes).
  - `--max-stops / -s`: Set maximum delivery stops per trip to account for driver shift duration or fatigue constraints.
  - `--allow-multi-area`: Enable cross-area package filling when spare capacity remains.
- **Quarantine Diagnostics**:
  - Automatic isolation and diagnostic reporting for packages exceeding vehicle capacity or containing corrupt attributes, allowing operators to reschedule them via freight carriers without interrupting the standard dispatch cycle.

---

## Submission Checklist

- [x] Program runs successfully on Python 3.10+.
- [x] Sample input files included (`data/sample_deliveries.csv`, `data/sample_deliveries.json`).
- [x] Edge cases dataset included (`data/edge_cases.csv`).
- [x] README explains setup, execution, and CLI options.
- [x] README thoroughly answers all 5 reasoning questions.
- [x] One additional useful feature implemented and documented (Section 5).
- [x] 100% automated test pass rate across 34 unit and integration tests.

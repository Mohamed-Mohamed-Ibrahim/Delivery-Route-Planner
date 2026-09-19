# Delivery Route Planner

A high-performance, modular, and test-driven delivery route planning engine developed in Python. The system organizes incoming delivery requests into capacity-constrained vehicle trips, prioritizing high-urgency requests and clustering deliveries destined for the same geographical area.

---

## Table of Contents

- [Delivery Route Planner](#delivery-route-planner)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Architecture \& Design](#architecture--design)
    - [Strategy Design Pattern](#strategy-design-pattern)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Running the Program](#running-the-program)
      - [Output](#output)
    - [CLI Reference](#cli-reference)
    - [Usage Examples](#usage-examples)
  - [Input Formats \& Sample Data](#input-formats--sample-data)
    - [CSV Format (`data/sample_deliveries.csv`)](#csv-format-datasample_deliveriescsv)
    - [JSON Format (`data/sample_deliveries.json`)](#json-format-datasample_deliveriesjson)
  - [Running Automated Tests](#running-automated-tests)
    - [Test Coverage Plan](#test-coverage-plan)
  - [Reasoning \& Technical Reflection](#reasoning--technical-reflection)
    - [1. Explain your solution approach in your own words.](#1-explain-your-solution-approach-in-your-own-words)
    - [2. What was the most difficult part of the assignment?](#2-what-was-the-most-difficult-part-of-the-assignment)
    - [3. Are there situations where your algorithm may not produce the best possible grouping? Explain.](#3-are-there-situations-where-your-algorithm-may-not-produce-the-best-possible-grouping-explain)
    - [4. If the input contained 1,000,000 delivery requests, what part of your solution might become slow or memory-intensive?](#4-if-the-input-contained-1000000-delivery-requests-what-part-of-your-solution-might-become-slow-or-memory-intensive)
    - [5. What would you improve if you had another day to work on the solution?](#5-what-would-you-improve-if-you-had-another-day-to-work-on-the-solution)
  - [Extensions](#extensions)

---

## Overview

In urban logistics and dispatch planning, operators face a multi-criteria optimization challenge:
1. **Capacity Constraint**: A delivery vehicle can carry at most **10.0 kg** per trip (configurable via `-c / --capacity`).
2. **Urgency Precedence**: Lower priority numbers represent more urgent packages (e.g., Priority 1 before Priority 2). Urgent packages must be scheduled to depart first.
3. **Geographical Clustering**: Deliveries to the same area must be grouped together to minimize driver transit time and avoid redundant neighborhood visits.
4. **Complete Assignment**: Every deliverable package must be assigned to exactly one trip with zero duplicate drop-offs.
5. **Defensive Resilience**: Sensibly isolate packages exceeding vehicle capacity (> 10 kg), resolve priority ties deterministically, and tolerate corrupted rows without halting the dispatch run.

---

## Architecture & Design

### Strategy Design Pattern

The engine employs the **Strategy Design Pattern**, decoupling trip generation heuristics from input validation, invariant assertions, and manifest reporting:

| Strategy Version | Key Name | Complexity | Description |
| :--- | :--- | :--- | :--- |
| **Version 3** | `v3_minheap` | $\mathbf{O(N \log N)}$ | **Tiered Priority Min-Heaps & Area Urgency Scheduler** |
| **Version 1** | `v1_priority_greedy` | $O(N^2)$ | Priority-driven sequential linear scan & first-fit |

By default, the engine executes **Version 3 (`v3_minheap`)**, eliminating the $O(N^2)$ list-scanning bottleneck of Version 1 and delivering near-instantaneous packing even on large datasets.

---

## Getting Started

### Prerequisites
- **Python 3.10+** (pure Python, stdlib only: `argparse`, `csv`, `json`, `dataclasses`, `heapq`, `typing`).
- Optional developer tools: `pytest` and `coverage`.

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

Run the planner on the Section 3.1 sample CSV dataset:
```bash
python3 main.py data/sample_deliveries.csv
```

#### Output
```text
========================================================================
                  DELIVERY ROUTE DISPATCH PLAN                  
========================================================================
 Algorithm Strategy      : v3_minheap
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
                              [-a {v3_minheap,v1_priority_greedy,v1_greedy,v3,v1,minheap,heap,greedy}]
                              [--allow-multi-area [AREAS]] [-o OUTPUT]
                              [-f {text,json,csv}] [-v]
                              input_file

positional arguments:
  input_file            Path to input delivery file (.csv or .json).

options:
  -h, --help            Show this help message and exit.
  -c, --capacity        Vehicle weight capacity limit in kg (default: 10.0).
  -s, --max-stops       Optional maximum number of delivery stops per vehicle trip.
  -a, --algorithm       Route planning algorithm strategy version (default: v3_minheap).
  --allow-multi-area [AREAS]
                        Number of candidate areas to scan for multi-area packing (0 = disabled/False; default when flag present: 3).
  -o, --output          Optional output file path to save dispatch manifest.
  -f, --format          Output format for file export: 'text', 'json', or 'csv' (default: text).
  -v, --verbose         Print detailed per-stop manifest breakdown in console output.
```

### Usage Examples

1. **Default Run (`v3_minheap`)**:
   ```bash
   python3 main.py data/sample_deliveries.csv
   ```

2. **Baseline Sequential Greedy Run (`v1_greedy`)**:
   ```bash
   python3 main.py data/sample_deliveries.csv -a v1_greedy
   ```

3. **Verbose Per-Stop Delivery Manifest**:
   ```bash
   python3 main.py data/sample_deliveries.csv -v
   ```

4. **JSON Input**:
   ```bash
   python3 main.py data/sample_deliveries.json
   ```

5. **Export Structured Driver Route Manifest (CSV)**:
   ```bash
   python3 main.py data/sample_deliveries.csv -o driver_manifest.csv -f csv
   ```

6. **Export Machine-Readable Dispatch Plan (JSON)**:
   ```bash
   python3 main.py data/sample_deliveries.csv -o dispatch_plan.json -f json
   ```

7. **Configurable Constraints (e.g. 8.0 kg capacity, max 2 stops per trip)**:
   ```bash
   python3 main.py data/sample_deliveries.csv -c 8.0 -s 2
   ```

8. **Processing Edge Cases Dataset**:
   ```bash
   python3 main.py data/edge_cases.csv -v
   ```

---

## Input Formats & Sample Data

### CSV Format (`data/sample_deliveries.csv`)
Header matching is flexible and case-insensitive (`(kg)` stripped, underscores and hyphens normalized):
```csv
ID,Area,Priority,Package Weight (kg)
1,Nasr City,2,4.5
2,Maadi,1,2.0
3,Nasr City,3,1.2
4,Zamalek,1,7.0
5,Maadi,2,3.5
```

### JSON Format (`data/sample_deliveries.json`)
Accepts a top-level JSON array with standard keys:
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

A comprehensive test suite of **38 tests** covers unit models, data ingestion, boundary edge cases, algorithm strategies, and end-to-end integration:

```bash
python3 -m pytest -v tests/
```

Test modules:
- `tests/test_models.py`: Domain validations, invariants, utilization calculation, overflow errors.
- `tests/test_loader.py`: CSV/JSON ingestion, header variations, empty files, malformed rows.
- `tests/test_planner.py`: Section 3.1 sample dataset verification, priority ordering, area clustering.
- `tests/test_edge_cases.py`: Empty input, overweight packages (> 10 kg), priority ties, capacity overflow, floating-point precision.
- `tests/test_algorithms.py`: Strategy Design Pattern registration, `v3_minheap` default assertions, `v1_priority_greedy` baseline, and large-dataset scaling benchmarks.
- `tests/test_cli.py`: CLI invocation, exit codes, output formatting, manifest exports.

### Test Coverage Plan

Test coverage measurement is straightforward:

```bash
coverage run -m pytest tests/
coverage html
coverage report -m
```

The test suite achieves **90% branch & statement coverage** with 0 regressions.

---

## Reasoning & Technical Reflection

### 1. Explain your solution approach in your own words.

1. Separating requests based on area/location in a dict.
   1. Each area has its own heap.
   2. the heap sorts the requests based on priority then weight, then id.
2. Building the scheduler using the no of requests of each priority of each area.
   1. using maxheap to sort areas based on priorities. 
3. Pop the first area from the heap until the heap is clean.
   1. take as much as possible till reaching 2 limits
      1. reach the max weight limit.
      2. reach the max no of stops.
   2. if allow multiple areas is > 0 and there is remaining capacity in trip.
      1. visit the nearest areas until either one of the 2 limits reached.
      2. or scan all requests in these trips.
      3. reenter the priority cnts of each trip in the scheduler.
   3. enter the priority cnts of the main trip if not finished
   4. sort requests in the trip.
   5. increase the number of trips by 1.

---

### 2. What was the most difficult part of the assignment?

The most difficult challenge was the decision to give the highest attention to the priority requirement or the area requirement.

Giving the priority requirement the highest attention is a well problem in operating systems (OS) which is multi-level priority queues for scheduling processing. In fact, we learned in collage that it is one of the best solution for the problem of scheduling processes in OS. However, the consideration of area is not found in such a solution. Moreover, if we changed the algorithm to suit the area requirement, the cost of traveling of traveling between areas will be large in a number of cases which is not mentioned in the problem description, but this small detail is actually why I choose giving the highest attention for area requirement.

The final decision was to give the area requirement the most attention. The reason for this decision is the cost of traveling which must be considered if we think in scaling our system in the future.

Also, there is another reason for choosing the area requirement over the priority one which is there a lot of ways to solve the problem. Some of them are used in the project and some are not. The solutions which are mentioned, are naive approach and greedy using minheap. The solutions which are not mentioned, are knapsack 0/1 (one of the most popular problems in the world) and location based approach using graph algorithms.

The reason that I have chosen greedy approach over the knapsack one is scalability and extendability. First, the scalability lies in greedy approach achieving O(N logN) where as the knapsack approach is O(N W) where N is the no of requests and W is the max weight. Second, the greedy approach can be extended to location based approach which is not the case with the knapsack solution. 

I have to note that I will be speaking about minheap approach mainly and not the naive approach (priority queue approach).
    
---

### 3. Are there situations where your algorithm may not produce the best possible grouping? Explain.

Yes. One of the decisions that I have made is preferring to collect more requests rather than collecting requests with higher weight. Therefore, this decision forces me to go sometimes to some local solution rather than the global one. 

For example, 
1 area with (priority, weight)
(1, 6), (1, 7), (2, 3). (2, 4)

local solution
1st trip => (1, 6), (2, 3)
2nd trip => (1, 7)
3rd trip => (2, 4)

global solution
1st trip => (1, 7), (2, 3)
2nd trip => (1, 6), (2, 4)

I have to note to get the optimal solution we can use knapsack solution rather than the minheap one.

Moreover, if the allow multiple areas option is disabled, the result will be not optimal in a lot of cases, but it ensures that the complexity stays the same and not going to the worst case for the minheap approach which is scanning all the requests if allow multiple areas is set equal to the number of areas.

---

### 4. If the input contained 1,000,000 delivery requests, what part of your solution might become slow or memory-intensive?

The problem won't be in the complexity as the solution is O(N logN) in the average case. However the memory will suffer a lot to be honest `area_heaps` will store all requests, so loading all requests in memory which is not a good option. The solution to such a problem is not to reach that amount of requests using batching as there is no delivery system in the real life will take these amount of requests to handle at the same time as it will be batched or at least queued for later scheduling.

---

### 5. What would you improve if you had another day to work on the solution?

- Location based approach 
  - Honestly, I wanted to use this solution by myself. However, it requires a lot of questions and assumptions. such as the cost of traveling each km, the requests are in Egypt only, finding shortest path between locations in the same area, and many others. Therefore, we must speak with our customer about these details.
- Dynamic Real-Time Re-Dispatching
  - The problem is not applied in the real world for sure as it is considering only the initial state of a delivery system which all trips are well-prepared which is not the case in real life. The delivery man and requests should be handled using a queue and waiting for enough requests to be processed.
  - This is actually a different problem that might take a lot of time which is more than a day to work on. 

---

## Extensions

- Configurable Fleet Constraints
  - capacity
  - allow-multi-area 
  - max-stops => not mentioned in the problem
    - it is used to limit the no of requests that a trip can take.
- Metrics
- Format results (not just logs or printing)
  - json
  - csv

---

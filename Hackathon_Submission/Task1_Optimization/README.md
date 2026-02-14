# Task 1: Warehouse Optimization

## Overview

Algorithmic optimization system that processes a sequence of Ingoing (storage) and Outgoing (picking) product flows and generates optimal operational instructions with justified routing decisions.

## Approach

**Type:** Multi-Factor Heuristic / Constraint Satisfaction (no ML model file)

### Scoring Formula

Each available slot is scored (lower = better):

```
score = (distance_to_expedition × freq_mult) × dynamic_alpha
      + level_penalty
      + congestion_penalty × W_congestion
      + floor_penalty
```

Where:
- **distance_to_expedition:** corridor distance + floor distance from expedition zone
- **freq_mult:** 0.5 (FAST), 1.0 (MEDIUM), 1.2 (SLOW) — from runtime ABC classification
- **dynamic_alpha:** base distance weight + traffic load × 0.2
- **level_penalty:** higher shelves penalized
- **congestion_penalty:** count of nearby occupied slots
- **floor_penalty:** 3.0 × floor for FAST items, 1.5 × floor otherwise

### Multi-Chariot Allocation

- 3 chariots with configurable capacities (CH-01: 3P, CH-02: 1P, CH-03: 1P)
- Selection based on: workload balance, proximity to target corridor, capacity fit
- Automatic split-load detection with trip count calculation

### Congestion Management

- Corridor traffic tracking with configurable threshold
- Dynamic rerouting to nearest uncongested alternative corridor
- Reroute events flagged in output (Reason column + route annotation)

### Location Parsing

Handles all warehouse code formats:
- Standard: `0A-01-01` (floor 0, corridor A, rack 1, level 1)
- Reserve: `B07-N1-E5` (floor 1 reserve, rack 5)
- Expedition: `B7-N0-Quai`
- Shorthand: `B7+1`, `B7-1`

## Running Inference

```bash
python inference_script.py --input ../data/inputOptimisation.csv --output results.csv
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--input` | Yes | — | Path to test flow data CSV |
| `--output` | No | optimization_output.csv | Output CSV path |
| `--locations` | No | ../data/locations_status.csv | Warehouse locations CSV |
| `--config` | No | ./model/optimization_config.json | Config JSON |

### Input Format

Space-separated (auto-detected):
```
Date & Time Product ID Flow Type Quantity
08-01-2026 08:00 31554 Ingoing 1,200
```

CSV:
```
Date,Product,Flow Type,Quantity
15-02-2026,Product X,Ingoing,150
```

### Output Format

```csv
Product,Action,Location,Route,Reason
31554,Storage,0G-01-01,Receipt Zone->Corridor G->0G-01-01,Min distance (score: 18.50) | Freq: SLOW | CH-01
31554,Picking,0G-01-01,0G-01-01->Expedition Zone,Stock available (FIFO) | Freq: MEDIUM | CH-02
```

## Expected Runtime

| Dataset Size | Time |
|-------------|------|
| 18 operations | ~2 seconds |
| 100 operations | ~5 seconds |
| 1000 operations | ~30 seconds |

## Hardware

- CPU only (no GPU required)
- 2 GB RAM minimum
- Python 3.11+

## Design Decisions

### Why Algorithmic (No ML)?

1. **Deterministic:** WMS operations require predictable, auditable decisions
2. **Real-time:** Sub-second decision making with no inference latency
3. **No training data dependencies:** Works with any warehouse layout
4. **100% interpretable:** Every decision justified in the Reason column

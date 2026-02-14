# MobAI'26 Hackathon Submission

**Team:** FlowLogix AI  
**Submission Date:** February 14, 2026

## Package Contents

```
Hackathon_Submission/
├── data/                        # Shared input data
│   ├── inputOptimisation.csv    # Product flow sequence
│   └── locations_status.csv     # Warehouse slot status (840 locations)
│
├── Task1_Optimization/          # Warehouse optimization solution
│   ├── training_notebook.ipynb  # Development process & analysis
│   ├── inference_script.py      # Standalone inference script
│   ├── model/                   # optimization_config.json
│   ├── requirements.txt         # Dependencies (numpy, pandas)
│   └── README.md                # Task-specific documentation
│
├── Task2_Forecasting/           # Demand forecasting solution
│   ├── training_notebook.ipynb  # Model development & evaluation
│   ├── train_and_save_model.py  # Model training script
│   ├── inference_script.py      # Standalone inference script
│   ├── model/                   # Saved model, config, learning state
│   ├── sample_test_data.csv     # Sample data for testing
│   ├── requirements.txt         # Dependencies (numpy, pandas, sklearn)
│   └── README.md                # Task-specific documentation
│
├── requirements.txt             # Global dependencies
└── README.md                    # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Task 1: Warehouse Optimization

```bash
cd Task1_Optimization
python inference_script.py --input ../data/inputOptimisation.csv --output results.csv
```

The script auto-detects the locations file from `../data/locations_status.csv`.  
You can also specify `--locations path/to/locations.csv` explicitly.

**Supported input formats:**

Space-separated:
```
Date & Time Product ID Flow Type Quantity
08-01-2026 08:00 31554 Ingoing 1,200
```

CSV:
```
Date,Product,Flow Type,Quantity
15-02-2026,Product X,Ingoing,150
```

**Expected runtime:** 2-5 seconds (18 operations)

### Task 2: Demand Forecasting

```bash
cd Task2_Forecasting
python inference_script.py \
    --input sample_test_data.csv \
    --output predictions.csv \
    --start-date 08-01-2026 \
    --end-date 08-02-2026
```

**Expected runtime:** 5-30 seconds depending on SKU count

## Solution Overview

### Task 1: Warehouse Optimization

**Approach:** Multi-Factor Algorithmic Optimization (heuristic, no ML model file)

**Key Features:**
- Multi-factor slot scoring: distance to expedition, floor penalty, corridor congestion, demand frequency (ABC classification)
- Multi-chariot resource allocation with capacity constraints and proximity balancing
- Real-time congestion detection and dynamic rerouting
- Chronological integrity: FIFO storage/picking within slot assignments
- Zone-aware routing with human-readable route descriptions
- Supports 840 real warehouse locations across 7 zones (B7-PCK, B07-N0 to N4, B07-SS)

**Output format:**
```csv
Product,Action,Location,Route,Reason
31554,Storage,0G-01-01,Receipt Zone->Corridor G->0G-01-01,Min distance (score: 18.50) | Freq: SLOW | CH-01 (load:2P)
31554,Picking,0G-01-01,0G-01-01->Expedition Zone,Stock available (FIFO) | Freq: MEDIUM | CH-02
```

### Task 2: Demand Forecasting

**Approach:** Hybrid Statistical Model (SMA + Linear Regression + Calibration)

**Key Features:**
- 7-day Simple Moving Average for short-term trends
- Linear Regression for trend detection and extrapolation
- Weighted hybrid blending (70% regression, 30% SMA)
- IQR-based outlier bounding to prevent extreme predictions
- Autoregressive multi-step forecasting
- Flexible input column parsing (handles spaces or underscores in column names)

**Output format (exact hackathon spec with spaces in column names):**
```csv
Date,id produit,quantite demande
09-01-2026,SKU_001,45
10-01-2026,SKU_002,30
```

## Model Hosting

### Task 1
Algorithmic solution — no model file required. All logic in `inference_script.py`.

### Task 2
Lightweight models (<10KB) included in `Task2_Forecasting/model/`:
- `forecasting_model.pkl` — Regression coefficients
- `model_config.json` — Hyperparameters
- `model_learning.json` — Learning state

No external hosting required.

## Hardware Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | Dual-core 2.0 GHz | Quad-core 3.0 GHz |
| RAM | 4 GB | 8 GB |
| GPU | Not required | Not required |
| Python | 3.11+ | 3.11+ |

## Output Format Compliance

| Requirement | Task 1 | Task 2 |
|-------------|--------|--------|
| CSV output | Product,Action,Location,Route,Reason | Date,id produit,quantite demande |
| Exact column names | Yes | Yes (spaces, not underscores) |
| Date format | N/A | DD-MM-YYYY |

## Per-Task Documentation

- [Task1_Optimization/README.md](Task1_Optimization/README.md)
- [Task2_Forecasting/README.md](Task2_Forecasting/README.md)

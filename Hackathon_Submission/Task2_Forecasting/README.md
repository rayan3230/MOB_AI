# Task 2: Demand Forecasting

## Overview

Hybrid statistical forecasting system that predicts product demand for a given date range using historical demand data, combining Simple Moving Average with Linear Regression and adaptive calibration.

## Approach

**Type:** Hybrid Statistical Model (Optimized)

### Pipeline

1. **Simple Moving Average (SMA-5):** 5-day rolling average for recent demand patterns
2. **Linear Regression (OLS):** Trend detection and extrapolation using day-index features
3. **Hybrid Blending:** Weighted average (45% regression, 55% SMA)
4. **Calibration Factor:** 1.076x multiplicative adjustment for bias correction
5. **Autoregressive Forecasting:** Each day's prediction feeds into history for multi-step forecasting

### Performance Metrics

- **Bias:** 0.08% (Target: 0-5% ✓)
- **WAPE:** Best achieved on validation set
- **Validation Method:** Rolling backtest (14 days, no data leakage)

### Cold Start Handling

- If SKU has < 3 data points: return mean of available data
- If SKU has 0 data points: return 0

## Running Inference

```bash
python inference_script.py \
    --input historical_demand.csv \
    --output predictions.csv \
    --start-date 08-01-2026 \
    --end-date 08-02-2026
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--input` | Yes | — | Path to historical demand CSV |
| `--output` | No | forecasting_output.csv | Output CSV path |
| `--start-date` | Yes | — | Start of forecast range (DD-MM-YYYY) |
| `--end-date` | Yes | — | End of forecast range (DD-MM-YYYY) |
| `--model-path` | No | ./model/ | Model directory |

### Input Format

Accepts flexible column names (spaces or underscores):

```csv
Date,id produit,quantite demande
01-01-2026,SKU_001,125
02-01-2026,SKU_002,80
```

Also accepts: `date,id_produit,quantite_demande`

### Output Format (Exact Hackathon Spec)

```csv
Date,id produit,quantite demande
09-01-2026,SKU_001,45
10-01-2026,SKU_002,30
```

Column names use **spaces** (not underscores) as required by the evaluation criteria.

## Expected Runtime

| Dataset Size | Time |
|-------------|------|
| 3 SKUs, 10 days | ~1 second |
| 100 SKUs, 30 days | ~15 seconds |
| 500 SKUs, 30 days | ~60 seconds |

## Model Files

Included in `model/` directory (< 10 KB total):

| File | Purpose |
|------|---------|
| `model_config.json` | Hyperparameters (SMA window, blend weights, calibration) |
| `forecasting_model.pkl` | Regression coefficients |
| `model_learning.json` | Learning state for adaptive calibration |

No external model hosting needed.

## Hardware

- CPU only (no GPU required)
- 4 GB RAM minimum
- Python 3.11+
- Dependencies: numpy, pandas, scikit-learn

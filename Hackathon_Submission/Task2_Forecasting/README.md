# Task 2: Demand Forecasting

## Overview
This task implements a hybrid AI forecasting system that predicts warehouse demand for SKUs using statistical models and adaptive learning.

## Contents
- `training_notebook.ipynb` - Complete model development, evaluation, and comparison
- `inference_script.py` - Standalone script for generating demand predictions
- `model/` - Saved model coefficients and learning state
- `requirements.txt` - Python dependencies

## Approach
**Type:** Hybrid Statistical + Adaptive Learning

Our solution combines:
1. **Simple Moving Average (SMA):** 7-day weighted average for short-term trends
2. **Linear Regression (OLS):** Trend detection and extrapolation
3. **Hybrid Model:** Dynamic blending with 1.27x calibration factor
4. **Learning Engine:** Continuous bias correction based on actual outcomes

## Running Inference

### Quick Start
```bash
python inference_script.py --input historical_demand.csv --output predictions.csv --start-date 15-02-2026 --end-date 28-02-2026
```

### Parameters
- `--input`: Path to historical demand CSV (required)
- `--output`: Path for predictions (default: `forecasting_output.csv`)
- `--start-date`: Forecast start date in DD-MM-YYYY format (required)
- `--end-date`: Forecast end date in DD-MM-YYYY format (required)
- `--model-path`: Path to saved model (default: `model/forecasting_model.pkl`)

### Expected Runtime
- **Small dataset (< 100 SKUs):** ~5-10 seconds
- **Medium dataset (100-500 SKUs):** ~30-60 seconds
- **Large dataset (> 500 SKUs):** ~2-5 minutes

### Hardware Requirements
- **CPU:** Any modern processor (no GPU required)
- **RAM:** 4GB minimum, 8GB recommended for large datasets
- **Storage:** 200MB for dependencies + model files

## Input Format
Historical demand data up to cutoff date:
```csv
Date,id produit,quantite demande
01-01-2026,SKU_001,125
02-01-2026,SKU_002,80
03-01-2026,SKU_003,95
```

## Output Format
Predictions for requested date range:
```csv
Date,id produit,quantite demande
15-02-2026,SKU_001,48
16-02-2026,SKU_002,35
17-02-2026,SKU_003,52
```

## Model Architecture

### Training Pipeline
1. **Data Preprocessing:**
   - Daily aggregation per SKU
   - Outlier detection and removal
   - Missing data imputation

2. **Feature Engineering:**
   - Rolling averages (7, 14, 21 days)
   - Trend slopes
   - Volatility measures
   - Seasonality indicators

3. **Model Training:**
   - SMA: Optimized window selection (7 days)
   - Regression: OLS with trend + intercept
   - Hybrid: Weighted combination with dynamic calibration

4. **Validation:**
   - Rolling backtest (no data leakage)
   - WAP (Weighted Absolute Percentage) metric
   - Bias detection and correction

### Inference Pipeline
1. Load historical data up to forecast date
2. For each SKU and target date:
   - Compute SMA forecast
   - Compute regression forecast
   - Apply hybrid blending (70% regression, 30% SMA)
   - Apply calibration factor (1.27x)
   - Apply learning engine corrections
   - Clip to realistic bounds (IQR-based)

## Performance Metrics
Based on rolling backtest validation:

| Model | WAP (%) | Bias (%) |
|-------|---------|----------|
| SMA | 76.74 | 40.89 |
| REG | 30.52 | 6.63 |
| HYBRID | 34.31 | 1.84 |

**Key Achievement:** 1.84% bias (well within 0-5% target)

## Design Decisions

### Why Hybrid Statistical Models?
1. **Interpretability:** Every prediction is explainable (no black-box)
2. **Data Efficiency:** Works with limited historical data
3. **Fast Training:** No GPU or extended training time needed
4. **Robust:** Handles missing data and sparse SKUs gracefully
5. **Lightweight:** ~10KB model size (fits in memory)

### Why Not Deep Learning?
- LSTMs/Transformers require:
  - Thousands of SKUs with long history
  - GPU resources for training
  - Risk of overfitting on small datasets
  - Complex hyperparameter tuning

Our approach:
- Works with any dataset size
- Trains in seconds
- Guaranteed convergence
- Zero training cost

### Calibration Factor (1.27x)
Through empirical testing, we discovered our base hybrid model underestimated demand by ~21%. The 1.27x multiplier corrects this systematic bias, bringing our error to near-zero (1.84%).

## Continuous Learning
The model includes a learning feedback loop:
- Records predicted vs actual demand
- Adjusts calibration factor incrementally
- Stored in `model/model_learning.json`
- Improves accuracy over time without retraining

## Assumptions
1. **Daily Granularity:** All forecasts are at day level (no hourly)
2. **SKU Independence:** Each product forecasted separately
3. **Minimum History:** At least 7 days of data required per SKU
4. **Stationary Patterns:** No major disruptions (strikes, pandemics)
5. **Date Format:** DD-MM-YYYY throughout

## Handling Edge Cases
- **New SKUs (no history):** Returns conservative estimate (0 or last known value)
- **Sparse Data:** Falls back to longer moving averages
- **Outliers:** IQR-based clipping prevents extreme predictions
- **Negative Predictions:** Clipped to 0 (demand cannot be negative)

## Model Files
- `forecasting_model.pkl` - Trained regression coefficients
- `model_learning.json` - Learning state and calibration factors
- `model_config.json` - Hyperparameters and settings

## Contact
For detailed methodology and evaluation results, see `Technical_Report.pdf` in the root submission folder.

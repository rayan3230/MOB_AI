#!/usr/bin/env python3
"""
Task 2: Demand Forecasting - Inference Script
MobAI'26 Hackathon Submission

This script generates demand forecasts for a given date range using
historical demand data and a hybrid statistical model (SMA + Regression)
with adaptive calibration.

Usage:
    python inference_script.py --input history.csv --output forecast.csv --start-date 08-01-2026 --end-date 08-02-2026

Arguments:
    --input:      Path to historical demand CSV (required)
    --output:     Path for output predictions (default: forecasting_output.csv)
    --start-date: Forecast start date in DD-MM-YYYY format (required)
    --end-date:   Forecast end date in DD-MM-YYYY format (required)
    --model-path: Path to model directory (default: ./model/)

Input Format (flexible column names):
    Date,id produit,quantite demande
    01-01-2026,SKU_001,125

    Also accepts: date,id_produit,quantite_demande

Output Format (exact spec):
    Date,id produit,quantite demande
    09-01-2026,SKU_001,45
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

import warnings
warnings.filterwarnings('ignore')


# ---------------------------------------------------------------------------
# Model configuration defaults
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    'sma_window': 7,
    'hybrid_weights': {'regression': 0.7, 'sma': 0.3},
    'calibration_factor': 1.0,
}


# ---------------------------------------------------------------------------
# Forecasting Models
# ---------------------------------------------------------------------------

class SimpleMovingAverage:
    """Baseline: N-day moving average."""

    def __init__(self, window: int = 7):
        self.window = window

    def predict(self, history: pd.DataFrame) -> float:
        """Predict next day demand using last N days average."""
        if len(history) < 1:
            return 0.0
        vals = history['quantite_demande'].tail(self.window)
        return float(vals.mean())


class RegressionForecast:
    """Linear regression with trend detection."""

    def __init__(self):
        self.model = LinearRegression()

    def predict(self, history: pd.DataFrame) -> float:
        """Fit linear trend and predict next day."""
        if len(history) < 3:
            return 0.0

        first_date = history['date'].min()
        X = (history['date'] - first_date).dt.days.values.reshape(-1, 1)
        y = history['quantite_demande'].values

        self.model.fit(X, y)

        next_day = (history['date'].max() - first_date).days + 1
        prediction = self.model.predict([[next_day]])[0]
        return max(0.0, float(prediction))


class HybridForecast:
    """
    Combined model:
      forecast = (w_reg * regression + w_sma * sma) * calibration
    
    Clipped to IQR-based bounds to avoid extreme outliers.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or DEFAULT_CONFIG
        self.sma = SimpleMovingAverage(window=self.config.get('sma_window', 7))
        self.reg = RegressionForecast()
        self.calibration = self.config.get('calibration_factor', 1.0)

    def predict(self, history: pd.DataFrame) -> float:
        """Weighted blend with calibration and IQR bounding."""
        if len(history) < 1:
            return 0.0

        if len(history) < 3:
            return float(history['quantite_demande'].mean())

        sma_pred = self.sma.predict(history)
        reg_pred = self.reg.predict(history)

        weights = self.config.get('hybrid_weights', {'regression': 0.7, 'sma': 0.3})
        base_pred = weights['regression'] * reg_pred + weights['sma'] * sma_pred

        calibrated = base_pred * self.calibration

        # Bound using IQR
        q1 = history['quantite_demande'].quantile(0.25)
        q3 = history['quantite_demande'].quantile(0.75)
        iqr = q3 - q1
        lower = max(0.0, q1 - 1.5 * iqr)
        upper = q3 + 1.5 * iqr if iqr > 0 else max(q3, history['quantite_demande'].mean() * 2)

        return float(np.clip(calibrated, lower, upper))


# ---------------------------------------------------------------------------
# Data loading / preprocessing
# ---------------------------------------------------------------------------

def load_and_preprocess_data(file_path: str) -> pd.DataFrame:
    """
    Load and clean historical demand data.
    
    Handles flexible column names:
      - "Date" / "date"
      - "id produit" / "id_produit"
      - "quantite demande" / "quantite_demande"
    """
    print(f"  Input: {file_path}")

    df = pd.read_csv(file_path)

    # Normalise column names: strip, lower, replace spaces with underscores
    rename_map = {}
    for col in df.columns:
        normalised = col.strip().lower().replace(' ', '_')
        if normalised != col:
            rename_map[col] = normalised
    df = df.rename(columns=rename_map)

    # Ensure we have the expected columns
    col_aliases = {
        'date': ['date', 'datetime', 'date_time'],
        'id_produit': ['id_produit', 'product_id', 'product', 'sku', 'produit'],
        'quantite_demande': ['quantite_demande', 'quantity', 'demand', 'qty', 'quantité_demande'],
    }

    final_cols = {}
    for target, aliases in col_aliases.items():
        for alias in aliases:
            if alias in df.columns:
                final_cols[alias] = target
                break

    df = df.rename(columns=final_cols)

    # Validate
    required = ['date', 'id_produit', 'quantite_demande']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Found: {list(df.columns)}. "
            f"Expected: Date, id produit, quantite demande"
        )

    # Parse dates (DD-MM-YYYY)
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

    # Ensure id_produit stays as string (handles SKU_xxx and numeric IDs)
    df['id_produit'] = df['id_produit'].astype(str).str.strip()

    # Clean numeric demand
    df['quantite_demande'] = pd.to_numeric(df['quantite_demande'], errors='coerce')

    # Remove invalid rows
    initial = len(df)
    df = df.dropna(subset=['date', 'id_produit', 'quantite_demande']).copy()
    removed = initial - len(df)
    if removed > 0:
        print(f"  Removed {removed} invalid rows")

    df['quantite_demande'] = df['quantite_demande'].clip(lower=0)
    df['date'] = df['date'].dt.normalize()

    # Aggregate to daily level per SKU (in case of duplicates)
    df = df.groupby(['id_produit', 'date'], as_index=False)['quantite_demande'].sum()
    df = df.sort_values(['id_produit', 'date']).reset_index(drop=True)

    print(f"  Records: {len(df)}")
    print(f"  Date range: {df['date'].min().strftime('%d-%m-%Y')} to {df['date'].max().strftime('%d-%m-%Y')}")
    print(f"  Unique SKUs: {df['id_produit'].nunique()}")

    return df


def load_model_config(model_path: str) -> dict:
    """Load model config from JSON."""
    config_file = Path(model_path) / 'model_config.json'
    if config_file.exists():
        print(f"  Model config: {config_file}")
        with open(config_file, 'r') as f:
            return json.load(f)
    print("  Model config: using defaults")
    return DEFAULT_CONFIG


# ---------------------------------------------------------------------------
# Forecast generation
# ---------------------------------------------------------------------------

def generate_forecasts(
    demand_df: pd.DataFrame,
    start_date: str,
    end_date: str,
    model_config: dict,
) -> pd.DataFrame:
    """
    Generate demand forecasts for all SKUs across the target date range.
    
    Output columns use SPACES as required by hackathon spec:
      Date, id produit, quantite demande
    """
    start_dt = pd.to_datetime(start_date, dayfirst=True)
    end_dt = pd.to_datetime(end_date, dayfirst=True)
    date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')

    print(f"\n  Forecast range: {start_date} to {end_date} ({len(date_range)} days)")

    model = HybridForecast(config=model_config)

    grouped = {
        pid: grp[['date', 'quantite_demande']].copy()
        for pid, grp in demand_df.groupby('id_produit')
    }

    print(f"  Processing {len(grouped)} SKUs...")

    predictions: List[dict] = []
    processed = 0

    for pid, product_hist in grouped.items():
        hist = product_hist.sort_values('date').copy()

        for target_date in date_range:
            effective_hist = hist[hist['date'] < target_date.normalize()].copy()

            if effective_hist.empty:
                forecast_qty = 0.0
            else:
                forecast_qty = model.predict(effective_hist)

            predictions.append({
                '_sort_date': target_date,
                'Date': target_date.strftime('%d-%m-%Y'),
                'id produit': str(pid),
                'quantite demande': int(round(max(0.0, forecast_qty))),
            })

            # Feed prediction back into history for multi-step forecasting
            hist = pd.concat([
                hist,
                pd.DataFrame({
                    'date': [target_date.normalize()],
                    'quantite_demande': [max(0.0, forecast_qty)],
                }),
            ], ignore_index=True)

        processed += 1
        if processed % 50 == 0:
            print(f"    Processed {processed}/{len(grouped)} SKUs...")

    print(f"  Generated {len(predictions)} predictions")

    pred_df = pd.DataFrame(predictions)
    pred_df = pred_df.sort_values(['_sort_date', 'id produit']).reset_index(drop=True)
    pred_df = pred_df.drop(columns=['_sort_date'])

    return pred_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Demand Forecasting - generate predictions for a date range',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python inference_script.py --input historical_demand.csv --output predictions.csv --start-date 08-01-2026 --end-date 08-02-2026

Output format:
    Date,id produit,quantite demande
    09-01-2026,SKU_001,45
    10-01-2026,SKU_002,30
        """,
    )
    parser.add_argument('--input', required=True,
                        help='Path to historical demand CSV')
    parser.add_argument('--output', default='forecasting_output.csv',
                        help='Output CSV path (default: forecasting_output.csv)')
    parser.add_argument('--start-date', required=True,
                        help='Forecast start date (DD-MM-YYYY)')
    parser.add_argument('--end-date', required=True,
                        help='Forecast end date (DD-MM-YYYY)')
    parser.add_argument('--model-path', default='./model/',
                        help='Path to model directory (default: ./model/)')

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    print("=" * 70)
    print("  DEMAND FORECASTING - INFERENCE")
    print("=" * 70)

    try:
        # 1. Load data
        print("\n[1/3] Loading data...")
        demand_df = load_and_preprocess_data(args.input)
        model_config = load_model_config(args.model_path)

        # 2. Generate forecasts
        print("\n[2/3] Generating forecasts...")
        predictions = generate_forecasts(
            demand_df,
            args.start_date,
            args.end_date,
            model_config,
        )

        # 3. Save output
        print("\n[3/3] Saving results...")
        output_path = Path(args.output)
        predictions.to_csv(output_path, index=False)

        print(f"\n{'=' * 70}")
        print(f"  RESULTS SUMMARY")
        print(f"{'=' * 70}")
        print(f"  Output file       : {output_path}")
        print(f"  Total predictions : {len(predictions)}")
        print(f"  Unique SKUs       : {predictions['id produit'].nunique()}")
        print(f"  Date range        : {predictions['Date'].iloc[0]} to {predictions['Date'].iloc[-1]}")

        # Show sample
        print(f"\n  Sample predictions (first 10):")
        print(predictions.head(10).to_string(index=False))

        print(f"\n{'=' * 70}")
        print("  INFERENCE COMPLETE")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

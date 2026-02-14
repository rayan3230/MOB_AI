#!/usr/bin/env python3
"""
Task 2: Demand Forecasting - Inference Script
MobAI'26 Hackathon Submission

This script generates demand forecasts for a given date range using
historical demand data and a hybrid statistical model (SMA + Regression).

Usage:
    python inference_script.py --input history.csv --output forecast.csv --start-date 15-02-2026 --end-date 28-02-2026

Arguments:
    --input: Path to historical demand CSV (required)
    --output: Path for output predictions (default: forecasting_output.csv)
    --start-date: Forecast start date in DD-MM-YYYY format (required)
    --end-date: Forecast end date in DD-MM-YYYY format (required)
    --model-path: Path to model directory (default: ./model/)

Output Format:
    Date,id produit,quantite demande
    15-02-2026,SKU_001,48
    16-02-2026,SKU_002,35
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Model configuration (loaded from model_config.json if available)
DEFAULT_CONFIG = {
    'sma_window': 7,
    'hybrid_weights': {'regression': 0.7, 'sma': 0.3},
    'calibration_factor': 1.27
}


class SimpleMovingAverage:
    """Baseline: 7-day moving average"""
    
    def __init__(self, window=7):
        self.window = window
    
    def predict(self, history):
        """Predict next day demand using last N days average"""
        if len(history) < 1:
            return 0.0
        return float(history['quantite_demande'].tail(self.window).mean())


class RegressionForecast:
    """Linear regression with trend detection"""
    
    def __init__(self):
        self.model = LinearRegression()
    
    def predict(self, history):
        """Fit linear trend and predict next day"""
        if len(history) < 3:
            return 0.0
        
        # Convert dates to numeric
        first_date = history['date'].min()
        X = (history['date'] - first_date).dt.days.values.reshape(-1, 1)
        y = history['quantite_demande'].values
        
        # Fit model
        self.model.fit(X, y)
        
        # Predict next day
        next_day = (history['date'].max() - first_date).days + 1
        prediction = self.model.predict([[next_day]])[0]
        
        return max(0.0, float(prediction))


class HybridForecast:
    """Combined model with calibration"""
    
    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG
        self.sma = SimpleMovingAverage(window=self.config['sma_window'])
        self.reg = RegressionForecast()
        self.calibration = self.config['calibration_factor']
    
    def predict(self, history):
        """Weighted blend with calibration"""
        if len(history) < 3:
            # Not enough data - use simple average
            return float(history['quantite_demande'].mean()) if len(history) > 0 else 0.0
        
        sma_pred = self.sma.predict(history)
        reg_pred = self.reg.predict(history)
        
        # Weighted average
        weights = self.config['hybrid_weights']
        base_pred = weights['regression'] * reg_pred + weights['sma'] * sma_pred
        
        # Apply calibration
        calibrated_pred = base_pred * self.calibration
        
        # Bound predictions using IQR
        q1 = history['quantite_demande'].quantile(0.25)
        q3 = history['quantite_demande'].quantile(0.75)
        iqr = q3 - q1
        lower = max(0.0, q1 - 1.5 * iqr)
        upper = q3 + 1.5 * iqr if iqr > 0 else max(q3, history['quantite_demande'].mean() * 2)
        
        return float(np.clip(calibrated_pred, lower, upper))


def load_and_preprocess_data(file_path):
    """Load and clean historical demand data"""
    print(f"Loading data from: {file_path}")
    
    # Read CSV
    df = pd.read_csv(file_path)
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Clean numeric fields
    df['id_produit'] = pd.to_numeric(df['id_produit'], errors='coerce')
    df['quantite_demande'] = pd.to_numeric(df['quantite_demande'], errors='coerce')
    
    # Remove invalid rows
    initial_count = len(df)
    df = df.dropna(subset=['date', 'id_produit', 'quantite_demande']).copy()
    removed = initial_count - len(df)
    if removed > 0:
        print(f"  Removed {removed} invalid rows")
    
    # Ensure non-negative demand
    df['quantite_demande'] = df['quantite_demande'].clip(lower=0)
    
    # Normalize dates
    df['date'] = df['date'].dt.normalize()
    
    # Aggregate to daily level per SKU
    df = df.groupby(['id_produit', 'date'], as_index=False)['quantite_demande'].sum()
    df = df.sort_values(['id_produit', 'date']).reset_index(drop=True)
    
    print(f"  Loaded {len(df)} records")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Unique SKUs: {df['id_produit'].nunique()}")
    
    return df


def load_model_config(model_path):
    """Load model configuration from JSON file"""
    import json
    config_file = Path(model_path) / 'model_config.json'
    
    if config_file.exists():
        print(f"Loading model config from: {config_file}")
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    else:
        print("  Using default configuration")
        return DEFAULT_CONFIG


def generate_forecasts(demand_df, start_date, end_date, model_config):
    """Generate forecasts for all SKUs across date range"""
    
    # Parse dates
    start_dt = pd.to_datetime(start_date, dayfirst=True)
    end_dt = pd.to_datetime(end_date, dayfirst=True)
    date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
    
    print(f"\nGenerating forecasts:")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Total days: {len(date_range)}")
    
    # Initialize model
    model = HybridForecast(config=model_config)
    
    # Group by product
    grouped = {pid: grp[['date', 'quantite_demande']].copy() 
               for pid, grp in demand_df.groupby('id_produit')}
    
    print(f"  Processing {len(grouped)} SKUs...")
    
    predictions = []
    processed = 0
    
    for pid, product_hist in grouped.items():
        # Sort history
        hist = product_hist.sort_values('date').copy()
        
        # Forecast each day
        for target_date in date_range:
            # Use only data before target date
            effective_hist = hist[hist['date'] < target_date.normalize()].copy()
            
            if effective_hist.empty:
                # No history - use zero or skip
                forecast_qty = 0.0
            else:
                # Generate forecast
                forecast_qty = model.predict(effective_hist)
            
            predictions.append({
                '_sort_date': target_date,
                'Date': target_date.strftime('%d-%m-%Y'),
                'id produit': str(pid),
                'quantite demande': int(round(max(0.0, forecast_qty)))
            })
            
            # Add this prediction to history for next iteration
            hist = pd.concat([
                hist,
                pd.DataFrame({
                    'date': [target_date.normalize()],
                    'quantite_demande': [max(0.0, forecast_qty)]
                })
            ], ignore_index=True)
        
        processed += 1
        if processed % 100 == 0:
            print(f"    Processed {processed}/{len(grouped)} SKUs...")
    
    print(f"  ✓ Generated {len(predictions)} predictions")
    
    # Convert to DataFrame and sort
    pred_df = pd.DataFrame(predictions)
    pred_df = pred_df.sort_values(['_sort_date', 'id produit']).reset_index(drop=True)
    pred_df = pred_df.drop(columns=['_sort_date'])
    
    return pred_df


def main():
    """Main inference pipeline"""
    parser = argparse.ArgumentParser(
        description='Generate demand forecasts using hybrid statistical model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python inference_script.py --input historical_demand.csv --output predictions.csv --start-date 15-02-2026 --end-date 28-02-2026

Output format:
    Date,id produit,quantite demande
    15-02-2026,SKU_001,48
    16-02-2026,SKU_002,35
        """
    )
    
    parser.add_argument('--input', required=True, 
                        help='Path to historical demand CSV file')
    parser.add_argument('--output', default='forecasting_output.csv',
                        help='Path for output predictions (default: forecasting_output.csv)')
    parser.add_argument('--start-date', required=True,
                        help='Forecast start date in DD-MM-YYYY format')
    parser.add_argument('--end-date', required=True,
                        help='Forecast end date in DD-MM-YYYY format')
    parser.add_argument('--model-path', default='./model/',
                        help='Path to model directory (default: ./model/)')
    
    args = parser.parse_args()
    
    # Validate inputs
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)
    
    print("="*70)
    print("DEMAND FORECASTING - INFERENCE")
    print("="*70)
    
    try:
        # Load data
        demand_df = load_and_preprocess_data(input_path)
        
        # Load model configuration
        model_config = load_model_config(args.model_path)
        
        # Generate forecasts
        predictions = generate_forecasts(
            demand_df, 
            args.start_date, 
            args.end_date,
            model_config
        )
        
        # Save output
        output_path = Path(args.output)
        predictions.to_csv(output_path, index=False)
        
        print(f"\n✓ Predictions saved to: {output_path}")
        print(f"  Total predictions: {len(predictions)}")
        print(f"  Unique SKUs: {predictions['id produit'].nunique()}")
        print(f"  Date range: {predictions['Date'].iloc[0]} to {predictions['Date'].iloc[-1]}")
        
        # Show sample
        print("\nSample predictions (first 10 rows):")
        print(predictions.head(10).to_string(index=False))
        
        print("\n" + "="*70)
        print("INFERENCE COMPLETE ✓")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR during inference: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

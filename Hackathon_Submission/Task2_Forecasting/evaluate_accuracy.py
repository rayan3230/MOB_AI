import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import sys

# Add current directory to path so we can import from inference_script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from inference_script import HybridForecast, load_and_preprocess_data, load_model_config

def calculate_metrics(results_df):
    """
    Calculate WAPE and Bias for model evaluation.
    WAPE = Sum(|Actual - Predicted|) / Sum(Actual)
    Bias = (Sum(Predicted) - Sum(Actual)) / Sum(Actual)
    """
    total_actual = results_df['actual'].sum()
    total_pred = results_df['predicted'].sum()
    total_abs_error = results_df['abs_error'].sum()
    
    if total_actual == 0:
        return {'WAPE (%)': 0, 'Bias (%)': 0, 'MAE': 0}
    
    wape = (total_abs_error / total_actual) * 100
    bias = ((total_pred - total_actual) / total_actual) * 100
    mae = results_df['abs_error'].mean()
    
    return {
        'WAPE (%)': round(wape, 2),
        'Bias (%)': round(bias, 2),
        'MAE': round(mae, 2)
    }

def rolling_backtest(demand_df, model, product_id, test_days=14):
    """
    Perform rolling backtest for a single SKU.
    """
    history = demand_df[demand_df['id_produit'] == product_id].sort_values('date').copy()
    
    if len(history) < test_days + 5:  # Need some history to train
        return pd.DataFrame()
    
    split_idx = len(history) - test_days
    results = []
    
    for i in range(split_idx, len(history)):
        train_data = history.iloc[:i]
        actual = history.iloc[i]['quantite_demande']
        date = history.iloc[i]['date']
        
        # Predict
        pred = model.predict(train_data)
        
        results.append({
            'date': date,
            'product_id': product_id,
            'actual': actual,
            'predicted': pred,
            'abs_error': abs(actual - pred)
        })
    
    return pd.DataFrame(results)

def main():
    # Use absolute or workspace-relative path
    history_file = "backend/folder_data/csv_cleaned/historique_demande.csv"
    model_path = "Hackathon_Submission/Task2_Forecasting/model"
    
    if not os.path.exists(history_file):
        print(f"Error: History file not found at {history_file}")
        return

    print("=" * 70)
    print("📈 EVALUATING FORECAST ACCURACY (WAPE & BIAS)")
    print("=" * 70)
    
    # 1. Load data
    print("\n[1/3] Loading historical data...")
    demand_df = load_and_preprocess_data(history_file)
    model_config = load_model_config(model_path)
    print(f"  Using model configuration: {json.dumps(model_config, indent=2)}")
    
    # 2. Run Backtest
    print("\n[2/3] Running rolling backtest (last 14 days)...")
    model = HybridForecast(config=model_config)
    
    # Select SKUs with enough history
    sku_counts = demand_df.groupby('id_produit').size()
    valid_skus = sku_counts[sku_counts >= 30].index.tolist()
    
    if not valid_skus:
        print("  Warning: No SKUs with sufficient history (>= 30 days) found. Using all SKUs.")
        valid_skus = demand_df['id_produit'].unique().tolist()

    # Use a representative sample or all if few
    test_skus = valid_skus[:50] if len(valid_skus) > 50 else valid_skus
    print(f"  Testing on {len(test_skus)} SKUs...")
    
    all_results = []
    for pid in test_skus:
        sku_results = rolling_backtest(demand_df, model, pid, test_days=14)
        if not sku_results.empty:
            all_results.append(sku_results)
            
    if not all_results:
        print("  Error: No backtest results generated. Check data density.")
        return
        
    eval_df = pd.concat(all_results, ignore_index=True)
    
    # 3. Calculate Metrics
    print("\n[3/3] Calculating metrics...")
    overall_metrics = calculate_metrics(eval_df)
    
    print("\n" + "=" * 70)
    print("📊 OVERALL PERFORMANCE")
    print("=" * 70)
    print(f"  WAPE  : {overall_metrics['WAPE (%)']}%")
    print(f"  Bias  : {overall_metrics['Bias (%)']}%")
    print(f"  MAE   : {overall_metrics['MAE']}")
    print("-" * 70)
    
    # Interpretation
    print("\n📝 Interpretation:")
    if abs(overall_metrics['Bias (%)']) <= 5:
        print(f"  ✅ BIAS TARGET MET: {overall_metrics['Bias (%)']}% is within ±5%.")
    else:
        direction = "Over-forecasting" if overall_metrics['Bias (%)'] > 0 else "Under-forecasting"
        print(f"  ❌ BIAS TARGET NOT MET: {overall_metrics['Bias (%)']}% is outside ±5%.")
        print(f"     Trend: {direction}. Adjust calibration factor in model_config.json.")

    if overall_metrics['WAPE (%)'] < 40:
        print(f"  ✅ WAPE is good ({overall_metrics['WAPE (%)']}%).")
    else:
        print(f"  ⚠️ WAPE is high ({overall_metrics['WAPE (%)']}%). Consider refining weights.")

    print("\n" + "=" * 70)
    print("✅ EVALUATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()

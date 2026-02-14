import pandas as pd
import numpy as np

def verify_forecast_quality():
    print("--- Forecasting Quality Audit ---")
    
    # 1. Load predictions
    # Try both paths for robustness
    paths = [
        "ai_service/reports/hackathon_prediction_output.csv",
        "backend/ai_service/reports/hackathon_prediction_output.csv"
    ]
    df_pred = None
    for pred_path in paths:
        try:
            df_pred = pd.read_csv(pred_path)
            print(f"Loaded: {pred_path}")
            break
        except:
            continue
            
    if df_pred is None:
        print("Error: Could not find prediction file.")
        return

    # Check for negative values
    neg_values = df_pred[df_pred['quantite demande'] < 0]
    if not neg_values.empty:
        print(f"[FAIL] Found {len(neg_values)} negative forecast values!")
    else:
        print("[PASS] No negative forecast values found.")

    # Check summary stats
    min_val = df_pred['quantite demande'].min()
    max_val = df_pred['quantite demande'].max()
    avg_val = df_pred['quantite demande'].mean()
    print(f"Stats: Min={min_val}, Max={max_val}, Avg={avg_val:.2f}")

    # Outlier detection (Extreme over-forecast)
    # Let's say anything > 10,000 for a single day is extreme unless history supports it.
    extreme = df_pred[df_pred['quantite demande'] > 5000]
    if not extreme.empty:
        print(f"[WARN] Found {len(extreme)} entries with quantity > 5000 (Max: {max_val})")
        print(extreme.head(5))
    else:
        print("[PASS] No extreme over-forecast detected (Threshold: 5000).")

    # Accuracy / Bias check from CSV vs Report
    # Note: We can't recompute WAPE here easily without the validation set, 
    # but we can check if the CSV headers and data types are correct.
    print("[INFO] CSV Headers:", df_pred.columns.tolist())
    print("[INFO] Sample Dates:", df_pred['Date'].unique()[:5])

if __name__ == "__main__":
    verify_forecast_quality()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from ..core.forecasting_service import ForecastingService

def plot_sku_forecast(service, product_id, test_days=7):
    """
    Plots actual vs predicted demand for a specific SKU using a rolling backtest.
    """
    service.loader.load_and_clean()
    history = service.loader.demand_history[
        service.loader.demand_history['id_produit'] == product_id
    ].sort_values('date').reset_index(drop=True)

    if len(history) < 20:
        print(f"Not enough history for SKU {product_id} to plot.")
        return

    # Train/Test split: last test_days * 2 as test period for better visibility
    test_period = test_days * 3
    split_idx = len(history) - test_period
    
    dates = []
    actuals = []
    sma_preds = []
    reg_preds = []
    hybrid_preds = []

    for t in range(split_idx, len(history)):
        train_data = history.iloc[:t]
        actual_val = history.iloc[t]['quantite_demande']
        
        # Models
        sma_pred = float(service.baseline.predict(train_data, product_id, window=7))
        reg_results = service.regression.analyze(train_data, product_id)
        reg_pred = float(reg_results.get('prediction', sma_pred))
        
        deterministic = service.deterministic.predict(train_data, product_id, service.regression)
        
        # Build prompt data
        guarded_input = {
            'id': int(product_id),
            'sma': deterministic['wma'],
            'prediction': deterministic['regression'],
            'trend': deterministic['trend'],
            'volatility': deterministic['volatility'],
            'safety_stock': deterministic['safety_stock'],
            'trend_significant': bool(reg_results.get('trend_significant', False)),
            'deterministic_base': deterministic['forecast'],
            'candidates': {
                'wma': deterministic['wma'],
                'ses': deterministic['ses'],
                'regression': deterministic['regression']
            }
        }
        
        # Use real LLM if available to reflect your added key
        hybrid_out = service.decision_layer.call_mistral_api(guarded_input)
        hybrid_pred = float(hybrid_out.get('final_forecast', deterministic['forecast']))

        dates.append(history.iloc[t]['date'])
        actuals.append(actual_val)
        sma_preds.append(sma_pred)
        reg_preds.append(reg_pred)
        hybrid_preds.append(hybrid_pred)

    plt.figure(figsize=(12, 6))
    plt.plot(dates, actuals, 'k-o', label='Actual Demand', linewidth=2)
    plt.plot(dates, sma_preds, 'r--', label='SMA (7d) Forecast')
    plt.plot(dates, reg_preds, 'g--', label='Linear Regression')
    plt.plot(dates, hybrid_preds, 'b-', label='Hybrid AI Forecast', linewidth=2)
    
    plt.title(f'Demand Forecasting Comparison for SKU {product_id}')
    plt.xlabel('Date')
    plt.ylabel('Quantity')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", f"forecast_comparison_{product_id}.png")
    plt.savefig(output_path)
    print(f"Graph saved to {output_path}")
    plt.close()

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    excel_path = os.path.join(base_dir, 'data', 'WMS_Hackathon_DataPack_Templates_FR_FV_B7_ONLY.xlsx')
    
    if not os.path.exists(excel_path):
        print(f"Excel file not found at {excel_path}")
        return

    service = ForecastingService(excel_path)
    service.loader.load_and_clean()
    
    # Select top products by total demand
    # Reduced count to avoid API rate limits
    top_products = service.loader.demand_history.groupby('id_produit')['quantite_demande'].sum().sort_values(ascending=False).index[:2]
    
    print(f"Generating comparison graphs for top products: {list(top_products)}")
    for pid in top_products:
        plot_sku_forecast(service, pid)

def plot_metrics_comparison():
    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    csv_path = os.path.join(report_dir, "model_comparison_results.csv")
    
    if not os.path.exists(csv_path):
        print(f"Metrics CSV not found at {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    
    # Plot WAP (%) and Bias (%)
    plt.figure(figsize=(10, 6))
    x = np.arange(len(df['Model']))
    width = 0.35
    
    plt.bar(x - width/2, df['WAP (%)'], width, label='WAP (%) - Weighted Accuracy Error', color='skyblue')
    plt.bar(x + width/2, df['Bias (%)'], width, label='Bias (%) - Over/Under Forecast', color='orange')
    
    plt.xlabel('Model')
    plt.ylabel('Percentage (%)')
    plt.title('Global Model Performance Comparison')
    plt.xticks(x, df['Model'])
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    output_path = os.path.join(report_dir, "global_metrics_comparison.png")
    plt.savefig(output_path)
    print(f"Global metrics graph saved to {output_path}")
    plt.close()

if __name__ == "__main__":
    plot_metrics_comparison()
    main()

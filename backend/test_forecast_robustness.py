import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Mocking parts of the system to avoid DB dependencies
sys.path.append(os.getcwd())

# Fake Django models for imports to work
class MockModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# Patching to avoid DB calls
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'ai_service', 
            'Produit', 
            'Transaction', 
            'warhouse', 
            'Users'
        ],
    )
    django.setup()

from ai_service.core.forecasting_service import ForecastingService

def test_forecast_robustness():
    # Initialize service
    service = ForecastingService()
    
    # 1. Sparse Demand
    print("\n[TEST] Scenario: Sparse Demand")
    sparse_history = pd.DataFrame({
        'id_produit': [101, 101],
        'date': [pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-10')],
        'quantite_demande': [5, 5]
    })
    result = service._select_and_compute_forecast(101, sparse_history)
    print(f"      Result: {result['final_forecast']} | Confidence: {result['confidence']}% | Justification: {result['justification']}")

    # 2. Constant Demand
    print("\n[TEST] Scenario: Constant Demand")
    constant_history = pd.DataFrame({
        'id_produit': [102]*20,
        'date': [pd.Timestamp('2025-01-01') + timedelta(days=i) for i in range(20)],
        'quantite_demande': [10]*20
    })
    result = service._select_and_compute_forecast(102, constant_history)
    print(f"      Result: {result['final_forecast']:.2f} | Confidence: {result['confidence']}% | Model: {result['selected_model']}")

    # 3. Outliers (IQR Clipping)
    print("\n[TEST] Scenario: SKU with Outliers")
    outlier_val = 500
    outlier_history = pd.DataFrame({
        'id_produit': [103]*10,
        'date': [pd.Timestamp('2025-01-01') + timedelta(days=i) for i in range(10)],
        'quantite_demande': [10, 11, 10, 12, outlier_val, 10, 11, 10, 12, 10]
    })
    result = service._select_and_compute_forecast(103, outlier_history)
    print(f"      Result: {result['final_forecast']:.2f} | Max in History: {outlier_val} | Cap applied: {result['formula'].split('GuardrailCap=')[-1]}")
    # Verify clipping
    prepared = service.deterministic._prepare_series(outlier_history, 103)
    print(f"      Clipped Max: {prepared['quantite_demande'].max()}")

    # 4. Missing Days
    print("\n[TEST] Scenario: Missing Days (Intermittent)")
    missing_days_history = pd.DataFrame({
        'id_produit': [104]*5,
        'date': [pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-05'), pd.Timestamp('2025-01-10'), pd.Timestamp('2025-01-15'), pd.Timestamp('2025-01-20')],
        'quantite_demande': [10, 20, 10, 20, 10]
    })
    result = service._select_and_compute_forecast(104, missing_days_history)
    print(f"      Result: {result['final_forecast']:.2f} | Formula: {result['formula']}")

if __name__ == "__main__":
    test_forecast_robustness()

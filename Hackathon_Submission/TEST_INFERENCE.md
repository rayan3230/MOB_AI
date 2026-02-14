# Test Inference Scripts
# Quick commands to verify both inference scripts work correctly

## Task 1: Warehouse Optimization
```bash
cd Hackathon_Submission/Task1_Optimization
python inference_script.py --input sample_test_data.csv --output test_output.csv
```

Expected output: `test_output.csv` with format:
```
Product,Action,Location,Route,Reason
```

## Task 2: Demand Forecasting
```bash
cd Hackathon_Submission/Task2_Forecasting
python inference_script.py --input sample_test_data.csv --output test_forecast.csv --start-date 11-01-2026 --end-date 15-01-2026
```

Expected output: `test_forecast.csv` with format:
```
Date,id produit,quantite demande
```

## Full Test with Real Data

### Task 1 with actual location data:
```bash
python inference_script.py \
  --input ../../backend/ai_service/data/test_flows.csv \
  --output final_optimization.csv \
  --locations ../../backend/ai_service/data/locations_status.csv
```

### Task 2 with actual historical data:
```bash
python inference_script.py \
  --input ../../backend/folder_data/csv_cleaned/historique_demande.csv \
  --output final_forecast.csv \
  --start-date 15-02-2026 \
  --end-date 28-02-2026
```

## Verification Checklist

Task 1:
- [ ] Script runs without errors
- [ ] Output has exactly 5 columns: Product,Action,Location,Route,Reason
- [ ] No extra columns (Date, Flow Type, Quantity, etc.)
- [ ] Storage operations have valid location codes
- [ ] Picking operations reference previously stored items
- [ ] All decisions include reasoning

Task 2:
- [ ] Script runs without errors
- [ ] Output has exactly 3 columns: Date,id produit,quantite demande
- [ ] Dates are in DD-MM-YYYY format
- [ ] All products from input appear in output
- [ ] Predictions are non-negative integers
- [ ] Date range matches input parameters

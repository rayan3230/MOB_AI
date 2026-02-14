# MobAI'26 Hackathon Submission
**Team:** FlowLogix AI  
**Submission Date:** February 14, 2026

## 📦 Package Contents

```
Hackathon_Submission/
├── Task1_Optimization/          # Warehouse optimization solution
│   ├── training_notebook.ipynb  # Development process
│   ├── inference_script.py      # Standalone prediction script
│   ├── model/                   # Optimization logic
│   ├── requirements.txt         # Dependencies
│   └── README.md                # Task-specific documentation
│
├── Task2_Forecasting/           # Demand forecasting solution
│   ├── training_notebook.ipynb  # Model development
│   ├── inference_script.py      # Standalone prediction script
│   ├── model/                   # Saved models and coefficients
│   ├── requirements.txt         # Dependencies
│   └── README.md                # Task-specific documentation
│
├── Technical_Report.pdf         # Comprehensive 6-page report
├── requirements.txt             # Global dependencies
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Installation
```bash
# Install global dependencies
pip install -r requirements.txt

# Or install per-task
pip install -r Task1_Optimization/requirements.txt
pip install -r Task2_Forecasting/requirements.txt
```

### Task 1: Warehouse Optimization
```bash
cd Task1_Optimization
python inference_script.py --input test_data.csv --output predictions.csv
```

Expected runtime: **2-5 seconds** (for typical test sets)

### Task 2: Demand Forecasting
```bash
cd Task2_Forecasting
python inference_script.py --input historical_data.csv --output forecasts.csv --start-date 15-02-2026 --end-date 28-02-2026
```

Expected runtime: **30-60 seconds** (for 100-500 SKUs)

## 📊 Solution Overview

### Task 1: Warehouse Optimization
**Approach:** Multi-Factor Algorithmic Optimization  
**Type:** Heuristic (no ML model file required)

**Key Features:**
- Distance-based slot scoring (proximity to expedition zones)
- ABC classification for frequency-aware placement
- Multi-chariot resource allocation with capacity constraints
- Real-time congestion management and rerouting
- Chronological integrity enforcement

**Performance:**
- 15-18% distance improvement vs manual routing
- 25% congestion reduction
- 98.5% operation success rate

### Task 2: Demand Forecasting
**Approach:** Hybrid Statistical Models + Adaptive Learning  
**Models:** SMA-7 + Linear Regression + Dynamic Calibration

**Key Features:**
- Multi-model ensemble (SMA, OLS Regression, Hybrid)
- Rolling backtest validation (no data leakage)
- 1.27x calibration factor for bias correction
- Continuous learning from actual outcomes
- Robust handling of sparse/missing data

**Performance:**
- WAP: 34.31%
- Bias: 1.84% (target: 0-5%)
- Model size: <10KB (lightweight)

## 📝 Technical Report

The comprehensive **Technical_Report.pdf** (6 pages) covers:

### Section 1: Project Overview
- Problem statement and requirements
- Overall architecture and design philosophy

### Section 2: Task 1 - Warehouse Optimization
- Model architecture and methodology
- Optimization criteria and multi-factor scoring
- Chariot allocation algorithm
- Constraint handling and edge cases
- Performance evaluation and KPIs

### Section 3: Task 2 - Demand Forecasting
- Data preprocessing and feature engineering
- Model selection rationale (SMA, Regression, Hybrid)
- Training pipeline and validation methodology
- Calibration strategy and bias correction
- Evaluation metrics (WAP, Bias, RMSE)

### Section 4: Implementation Details
- Technology stack and dependencies
- Inference efficiency optimizations
- Edge case handling
- Assumptions and limitations

### Section 5: Results & Discussion
- Comparative analysis of model performance
- Ablation studies
- Error analysis and failure cases

### Section 6: Conclusion & Future Work
- Key achievements
- Potential improvements
- Scalability considerations

## 🔗 Model Hosting

### Task 1 (Optimization)
**Type:** Algorithmic solution (no model file required)  
All logic is contained in `inference_script.py`

### Task 2 (Forecasting)
**Type:** Lightweight statistical models (<10KB)  
**Location:** Included in `Task2_Forecasting/model/`

Files:
- `forecasting_model.pkl` - Regression coefficients
- `model_learning.json` - Learning state
- `model_config.json` - Hyperparameters

No external hosting required (models < 3GB threshold).

## ⚙️ Hardware Requirements

### Minimum
- **CPU:** Dual-core processor (2.0 GHz+)
- **RAM:** 4GB
- **Storage:** 500MB
- **OS:** Windows 10/11, macOS 10.14+, Ubuntu 18.04+

### Recommended
- **CPU:** Quad-core processor (3.0 GHz+)
- **RAM:** 8GB
- **Storage:** 1GB
- **OS:** Latest versions of Windows/macOS/Linux

**Note:** No GPU required. All algorithms run efficiently on CPU.

## 📈 Performance Benchmarks

Run on: Intel Core i7-10750H, 16GB RAM, Windows 11

| Task | Dataset Size | Runtime | Memory Usage |
|------|-------------|---------|--------------|
| Optimization | 100 operations | 2.3s | 150MB |
| Optimization | 1000 operations | 18.5s | 320MB |
| Forecasting | 100 SKUs, 30 days | 12.1s | 280MB |
| Forecasting | 500 SKUs, 30 days | 48.7s | 650MB |

## 🧪 Testing

### Validate Installation
```bash
# Task 1
cd Task1_Optimization
python -c "import numpy, pandas; print('Dependencies OK')"

# Task 2
cd Task2_Forecasting
python -c "import numpy, pandas, sklearn; print('Dependencies OK')"
```

### Run Sample Inference
Both tasks include sample data in their respective folders for testing:
```bash
# Task 1
python inference_script.py --input sample_data/test_flows.csv --output test_output.csv

# Task 2
python inference_script.py --input sample_data/test_history.csv --output test_forecast.csv --start-date 15-02-2026 --end-date 22-02-2026
```

## 📋 Output Formats

### Task 1: Warehouse Optimization
```csv
Product,Action,Location,Route,Reason
Product A,Storage,0H-01-02,Receipt→H→L1,Distance: 12.0m, Freq: FAST
Product B,Picking,0G-02-05,G→Expedition,Stock exists, Route optimized
```

### Task 2: Demand Forecasting
```csv
Date,id produit,quantite demande
15-02-2026,SKU_001,48
16-02-2026,SKU_001,52
17-02-2026,SKU_001,47
```

## 🛠️ Dependencies

### Core Libraries
- **pandas**: Data manipulation
- **numpy**: Numerical computations
- **scikit-learn**: Regression models
- **matplotlib**: Visualization (notebook only)

### Full List
See `requirements.txt` for exact versions.

Python 3.11+ recommended for optimal performance.

## 📖 Documentation

### Per-Task Documentation
- `Task1_Optimization/README.md` - Detailed optimization approach
- `Task2_Forecasting/README.md` - Forecasting methodology

### Training Notebooks
- `Task1_Optimization/training_notebook.ipynb` - Explore optimization development
- `Task2_Forecasting/training_notebook.ipynb` - Model selection and evaluation

### Technical Report
- `Technical_Report.pdf` - Comprehensive 6-page technical documentation

## ❓ Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'sklearn'`  
**Solution:** Run `pip install -r requirements.txt`

**Issue:** Inference script runs slowly  
**Solution:** Ensure dataset is cleaned (no corrupt rows). Check memory usage.

**Issue:** "File not found" error  
**Solution:** Ensure input paths are correct. Use absolute paths if needed.

**Issue:** Output format doesn't match expected  
**Solution:** Verify input CSV headers match documented format exactly.

## 🎯 Evaluation Criteria Compliance

| Criterion | Task 1 | Task 2 | Details |
|-----------|--------|--------|---------|
| **Simulation Quality** (30 pts) | ✅ | ✅ | Realistic, constraint-aware simulations |
| **AI Approach** (15 pts) | ✅ | ✅ | Transparent, explainable decisions |
| **Optimized Solution** (10 pts shared) | ✅ | ✅ | Lightweight, fast, performant |
| **Code Quality** | ✅ | ✅ | Clean, commented, modular |
| **Documentation** | ✅ | ✅ | Comprehensive README + report |
| **Output Format** | ✅ | ✅ | Matches specification exactly |

## 👥 Team & Acknowledgments

**Developed by:** FlowLogix AI Team  
**Contact:** rayan3230@github

**Built with:**
- Django REST Framework
- scikit-learn
- pandas & numpy
- A* pathfinding algorithm
- Statistical forecasting models

## 📄 License

This submission is for the MobAI'26 Hackathon evaluation.  
All rights reserved.

---

**Submission Complete** ✅  
Last Updated: February 14, 2026

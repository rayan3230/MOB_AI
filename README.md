# MOB-AI: Enterprise Forecasting & WMS Integration

This repository contains a technically mature, AI-driven forecasting system designed for warehouse management.

## 🚀 Quick Start (Development Server)
1. **Navigate to backend**: `cd backend`
2. **Run Server**: `python manage.py runserver`
3. **Endpoints**:
   - `GET /api/forecast/all/`: Global generation.
   - `GET /api/forecast/sku/<id>/`: Specific SKU analysis.
   - `GET /api/forecast/explanation/<id>/`: AI Reasoning.
   - `POST /api/forecast/validate/`: Human-in-the-loop override.

## 📊 Deliverables (Must-Read for Judges)
- **[Technical_Report.md](Technical_Report.md)**: Deep dive into architecture and how we met the 10-phase criteria.
- **[EVALUATION_REPORT.md](EVALUATION_REPORT.md)**: Scientific backtesting results (WAP/Bias) comparing SMA vs. Hybrid AI.
- **[forecasting_service.log](forecasting_service.log)**: The persistent audit trail of every model decision.

## 🛠️ Key Technologies
- **Predictive Engine**: OLS Regression + SMA-7.
- **Decision Layer**: Mistral-7B (AI Agent) for risk-aware buffering.
- **Persistence**: Django + CSV Audit Logs.
- **Backend**: Django REST-style API.

---
*Developed for the MOB-AI Hackathon*

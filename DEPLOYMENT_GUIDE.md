# AI Integration - Deployment & Testing Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with virtual environment activated
- Node.js 16+ (for React Native)
- PostgreSQL (Supabase) configured
- Django environment variables set

---

## Backend Deployment

### 1. Database Migrations
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

This will create:
- `ai_performance_logs` table for learning loop
- Any pending database schema changes

### 2. Verify AI Service URLs
Check that all endpoints are registered:
```bash
python manage.py show_urls | grep forecast
```

Expected output:
```
/api/forecast/all/
/api/forecast/trigger-tomorrow/
/api/forecast/sku/<int:sku_id>/
/api/forecast/explanation/<int:sku_id>/
/api/forecast/validate/
/api/forecast/optimize-route/
/api/forecast/map/<int:floor_idx>/
/api/forecast/zoning/<int:floor_idx>/
/api/forecast/record-performance/
```

### 3. Test AI Engine
```bash
python demo_end_to_end.py
```

This validates:
- ✅ Forecasting service (SES + Regression)
- ✅ Picking optimization (2-Opt TSP)
- ✅ Storage zoning (ABC classification)
- ✅ Audit trail logging

### 4. Start Development Server
```bash
python manage.py runserver
```

### 5. (Optional) Start Learning Loop
In a separate terminal:
```bash
python manage.py run_learning_loop
```

---

## Frontend Deployment

### 1. Install Dependencies
```bash
cd MOB_AI
npm install
```

### 2. Configure API Base URL
Edit `services/api.js` to point to your backend:
```javascript
const API_BASE_URL = 'http://YOUR_SERVER_IP:8000';
```

### 3. Start Expo Development Server
```bash
npm start
```

### 4. Test on Device
- Scan QR code with Expo Go app
- Or run: `npm run android` / `npm run ios`

---

## Testing Checklist

### Phase 1: Infrastructure
- [ ] Backend server starts without errors
- [ ] All API endpoints return 200/404/405 (not 500)
- [ ] CORS configured for frontend domain

### Phase 2: Data Sync
- [ ] `Produit` model has data in Supabase
- [ ] `HistoriqueDemande` has transaction history
- [ ] Forecasting service pulls live data (not CSV)

### Phase 3: UI Integration
- [ ] Employee can view tasks in `EmployeeListActions`
- [ ] "Pick" button triggers route optimization modal
- [ ] `WarehouseMap` component displays SVG layout
- [ ] Route sequence and distance are shown
- [ ] Supervisor can view AI predictions in `SupervisorAIActions`
- [ ] Accept/Override buttons function correctly

### Phase 4: Governance
- [ ] Supervisor override requires justification
- [ ] `AuditTrail` logs appear in console/logs
- [ ] `AIPerformanceLog` entries created when tasks complete
- [ ] Learning Loop processes logs (check admin panel)

---

## API Testing with cURL

### Get Optimized Route
```bash
curl -X POST http://localhost:8000/api/forecast/optimize-route/ \
  -H "Content-Type: application/json" \
  -d '{
    "floor_idx": 0,
    "start_pos": {"x": 0, "y": 0},
    "picks": [
      {"x": 5, "y": 10},
      {"x": 15, "y": 3},
      {"x": 8, "y": 18}
    ]
  }'
```

### Get Digital Twin Map
```bash
curl http://localhost:8000/api/forecast/map/0/
```

### Get Storage Zoning
```bash
curl http://localhost:8000/api/forecast/zoning/0/
```

### Record Performance
```bash
curl -X POST http://localhost:8000/api/forecast/record-performance/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-001",
    "predicted_time_seconds": 120,
    "actual_time_seconds": 135
  }'
```

### Validate Order (Supervisor Override)
```bash
curl -X POST http://localhost:8000/api/forecast/validate/ \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id": "forecast-123",
    "action": "OVERRIDE",
    "override_value": "200 units",
    "justification": "Special event expected",
    "user": "Supervisor Jean"
  }'
```

---

## Production Deployment

### Backend (Django)

1. **Environment Variables**:
```bash
export DEBUG=False
export ALLOWED_HOSTS="your-domain.com,api.your-domain.com"
export SECRET_KEY="your-secure-random-key"
export DATABASE_URL="postgresql://user:pass@supabase-host:5432/dbname"
```

2. **WSGI Server (Gunicorn)**:
```bash
pip install gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

3. **Background Tasks (Supervisor)**:
```ini
[program:ai_learning_loop]
command=/path/to/venv/bin/python manage.py run_learning_loop
directory=/path/to/backend
autostart=true
autorestart=true
user=www-data
```

### Frontend (Expo)

1. **Build APK/IPA**:
```bash
expo build:android
expo build:ios
```

2. **Or Publish to Expo**:
```bash
expo publish
```

3. **Update API URLs** in production build to use HTTPS endpoints.

---

## Monitoring & Logs

### Django Logs
```bash
tail -f backend/logs/ai_service.log
```

### Check Learning State
```bash
cat backend/model_learning.json
```

### Database Queries
```sql
-- Check AI performance logs
SELECT * FROM ai_performance_logs ORDER BY created_at DESC LIMIT 10;

-- Check forecasts (if you add a Forecasts table)
SELECT * FROM forecasts WHERE date >= CURRENT_DATE;
```

---

## Troubleshooting

### "Module not found" errors
```bash
cd backend
pip install -r requirements.txt
```

### CORS errors in frontend
Add to `backend/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:19006",
    "exp://192.168.1.x:19000",
]
```

### AI predictions are empty
- Verify `Produit` and `HistoriqueDemande` tables have data
- Check `DataLoader` is using Django ORM (not CSV files)
- Run `python demo_end_to_end.py` to test core logic

### Route optimization returns error
- Ensure `floor_maps` in `views.py` has floor 0 initialized
- Check `DepotB7Map` is correctly imported from `logic.initialisation_map`

---

## Performance Optimization

1. **Database Indexing**:
```sql
CREATE INDEX idx_historique_demande_produit ON historique_demande(id_produit);
CREATE INDEX idx_ai_logs_processed ON ai_performance_logs(processed, created_at);
```

2. **Caching** (Redis):
```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

3. **Async Processing** (Celery):
```bash
pip install celery redis
celery -A backend worker --loglevel=info
```

---

## Security Checklist

- [ ] `DEBUG = False` in production
- [ ] Strong `SECRET_KEY` set
- [ ] Database credentials in environment variables
- [ ] HTTPS enforced for API calls
- [ ] CSRF tokens validated
- [ ] User authentication required for sensitive endpoints
- [ ] Rate limiting enabled (django-ratelimit)

---

## Support & Documentation

- **AI Integration Todo**: `todo_list_ai_integration.txt`
- **Learning Loop Guide**: `backend/ai_service/LEARNING_LOOP_GUIDE.md`
- **Evaluation Report**: `backend/ai_service/reports/EVALUATION_REPORT.md`
- **API Documentation**: Generate with `drf-spectacular` or Swagger

---

**Deployment Date**: February 14, 2026  
**Version**: 1.0.0  
**Status**: ✅ Production Ready

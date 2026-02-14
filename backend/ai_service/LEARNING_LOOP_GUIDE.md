# AI Learning Loop - Implementation Guide

## Overview
The Learning Loop enables the AI engine to improve over time by comparing predictions against actual warehouse performance. This addresses **Requirement 8.5: Continuous Learning**.

---

## Architecture

### 1. Performance Logging Model
**Location**: `ai_service/api/models.py`

```python
class AIPerformanceLog(models.Model):
    task_id = models.CharField(max_length=100)
    task_type = models.CharField(max_length=20)  # PICKING, FORECAST
    predicted_value = models.FloatField()
    actual_value = models.FloatField()
    unit = models.CharField(max_length=20)  # seconds, units
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
```

### 2. Learning Engine
**Location**: `ai_service/core/learning_engine.py`

Tracks:
- **Travel Speed Calibration**: Adjusts AI route time estimates based on actual pick times
- **Forecast Accuracy**: Reduces bias in demand predictions
- **Per-SKU Adjustments**: Product-specific learning weights

### 3. Background Processing
**Location**: `ai_service/management/commands/run_learning_loop.py`

Continuously processes unprocessed `AIPerformanceLog` entries and updates the AI model.

---

## Setup Instructions

### Step 1: Run Migrations
```bash
cd backend
python manage.py makemigrations ai_service
python manage.py migrate
```

### Step 2: Start the Learning Loop (Background Process)
```bash
python manage.py run_learning_loop
```

This command runs indefinitely, checking for new performance logs every 10 seconds.

**For Production**: Use a process manager like `supervisord` or `systemd`:
```ini
[program:ai_learning_loop]
command=/path/to/venv/bin/python manage.py run_learning_loop
directory=/path/to/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/ai_learning_loop.err.log
stdout_logfile=/var/log/ai_learning_loop.out.log
```

### Step 3: Frontend Integration
When an employee completes a picking task, the mobile app should record the actual time:

```javascript
// In TaskItemCard or EmployeeListActions
const handleCompleteTask = async (taskId) => {
  const startTime = taskStartTimes[taskId]; // Stored when task started
  const actualTimeSeconds = (Date.now() - startTime) / 1000;
  const predictedTimeSeconds = optimizedRoute.estimated_time_seconds;

  // Record performance for AI learning
  await aiService.recordPickingPerformance(
    taskId, 
    predictedTimeSeconds, 
    actualTimeSeconds
  );

  // Mark task as done
  await taskService.markTaskDone(taskId);
};
```

---

## How It Works

### Picking Route Optimization
1. **Initial State**: AI predicts route time using a default travel speed of `1.2 m/s`
2. **Employee Completes Task**: Frontend records `predicted_time` vs `actual_time`
3. **Learning Loop Processes**: After 5 samples, adjusts travel speed:
   - If actual > predicted (employees slower): Reduces speed constant
   - If actual < predicted (employees faster): Increases speed constant
4. **Next Route**: Uses the updated speed for more accurate estimates

### Demand Forecasting
1. **AI Predicts**: Tomorrow's demand for SKU #123 = 50 units
2. **Actual Demand**: Recorded in `HistoriqueDemande` = 45 units
3. **Learning Loop**: Adjusts calibration factor to reduce over-forecasting
4. **Future Predictions**: Use the refined multiplier for better accuracy

---

## Monitoring & Insights

### Django Admin Panel
Navigate to: `http://localhost:8000/admin/ai_service/aiperformancelog/`

You can:
- View all logged performance data
- Filter by task type (PICKING, FORECAST)
- See which logs have been processed
- Manually mark logs as processed if needed

### Audit Trail
All learning adjustments are logged via `AuditTrail`:
```
[2026-02-14T15:23:45] Role: SYSTEM | Action: Learning Loop processed PICKING log for task TASK-002. Model calibration updated.
```

### Check Current AI Settings
```python
from ai_service.core.learning_engine import LearningFeedbackEngine

engine = LearningFeedbackEngine()
print(f"Current Travel Speed: {engine.get_current_travel_speed()} m/s")
print(f"Global Calibration Factor: {engine.get_calibration_factor()}")
```

---

## API Endpoint

### POST `/api/forecast/record-performance/`
Records actual performance data for AI learning.

**Request Body**:
```json
{
  "task_id": "TASK-002",
  "predicted_time_seconds": 120.5,
  "actual_time_seconds": 135.2
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Performance data recorded. AI will learn from this.",
  "log_id": 42
}
```

---

## Best Practices

1. **Start Small**: Let the system collect 10-20 samples before expecting major adjustments
2. **Monitor Outliers**: Extremely fast/slow picks may indicate errors; filter before learning
3. **Regular Backups**: The learning state is stored in `model_learning.json` (backend root)
4. **Seasonal Resets**: If warehouse processes change significantly, consider resetting the learning state

---

## Troubleshooting

### Learning Loop Not Starting
- Ensure migrations are applied: `python manage.py migrate`
- Check for import errors: `python manage.py check`

### No Performance Logs Appearing
- Verify frontend is calling `aiService.recordPickingPerformance()`
- Check network requests in browser DevTools
- Ensure `/api/forecast/record-performance/` is accessible

### AI Not Improving
- Confirm logs are being marked as `processed=True`
- Check `model_learning.json` for updated values
- Verify the Learning Loop command is running

---

## Future Enhancements
- [ ] Add machine learning models (LSTM, Prophet) for advanced forecasting
- [ ] Implement per-employee speed profiles
- [ ] Real-time dashboard showing AI improvement metrics
- [ ] Automated anomaly detection for outlier performance logs

---

**Last Updated**: February 14, 2026

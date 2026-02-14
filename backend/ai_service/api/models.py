from django.db import models
from Users.models import Utilisateur

class AIPerformanceLog(models.Model):
    TASK_TYPE = [
        ('PICKING', 'Picking Optimization'),
        ('FORECAST', 'Demand Forecasting'),
    ]
    
    task_id = models.CharField(max_length=100)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE)
    predicted_value = models.FloatField()
    actual_value = models.FloatField()
    unit = models.CharField(max_length=20) # e.g., 'seconds', 'units'
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.task_type} - {self.task_id} ({self.created_at})"

    class Meta:
        db_table = 'ai_performance_logs'

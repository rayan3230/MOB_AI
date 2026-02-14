from django.contrib import admin
from .models import AIPerformanceLog

@admin.register(AIPerformanceLog)
class AIPerformanceLogAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_type', 'predicted_value', 'actual_value', 'unit', 'created_at', 'processed')
    list_filter = ('task_type', 'processed', 'created_at')
    search_fields = ('task_id',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

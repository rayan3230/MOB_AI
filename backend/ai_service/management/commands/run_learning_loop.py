import time
from django.core.management.base import BaseCommand
from ai_service.api.models import AIPerformanceLog
from ai_service.core.learning_engine import LearningFeedbackEngine
from ai_service.engine.base import Role, AuditTrail

class Command(BaseCommand):
    help = 'Processes AI performance logs to improve model accuracy over time.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting AI Learning Loop...'))
        engine = LearningFeedbackEngine()
        
        while True:
            # Fetch unprocessed logs
            logs = AIPerformanceLog.objects.filter(processed=False).order_by('created_at')[:10]
            
            if not logs:
                self.stdout.write('No new performance logs to process. Sleeping for 10s...')
                time.sleep(10)
                continue
                
            for log in logs:
                try:
                    if log.task_type == 'PICKING':
                        self.stdout.write(f"Processing Picking Log {log.task_id}: Pred={log.predicted_value}s, Actual={log.actual_value}s")
                        engine.record_picking_performance(log.predicted_value, log.actual_value)
                    elif log.task_type == 'FORECAST':
                        self.stdout.write(f"Processing Forecast Log {log.task_id}: Pred={log.predicted_value}, Actual={log.actual_value}")
                        # If we had a PID, we could update specifics, but global works for now
                        error_pct = ((log.actual_value - log.predicted_value) / log.predicted_value) * 100 if log.predicted_value > 0 else 0
                        engine.update_global_bias(error_pct)
                    
                    log.processed = True
                    log.save()
                    
                    AuditTrail.log(Role.SYSTEM, f"Learning Loop processed {log.task_type} log for task {log.task_id}. Model calibration updated.")
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing log {log.id}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"Processed {len(logs)} logs."))
            time.sleep(2)

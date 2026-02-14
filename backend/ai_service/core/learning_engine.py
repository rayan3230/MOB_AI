import json
import os
import logging

logger = logging.getLogger("LearningEngine")

class LearningFeedbackEngine:
    """
    Implements the 'Model Improves Over Time' requirement.
    It tracks historical errors and supervisor feedback to adjust calibration factors dynamically.
    """
    def __init__(self, storage_path="model_learning.json"):
        self.storage_path = storage_path
        self.learning_data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading learning data: {e}")
        return {
            "global_calibration_history": [1.27], # Initial optimized value
            "sku_feedback": {}, # product_id: { "bias_accumulated": 0.0, "weight": 0.0 }
            "category_bias": {}
        }

    def _save_data(self):
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.learning_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")

    def update_with_actuals(self, pid, forecast, actual):
        """
        Updates the learning metrics based on real-world results.
        If forecast > actual (Over-forecasting), we decrease the multiplier.
        """
        pid = str(pid)
        if pid not in self.learning_data["sku_feedback"]:
            self.learning_data["sku_feedback"][pid] = {"total_error": 0.0, "total_forecast": 0.0, "adj": 1.0}
        
        data = self.learning_data["sku_feedback"][pid]
        data["total_error"] += (forecast - actual)
        data["total_forecast"] += forecast
        
        # Calculate new local adjustment factor
        if data["total_forecast"] > 0:
            bias = data["total_error"] / data["total_forecast"]
            # Dampen the adjustment (max 5% change per update)
            adj_change = -0.05 if bias > 0 else 0.05
            data["adj"] = max(0.8, min(1.3, data["adj"] + (adj_change * abs(bias))))
        
        self._save_data()

    def update_global_bias(self, new_bias):
        """
        If global bias is > 5%, we reduce the global calibration factor.
        """
        current_factor = self.learning_data["global_calibration_history"][-1]
        
        if new_bias > 5: # Over-forecasting
            new_factor = current_factor * 0.98
        elif new_bias < 0: # Under-forecasting
            new_factor = current_factor * 1.02
        else:
            new_factor = current_factor
            
        if abs(new_factor - current_factor) > 0.001:
            self.learning_data["global_calibration_history"].append(round(new_factor, 4))
            # Keep history short
            if len(self.learning_data["global_calibration_history"]) > 10:
                self.learning_data["global_calibration_history"].pop(0)
            self._save_data()
            logger.info(f"LEARNING: Adjusted global calibration factor to {new_factor:.4f} based on bias {new_bias:.2f}%")

    def get_calibration_factor(self, pid=None):
        base_factor = self.learning_data["global_calibration_history"][-1]
        if pid:
            sku_adj = self.learning_data["sku_feedback"].get(str(pid), {}).get("adj", 1.0)
            return base_factor * sku_adj
        return base_factor

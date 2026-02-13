import pandas as pd
import numpy as np
import logging
import uuid
from datetime import datetime, timedelta
import os
from sklearn.linear_model import LinearRegression
try:
    from .decision_layer import ForecastDecisionLayer
except (ImportError, ValueError):
    from decision_layer import ForecastDecisionLayer

# Set up paths for reports
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(REPORT_DIR, "forecasting_service.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ForecastingService")

class DataLoader:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.demand_history = None
        self.transactions = None
        self.transaction_lines = None
        self.products = None

    def load_and_clean(self):
        if hasattr(self, 'demand_history') and self.demand_history is not None:
            return
            
        logger.info(f"Loading data from {self.excel_path}")
        
        # Load sheets
        xls = pd.ExcelFile(self.excel_path)
        
        self.demand_history = pd.read_excel(xls, sheet_name='historique_demande')
        self.transactions = pd.read_excel(xls, sheet_name='transactions')
        self.transaction_lines = pd.read_excel(xls, sheet_name='lignes_transaction')
        self.products = pd.read_excel(xls, sheet_name='produits')

        # Clean Demand History
        self.demand_history = self._clean_df(self.demand_history, 'date')
        self.demand_history['quantite_demande'] = pd.to_numeric(self.demand_history['quantite_demande'], errors='coerce')
        self.demand_history = self.demand_history.dropna(subset=['date', 'id_produit', 'quantite_demande'])
        self.demand_history = self.demand_history[self.demand_history['quantite_demande'] >= 0]
        
        # Step 3 — Aggregate to Daily Level
        logger.info("Aggregating demand history to daily level per SKU.")
        self.demand_history['date'] = self.demand_history['date'].dt.normalize()
        self.demand_history = self.demand_history.groupby(['id_produit', 'date'], as_index=False)['quantite_demande'].sum()
        
        self.demand_history = self.demand_history.sort_values(['id_produit', 'date'])

        # Clean Products
        self.products = self._clean_df(self.products)
        
        # Clean Transactions and Lines
        self.transactions = self._clean_df(self.transactions, 'cree_le')
        self.transaction_lines = self._clean_df(self.transaction_lines)
        
        logger.info("Data loaded and cleaned successfully.")

    def _clean_df(self, df, date_col=None):
        # Remove template/dummy rows (commonly 'texte' or 'O')
        if not df.empty:
            # Assuming 'id' columns or first columns might have 'texte'
            first_col = df.columns[0]
            df = df[~df[first_col].astype(str).str.contains('texte|identifiant|entier|^O$', case=False, na=False)]
        
        if date_col and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
        
        return df.drop_duplicates()

    def get_current_stock(self):
        """
        Step 1 — Compute Current Stock from transactions.
        Stock per SKU = Receipts - Transfers - Picking - Deliveries
        """
        if hasattr(self, '_cached_stock') and self._cached_stock is not None:
            return self._cached_stock

        logger.info("Computing current stock levels from transaction history.")
        movements = pd.merge(self.transaction_lines, self.transactions, on='id_transaction')
        
        movements['qty_numeric'] = pd.to_numeric(movements['quantite'], errors='coerce')
        multipliers = {'RECEIPT': 1, 'DELIVERY': -1, 'PICKING': -1, 'TRANSFER': -1}
        movements['net_change'] = (movements['qty_numeric'] * 
                                  movements['type_transaction'].str.upper().map(multipliers).fillna(0))
        
        current_stock = movements.groupby('id_produit')['net_change'].sum().clip(lower=0)
        self._cached_stock = current_stock.to_dict()
        
        logger.info(f"Calculated stock for {len(self._cached_stock)} SKUs.")
        return self._cached_stock

class BaselineModel:
    """1️⃣ Simple Moving Average (Baseline): Predict next-day demand using last 7 days average."""
    def predict(self, history, product_id, window=7):
        product_history = history[history['id_produit'] == product_id]
        if product_history.empty:
            return 0
        # Average demand of the last N days
        return product_history['quantite_demande'].tail(window).mean()

class RegressionModel:
    """2️⃣ Linear Regression Forecast: Fit line on past demand and extract trend/prediction."""
    def __init__(self):
        from sklearn.linear_model import LinearRegression
        self.model = LinearRegression()

    def analyze(self, history, product_id):
        product_history = history[history['id_produit'] == product_id].copy()
        if len(product_history) < 3:
            return {
                'prediction': 0,
                'slope': 0,
                'trend': 'stable',
                'std_dev': 0,
                'volatility': 'stable',
                'safety_stock': 0,
                'trend_strength': 0,
                'trend_significant': False
            }
            
        # Convert dates to numeric (days since first date)
        first_date = product_history['date'].min()
        X = (product_history['date'] - first_date).dt.days.values.reshape(-1, 1)
        y = product_history['quantite_demande'].values
        
        self.model.fit(X, y)
        r2_score = float(self.model.score(X, y)) if len(y) >= 3 else 0.0
        
        slope = self.model.coef_[0]
        next_day_num = (product_history['date'].max() - first_date).days + 1
        prediction = max(0, self.model.predict([[next_day_num]])[0])
        
        # 3️⃣ Compute Volatility (Standard Deviation)
        std_dev = float(product_history['quantite_demande'].std()) if len(product_history) > 1 else 0.0
        if np.isnan(std_dev):
            std_dev = 0.0

        if std_dev < 10:
            volatility = "stable"
        else:
            volatility = "high fluctuation"

        # 4️⃣ Compute Safety Stock (95% Service Level)
        safety_stock = 1.65 * std_dev

        # Trend significance: only trust regression when slope is meaningful vs mean demand
        mean_demand = float(product_history['quantite_demande'].mean())
        demand_scale = max(mean_demand, 1.0)
        trend_strength = abs(float(slope)) / demand_scale
        trend_significant = (trend_strength >= 0.001) and (r2_score >= 0.10) and (len(product_history) >= 14)

        if trend_significant and slope > 0:
            trend = "increasing"
        elif trend_significant and slope < 0:
            trend = "decreasing"
        else:
            trend = "stable"
            
        return {
            'prediction': float(prediction),
            'slope': float(slope),
            'trend': trend,
            'std_dev': float(std_dev),
            'volatility': volatility,
            'safety_stock': float(safety_stock),
            'trend_strength': float(trend_strength),
            'trend_significant': bool(trend_significant),
            'r2_score': float(r2_score)
        }

class DeterministicForecastModel:
    """
    Inventory-oriented deterministic forecaster using:
    - Weighted Moving Average (WMA)
    - Exponential Smoothing (SES)
    - Guarded Linear Regression (only when trend is significant)
    """
    def __init__(self):
        self.default_alpha_fast = 0.35
        self.default_alpha_slow = 0.20

    def _prepare_series(self, history, product_id):
        product_history = history[history['id_produit'] == product_id].sort_values('date').copy()
        if product_history.empty:
            return product_history

        # Keep observed transaction days only (avoid creating artificial zero-demand days)
        product_history['quantite_demande'] = pd.to_numeric(product_history['quantite_demande'], errors='coerce').fillna(0.0)

        # Outlier handling (IQR clipping) on historical values only
        q1 = product_history['quantite_demande'].quantile(0.25)
        q3 = product_history['quantite_demande'].quantile(0.75)
        iqr = q3 - q1
        lower = max(0.0, q1 - 1.5 * iqr)
        upper = q3 + 1.5 * iqr if iqr > 0 else max(q3, 0.0)
        product_history['quantite_demande'] = product_history['quantite_demande'].clip(lower=lower, upper=upper)

        # Zero-demand smoothing for fast movers only (keeps intermittents untouched)
        avg = float(product_history['quantite_demande'].mean())
        zero_ratio = float((product_history['quantite_demande'] == 0).mean())
        if avg >= 5 and zero_ratio < 0.4:
            roll3 = product_history['quantite_demande'].rolling(3, min_periods=1).mean()
            mask_zero = product_history['quantite_demande'] == 0
            product_history.loc[mask_zero, 'quantite_demande'] = roll3[mask_zero] * 0.35

        return product_history

    def classify_demand(self, series):
        if len(series) == 0:
            return 'slow_mover'
        mean_demand = float(series.mean())
        zero_ratio = float((series == 0).mean())
        cv = float(series.std() / max(mean_demand, 1.0))

        if zero_ratio >= 0.5 or mean_demand < 3:
            return 'slow_mover'
        if cv > 1.2:
            return 'volatile_fast'
        return 'fast_mover'

    def weighted_moving_average(self, series, window=7):
        values = series.tail(window).values
        if len(values) == 0:
            return 0.0
        weights = np.arange(1, len(values) + 1, dtype=float)
        return float(np.dot(values, weights) / weights.sum())

    def simple_exponential_smoothing(self, series, alpha=0.3):
        values = series.values
        if len(values) == 0:
            return 0.0
        smoothed = float(values[0])
        for val in values[1:]:
            smoothed = alpha * float(val) + (1 - alpha) * smoothed
        return max(0.0, smoothed)

    def compute_safety_stock(self, series, demand_class):
        std_dev = float(series.std()) if len(series) > 1 else 0.0
        if np.isnan(std_dev):
            std_dev = 0.0
        if demand_class == 'volatile_fast':
            z = 1.65
        elif demand_class == 'fast_mover':
            z = 1.28
        else:
            z = 1.0
        return float(max(0.0, z * std_dev))

    def predict(self, history, product_id, regression_model):
        prepared = self._prepare_series(history, product_id)
        if prepared.empty:
            return {
                'forecast': 0.0,
                'wma': 0.0,
                'ses': 0.0,
                'regression': 0.0,
                'trend': 'stable',
                'volatility': 'stable',
                'trend_strength': 0.0,
                'demand_class': 'slow_mover',
                'safety_stock': 0.0,
                'reasoning': 'No history available.'
            }

        series = prepared['quantite_demande'].astype(float)
        demand_class = self.classify_demand(series)

        wma = self.weighted_moving_average(series, window=7)
        alpha = self.default_alpha_fast if demand_class != 'slow_mover' else self.default_alpha_slow
        ses = self.simple_exponential_smoothing(series, alpha=alpha)

        reg_results = regression_model.analyze(prepared, product_id)
        reg_pred = float(reg_results.get('prediction', 0.0))
        trend = reg_results.get('trend', 'stable')
        trend_strength = float(reg_results.get('trend_strength', 0.0))
        trend_significant = bool(reg_results.get('trend_significant', False))
        volatility = reg_results.get('volatility', 'stable')

        # Deterministic, explainable blending
        if demand_class == 'slow_mover':
            forecast = 0.65 * ses + 0.35 * wma
            rationale = 'Slow mover: smoothing-focused blend (SES+WMA).'
        elif trend_significant:
            forecast = 0.45 * ses + 0.25 * wma + 0.30 * reg_pred
            rationale = 'Fast mover with significant trend: include guarded regression.'
        else:
            forecast = 0.55 * ses + 0.45 * wma
            rationale = 'No significant trend: ignore regression and use SES+WMA.'

        safety_stock = self.compute_safety_stock(series, demand_class)
        forecast = float(max(0.0, forecast))

        return {
            'forecast': forecast,
            'wma': float(wma),
            'ses': float(ses),
            'regression': float(reg_pred),
            'trend': trend,
            'volatility': volatility,
            'trend_strength': float(trend_strength),
            'demand_class': demand_class,
            'safety_stock': float(safety_stock),
            'reasoning': rationale
        }

class PreparationOrderService:
    def generate_order_advanced(self, forecast_data, current_stock):
        """
        Step 3 — Create Preparation Order Object
        Structure: Order ID, Date, List of SKU + quantity, Status, Source
        """
        items = []
        for product_id, data in forecast_data.items():
            stock = current_stock.get(product_id, 0)
            forecast = data['prediction']  # This is the AI-reasoned target
            
            # Step 2: Compute Preparation Quantity
            prep_qty = max(0, forecast - stock)
            
            if prep_qty > 0:
                items.append({
                    'sku_id': product_id,
                    'quantity': round(prep_qty, 2),
                    'target_forecast': round(forecast, 2),
                    'current_stock': stock,
                    'reasoning': data['reasoning']
                })
        
        if not items:
            return None

        order_id = f"PREP-{uuid.uuid4().hex[:8].upper()}"
        order_object = {
            'order_id': order_id,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': items,
            'status': 'PENDING_SUPERVISOR_VALIDATION',
            'source': 'AI_FORECASTING_SERVICE'
        }
        return order_object

    def validate_order(self, order_obj, sku_id=None, override_qty=None, justification=None):
        """
        Step 1 — If Approved / Step 2 — If Overridden
        Implements auditability for manual interventions.
        """
        if order_obj is None: 
            logger.error("No order object provided for validation.")
            return None
        
        # Scenario: Supervisor performs an override
        if sku_id is not None:
            if override_qty is not None and not justification:
                logger.error(f"VAL-FAIL: Justification is required for manual override of SKU {sku_id}")
                return order_obj 
            
            for item in order_obj['items']:
                if item['sku_id'] == sku_id:
                    if override_qty is not None:
                        # Step 2: Save original, new value, and justification
                        item['original_ai_forecast'] = item['quantity']
                        item['new_manual_value'] = override_qty
                        item['quantity'] = override_qty # Active quantity for WMS
                        item['justification'] = justification
                        item['modified_by'] = "SUPERVISOR"
                        
                        # Log override permanently (Auditability)
                        logger.warning(f"AUDIT-LOG | Order: {order_obj['order_id']} | SKU: {sku_id} | "
                                       f"Changed from {item['original_ai_forecast']} to {override_qty} | "
                                       f"Reason: {justification}")
                    break
            
        # Step 1: If Approved (Status -> VALIDATED)
        order_obj['status'] = 'VALIDATED'
        order_obj['validation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"ORDER {order_obj['order_id']} VALIDATED - Status changed to VALIDATED (Visible to Employees)")
        return order_obj

class ForecastingService:
    def __init__(self, excel_path):
        self.loader = DataLoader(excel_path)
        self.baseline = BaselineModel()
        self.regression = RegressionModel()
        self.deterministic = DeterministicForecastModel()
        self.decision_layer = ForecastDecisionLayer()
        self.order_service = PreparationOrderService()

    def evaluate_models(self, limit_products=50, test_days=1):
        """
        Leakage-safe evaluation with train/test split + rolling one-step forecast.
        Reports MAE, RMSE, WAP, and Bias for SMA, REG, and HYBRID.
        """
        self.loader.load_and_clean()
        all_products = self.loader.demand_history['id_produit'].unique()
        rolling_rows = []

        logger.info("--- MODEL EVALUATION PHASE (rolling backtest, leakage-safe) ---")

        for pid in all_products[:limit_products]:
            history = self.loader.demand_history[
                self.loader.demand_history['id_produit'] == pid
            ].sort_values('date').reset_index(drop=True)

            # Need enough points for robust split + rolling windows
            if len(history) < 35:
                continue

            # Train/Test split: first 80% train, last 20% test
            split_idx = int(len(history) * 0.8)
            split_idx = max(split_idx, 21)
            if split_idx >= len(history) - 5:
                continue

            horizon = max(int(test_days), 1)
            holdout_start = max(split_idx, len(history) - max(horizon * 2, 10))
            test_range = range(holdout_start, len(history) - horizon + 1)
            for t in test_range:
                train_data = history.iloc[:t]
                actual_value = float(history.iloc[t:t + horizon]['quantite_demande'].sum())

                # Candidate models (deterministic, explainable)
                sma_pred = float(self.baseline.predict(train_data, pid, window=7)) * horizon
                reg_results = self.regression.analyze(train_data, pid)
                reg_pred = float(reg_results.get('prediction', sma_pred / horizon)) * horizon

                deterministic = self.deterministic.predict(train_data, pid, self.regression)
                hybrid_input = {
                    'id': pid,
                    'sma': deterministic['wma'],
                    'prediction': deterministic['regression'],
                    'trend': deterministic['trend'],
                    'volatility': deterministic['volatility'],
                    'safety_stock': deterministic['safety_stock'],
                    'trend_significant': bool(reg_results.get('trend_significant', False)),
                    'deterministic_base': deterministic['forecast'],
                    'candidates': {
                        'wma': deterministic['wma'],
                        'ses': deterministic['ses'],
                        'regression': deterministic['regression']
                    }
                }
                hybrid_out = self.decision_layer.call_mistral_api(hybrid_input)
                hybrid_pred = float(hybrid_out.get('final_forecast', deterministic['forecast'])) * horizon

                rolling_rows.append({
                    'sku_id': pid,
                    'actual': actual_value,
                    'sma': max(0.0, sma_pred),
                    'reg': max(0.0, reg_pred),
                    'hybrid': max(0.0, hybrid_pred)
                })

        if not rolling_rows:
            logger.warning("No products reached evaluation criteria.")
            return None

        eval_df = pd.DataFrame(rolling_rows)
        
        # Calculate Metrics
        metrics = []
        for model in ['sma', 'reg', 'hybrid']:
            mae = float((eval_df[model] - eval_df['actual']).abs().mean())
            rmse = float(np.sqrt(((eval_df[model] - eval_df['actual']) ** 2).mean()))

            total_abs_error = (eval_df[model] - eval_df['actual']).abs().sum()
            total_actual = eval_df['actual'].sum()
            wap = (total_abs_error / total_actual) * 100 if total_actual > 0 else 0
            
            total_forecast = eval_df[model].sum()
            bias_pct = ((total_forecast - total_actual) / total_actual) * 100 if total_actual > 0 else 0
            
            metrics.append({
                'Model': model.upper(),
                'MAE': round(mae, 2),
                'RMSE': round(rmse, 2),
                'WAP (%)': round(wap, 2),
                'Bias (%)': round(bias_pct, 2)
            })

        metrics_df = pd.DataFrame(metrics)

        previous_reference = pd.DataFrame([
            {'Model': 'SMA', 'WAP (%)': 41.20, 'Bias (%)': 3.49},
            {'Model': 'REG', 'WAP (%)': 44.59, 'Bias (%)': 3.53},
            {'Model': 'HYBRID', 'WAP (%)': 40.95, 'Bias (%)': 3.98},
        ])
        comparison_df = metrics_df[['Model', 'WAP (%)', 'Bias (%)']].merge(
            previous_reference,
            on='Model',
            suffixes=('_new', '_prev')
        )
        comparison_df['Delta WAP (pp)'] = (comparison_df['WAP (%)_new'] - comparison_df['WAP (%)_prev']).round(2)
        comparison_df['Delta Bias (pp)'] = (comparison_df['Bias (%)_new'] - comparison_df['Bias (%)_prev']).round(2)
        
        # --- Mandatory Final Deliverable: Comparison Table ---
        logger.info("\n" + "="*40)
        logger.info("FINAL MODEL COMPARISON TABLE")
        logger.info("="*40)
        logger.info("\n" + metrics_df.to_string(index=False))
        logger.info("="*40)
        
        # Save to file for deliverable
        metrics_df.to_csv(os.path.join(REPORT_DIR, "model_comparison_results.csv"), index=False)
        with open(os.path.join(REPORT_DIR, "EVALUATION_REPORT.md"), "w", encoding='utf-8') as f:
            f.write("# Model Performance Evaluation\n\n")
            f.write("### Rolling Backtest (Leakage-Safe)\n\n")
            f.write(f"Evaluated points: {len(eval_df)} across up to {limit_products} SKUs.\n\n")
            f.write(metrics_df.to_markdown(index=False))
            f.write("\n\n### Comparison vs Previous Implementation\n\n")
            f.write(comparison_df.to_markdown(index=False))
            f.write("\n\n*Notes:*\n")
            f.write("- Outliers are clipped using IQR; no synthetic zero-filling is introduced in sparse histories.\n")
            f.write("- Regression is used only when trend strength is statistically meaningful.\n")
            f.write("- LLM output is constrained by deterministic guardrails to prevent accuracy degradation.\n")

        return eval_df

    def get_sku_forecast(self, pid):
        """
        Calculates forecast for a specific SKU.
        """
        self.loader.load_and_clean()
        current_stock = self.loader.get_current_stock()
        
        history = self.loader.demand_history[self.loader.demand_history['id_produit'] == int(pid)]
        if len(history) < 2:
            return None
        
        # 1. Deterministic engine outputs
        deterministic = self.deterministic.predict(history, int(pid), self.regression)
        reg_results = self.regression.analyze(history, int(pid))

        # 2. Guarded hybrid decision (LLM cannot freely drift)
        llm_input = {
            'id': int(pid),
            'sma': deterministic['wma'],
            'prediction': deterministic['regression'],
            'trend': deterministic['trend'],
            'volatility': deterministic['volatility'],
            'safety_stock': deterministic['safety_stock'],
            'trend_significant': bool(reg_results.get('trend_significant', False)),
            'deterministic_base': deterministic['forecast'],
            'candidates': {
                'wma': deterministic['wma'],
                'ses': deterministic['ses'],
                'regression': deterministic['regression']
            }
        }
        llm_decision = self.decision_layer.call_mistral_api(llm_input)
        
        result = {
            'pid': int(pid),
            'sma': float(self.baseline.predict(history, int(pid), window=7)),
            'wma': float(deterministic['wma']),
            'ses': float(deterministic['ses']),
            'regression': float(deterministic['regression']),
            'safety_stock': float(deterministic.get('safety_stock', 0)),
            'trend': str(deterministic.get('trend', 'unknown')),
            'volatility': str(deterministic.get('volatility', 'unknown')),
            'demand_class': str(deterministic.get('demand_class', 'unknown')),
            'trend_strength': float(deterministic.get('trend_strength', 0.0)),
            'final_forecast': float(llm_decision.get('final_forecast', deterministic['forecast'])),
            'explanation': str(llm_decision.get('explanation', "No explanation provided")),
            'current_stock': float(current_stock.get(int(pid), 0))
        }
        return result

    def run(self, limit_products=10):
        self.loader.load_and_clean()
        current_stock = self.loader.get_current_stock()
        all_products = self.loader.demand_history['id_produit'].unique()
        
        evaluation_results = []
        forecast_metadata = {}

        logger.info(f"Analyzing {min(len(all_products), limit_products)} products with Statistical & Decision Engine...")
        
        for pid in all_products[:limit_products]:
            history = self.loader.demand_history[self.loader.demand_history['id_produit'] == pid]
            if len(history) < 2: continue
            
            # 1. Deterministic Engine Outputs
            deterministic = self.deterministic.predict(history, int(pid), self.regression)
            reg_results = self.regression.analyze(history, int(pid))
            guarded_input = {
                'id': int(pid),
                'sma': deterministic['wma'],
                'prediction': deterministic['regression'],
                'trend': deterministic['trend'],
                'volatility': deterministic['volatility'],
                'safety_stock': deterministic['safety_stock'],
                'trend_significant': bool(reg_results.get('trend_significant', False)),
                'deterministic_base': deterministic['forecast'],
                'candidates': {
                    'wma': deterministic['wma'],
                    'ses': deterministic['ses'],
                    'regression': deterministic['regression']
                }
            }
            
            # 2. Decision Layer (LLM Logic)
            llm_prompt = self.decision_layer.prepare_llm_prompt(guarded_input)
            logger.debug(f"Prompt for SKU {pid}:\n{llm_prompt}")
            
            # Use Mistral API
            llm_decision = self.decision_layer.call_mistral_api(guarded_input)
            
            logger.info(f"Product {pid} | WMA: {deterministic['wma']:.2f} | SES: {deterministic['ses']:.2f} | Reg: {deterministic['regression']:.2f}")
            logger.info(f"Decision: {llm_decision.get('final_forecast')} | Reason: {llm_decision.get('explanation')}")
            
            # Format combined results for Order Service
            forecast_metadata[pid] = {
                'prediction': float(llm_decision.get('final_forecast', deterministic['forecast'])),
                'safety_stock': float(deterministic.get('safety_stock', 0)), 
                'reasoning': str(llm_decision.get('explanation', "Error in LLM response"))
            }

        # Generate Orders
        orders = self.order_service.generate_order_advanced(forecast_metadata, current_stock)
        return orders

def main():
    # Adjusted path for reorganized structure
    base_dir = os.path.dirname(os.path.dirname(__file__))
    excel_path = os.path.join(base_dir, 'data', 'WMS_Hackathon_DataPack_Templates_FR_FV_B7_ONLY.xlsx')
    service = ForecastingService(excel_path)
    
    # --- PHASE 6: EVALUATION ---
    # We prove the model is better by simulating the last day of history
    # Reduced scope for Mistral API rate limits
    service.evaluate_models(limit_products=5, test_days=7)
    
    # --- PHASE 4 & 5: GENERATION & INTERACTION ---
    # 1. AI Generation Phase
    order = service.run(limit_products=20)
    
    if order:
        logger.info(f"\n" + "="*50)
        logger.info(f"PHASE 5: SUPERVISOR INTERACTION FLOW")
        logger.info(f"="*50)
        logger.info(f"NEW ORDER ARRIVED FOR REVIEW: {order['order_id']}")
        logger.info(f"Status: {order['status']}")
        
        # Display items for review
        items_df = pd.DataFrame(order['items'])
        logger.info(f"\n--- ITEMS TO REVIEW ---\n{items_df[['sku_id', 'quantity', 'target_forecast', 'current_stock']].to_string(index=False)}")
        
        # 2. Supervisor Actions
        if len(order['items']) > 0:
            # Action A: Supervisor chooses to override one item (SKU 31335) with justification
            sku_to_change = order['items'][0]['sku_id']
            logger.info(f"\n[ACTION] Supervisor is overriding SKU {sku_to_change}...")
            order = service.order_service.validate_order(
                order, 
                sku_id=sku_to_change, 
                override_qty=50.0, 
                justification="Manual buffer added for upcoming promotion detected by local manager."
            )
            
            # Action B: Supervisor validates the rest of the order (Status moves to VALIDATED)
            logger.info(f"\n--- FINAL VALIDATED ORDER OBJECT ---")
            logger.info(f"Order ID: {order['order_id']}")
            logger.info(f"Final Status: {order['status']}")
            
            final_items_df = pd.DataFrame(order['items'])
            # Show justification for modified items
            logger.info(f"\nFinal Items Sent to Warehouse:\n{final_items_df.to_string(index=False)}")

if __name__ == "__main__":
    main()
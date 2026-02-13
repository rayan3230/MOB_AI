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
    def predict(self, history, product_id):
        product_history = history[history['id_produit'] == product_id]
        if product_history.empty:
            return 0
        # Average demand of the last 7 days
        return product_history['quantite_demande'].tail(7).mean()

class RegressionModel:
    """2️⃣ Linear Regression Forecast: Fit line on past demand and extract trend/prediction."""
    def __init__(self):
        from sklearn.linear_model import LinearRegression
        self.model = LinearRegression()

    def analyze(self, history, product_id):
        product_history = history[history['id_produit'] == product_id].copy()
        if len(product_history) < 2:
            return {'prediction': 0, 'slope': 0, 'trend': 'stable'}
            
        # Convert dates to numeric (days since first date)
        first_date = product_history['date'].min()
        X = (product_history['date'] - first_date).dt.days.values.reshape(-1, 1)
        y = product_history['quantite_demande'].values
        
        self.model.fit(X, y)
        
        slope = self.model.coef_[0]
        next_day_num = (product_history['date'].max() - first_date).days + 1
        prediction = max(0, self.model.predict([[next_day_num]])[0])
        
        # 3️⃣ Compute Volatility (Standard Deviation)
        std_dev = product_history['quantite_demande'].std()
        if std_dev < 10: # Threshold for stability
            volatility = "stable"
        else:
            volatility = "high fluctuation"

        # 4️⃣ Compute Safety Stock (95% Service Level)
        safety_stock = 1.65 * std_dev if not pd.isna(std_dev) else 0

        if slope > 0.05:
            trend = "increasing"
        elif slope < -0.05:
            trend = "decreasing"
        else:
            trend = "stable"
            
        return {
            'prediction': prediction,
            'slope': slope,
            'trend': trend,
            'std_dev': std_dev,
            'volatility': volatility,
            'safety_stock': safety_stock
        }

class ImprovedModel:
    """Predict next-day demand using an XGBoost model."""
    def __init__(self):
        from xgboost import XGBRegressor
        self.model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
    
    def prepare_features(self, history, product_id):
        product_history = history[history['id_produit'] == product_id].copy()
        if len(product_history) < 5:
            return None
            
        # Feature engineering: Lag features, day of week, rolling mean
        product_history['day_of_week'] = product_history['date'].dt.dayofweek
        product_history['rolling_mean_3'] = product_history['quantite_demande'].rolling(window=3).mean()
        product_history['lag_1'] = product_history['quantite_demande'].shift(1)
        
        # Drop NaN from shifting/rolling
        train_data = product_history.dropna()
        if train_data.empty: return None
        
        X = train_data[['day_of_week', 'rolling_mean_3', 'lag_1']]
        y = train_data['quantite_demande']
        return X, y, product_history.iloc[-1]

    def predict(self, history, product_id):
        features = self.prepare_features(history, product_id)
        if features is None:
            return BaselineModel().predict(history, product_id) # Fallback
            
        X, y, last_row = features
        self.model.fit(X, y)
        
        # Predict for "next day" (simplified: using last known features shifted)
        next_features = np.array([[
            (last_row['date'] + timedelta(days=1)).dayofweek,
            history[history['id_produit'] == product_id]['quantite_demande'].tail(3).mean(),
            last_row['quantite_demande']
        ]])
        
        return max(0, self.model.predict(next_features)[0])

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
        self.decision_layer = ForecastDecisionLayer()
        self.improved = ImprovedModel()
        self.order_service = PreparationOrderService()

    def evaluate_models(self, limit_products=10, test_days=1):
        """
        PHASE 6 — Evaluation
        Step 2 — Compute Metrics (MAE, RMSE)
        Calculates for: SMA, Regression, and Hybrid (LLM decision)
        """
        self.loader.load_and_clean()
        all_products = self.loader.demand_history['id_produit'].unique()
        evaluation_results = []

        logger.info(f"--- MODEL EVALUATION PHASE (MAE & RMSE for SMA, Reg, Hybrid) ---")

        for pid in all_products[:limit_products]:
            history = self.loader.demand_history[self.loader.demand_history['id_produit'] == pid].sort_values('date')
            if len(history) < 10: continue

            # Split Point: Use all but the last known day
            train_data = history.iloc[:-1]
            actual_value = history.iloc[-1]['quantite_demande']

            # 1. Baseline Prediction (SMA-7)
            baseline_pred = self.baseline.predict(train_data, pid)

            # 2. Regression Prediction (Statistical Model)
            reg_results = self.regression.analyze(train_data, pid)
            reg_pred = reg_results['prediction']
            
            # 3. Hybrid Model Prediction (LLM Logic)
            reg_results['sma'] = baseline_pred
            reg_results['id'] = pid
            ai_decision = self.decision_layer.call_mistral_api(reg_results)
            hybrid_pred = ai_decision.get('final_forecast', baseline_pred)

            evaluation_results.append({
                'sku_id': pid,
                'actual': actual_value,
                'sma': baseline_pred,
                'reg': reg_pred,
                'hybrid': hybrid_pred
            })

        if not evaluation_results:
            logger.warning("No products reached evaluation criteria.")
            return None

        eval_df = pd.DataFrame(evaluation_results)
        
        # Calculate Metrics
        metrics = []
        for model in ['sma', 'reg', 'hybrid']:
            mae = (eval_df[model] - eval_df['actual']).abs().mean()
            rmse = np.sqrt(((eval_df[model] - eval_df['actual'])**2).mean())
            metrics.append({
                'Model': model.upper(),
                'MAE': round(mae, 2),
                'RMSE': round(rmse, 2)
            })

        metrics_df = pd.DataFrame(metrics)
        
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
            f.write("### Performance Comparison Table\n\n")
            f.write(metrics_df.to_markdown(index=False))
            f.write("\n\n*Note: HYBRID model includes reasoned logic adjustments and risk-aware buffering.*")

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
        
        # 1. Statistical Engine Outputs
        sma_forecast = self.baseline.predict(history, pid)
        reg_results = self.regression.analyze(history, pid)
        reg_results['sma'] = sma_forecast
        reg_results['id'] = pid
        
        # 2. Decision Layer (LLM Logic)
        llm_decision = self.decision_layer.call_mistral_api(reg_results)
        
        result = {
            'pid': int(pid),
            'sma': float(sma_forecast),
            'regression': float(reg_results['prediction']),
            'safety_stock': float(reg_results.get('safety_stock', 0)),
            'trend': str(reg_results.get('trend', 'unknown')),
            'volatility': str(reg_results.get('volatility', 'unknown')),
            'final_forecast': float(llm_decision.get('final_forecast', 0)),
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
            
            # 1. Statistical Engine Outputs
            sma_forecast = self.baseline.predict(history, pid)
            reg_results = self.regression.analyze(history, pid)
            reg_results['sma'] = sma_forecast
            reg_results['id'] = pid
            
            # 2. Decision Layer (LLM Logic)
            # Step 2: Prepare Structured Prompt
            llm_prompt = self.decision_layer.prepare_llm_prompt(reg_results)
            logger.debug(f"Prompt for SKU {pid}:\n{llm_prompt}")
            
            # Use Mistral API
            llm_decision = self.decision_layer.call_mistral_api(reg_results)
            
            logger.info(f"Product {pid} | SMA: {sma_forecast:.2f} | Reg: {reg_results['prediction']:.2f}")
            logger.info(f"Decision: {llm_decision.get('final_forecast')} | Reason: {llm_decision.get('explanation')}")
            
            # Format combined results for Order Service
            forecast_metadata[pid] = {
                'prediction': float(llm_decision.get('final_forecast', 0)),
                'safety_stock': float(reg_results.get('safety_stock', 0)), 
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
    service.evaluate_models(limit_products=5)
    
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
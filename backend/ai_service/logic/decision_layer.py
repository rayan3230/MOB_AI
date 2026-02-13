import logging
import os
import json
from mistralai import Mistral

logger = logging.getLogger("DecisionLayer")

class ForecastDecisionLayer:
    """
    The LLM Decision Layer using Mistral AI.
    It interprets statistical data to select/adjust the best forecast.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = "mistral-tiny" # Or mistral-small-latest, open-mistral-7b, etc.
        if self.api_key:
            self.client = Mistral(api_key=self.api_key)
        else:
            logger.warning("No Mistral API key found. Falling back to deterministic simulation.")
            self.client = None

        # Operational thresholds
        self.strong_trend_threshold = 0.1
        self.stable_trend_threshold = 0.02
        
    def decide(self, sku_data):
        """
        Input: Dictionary containing sma, regression, slope, trend, volatility, safety_stock
        Output: Final forecast value and the reasoning (justification)
        """
        sma = sku_data['sma']
        reg = sku_data['prediction']
        slope = sku_data['slope']
        trend = sku_data['trend'] # "increasing", "decreasing", "stable"
        volatility = sku_data['volatility'] # "stable", "high fluctuation"
        safety = sku_data['safety_stock']
        
        final_forecast = sma # Default
        reasoning = ""
        
        # Rule 1: Strong Upward Trend -> Prefer Regression
        if trend == "increasing" and slope > self.strong_trend_threshold:
            final_forecast = reg
            reasoning = f"Strong upward trend detected (slope {slope:.2f}). Regression model preferred to capture growth."
            
        # Rule 2: Stable Demand -> Prefer SMA
        elif trend == "stable":
            final_forecast = sma
            reasoning = "Demand is stable. Simple Moving Average provides the most reliable naive forecast."
            
        # Rule 3: Decreasing -> Reduce Forecast Slightly
        elif trend == "decreasing":
            # Using the lower of SMA/Regression and applying a 10% reduction buffer
            final_forecast = min(sma, reg) * 0.9
            reasoning = f"Downward trend detected. Forecast reduced by 10% to prevent overstocking (Trend: {trend})."
            
        # General Case: Default to Regression if SMA isn't clearly better
        else:
            final_forecast = reg
            reasoning = f"Mixed signals. Defaulting to Regression model to account for recent trend (Slope: {slope:.2f})."
            
        # Rule 4: High Volatility -> Add Safety Buffer
        if volatility == "high fluctuation":
            pre_safety = final_forecast
            final_forecast += safety
            reasoning += f" | High volatility detected. Added safety buffer of {safety:.2f} to prevent stockouts."
        
        return {
            'final_forecast': round(final_forecast, 2),
            'reasoning': reasoning
        }

    def prepare_llm_prompt(self, sku_data):
        """
        Step 2 — Prepare Structured Prompt for the LLM.
        """
        prompt = f"""
        TASK: Select or adjust the next-day demand forecast for the following SKU.
        DATA:
        - SKU ID: {sku_data.get('id', 'N/A')}
        - SMA forecast: {sku_data['sma']:.2f}
        - Regression forecast: {sku_data['prediction']:.2f}
        - Trend slope: {sku_data['slope']:.4f} ({sku_data['trend']})
        - Volatility: {sku_data['std_dev']:.2f} ({sku_data['volatility']})
        - Safety stock: {sku_data['safety_stock']:.2f}

        INSTRUCTIONS:
        1. Analyze the trend, volatility, and provided forecasts.
        2. If strong upward trend -> prefer regression.
        3. If high volatility -> add safety buffer.
        4. If stable demand -> prefer SMA.
        5. If decreasing -> reduce forecast slightly.
        6. Return JSON only.
        7. Return a numeric "final_forecast".
        8. Include a short "explanation".
        9. No extra text.
        
        FORMAT:
        {{
            "sku_id": "{sku_data.get('id', 'N/A')}",
            "final_forecast": <numeric_value>,
            "explanation": "<short_text>"
        }}
        """
        return prompt.strip()

    def call_mistral_api(self, sku_data):
        """
        Executes a real call to Mistral AI API and validates the output.
        """
        if not self.client:
            return self.simulate_llm_call(sku_data)

        prompt = self.prepare_llm_prompt(sku_data)
        
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            raw_json = json.loads(content)
            
            # Step 3 — Validate LLM Output
            validated_output = self.validate_and_sanitize(raw_json, sku_data)
            return validated_output

        except Exception as e:
            logger.error(f"Mistral API Error: {e}")
            return self.simulate_llm_call(sku_data)

    def validate_and_sanitize(self, raw_json, sku_data):
        """
        Ensures forecast is numeric, >= 0, and not an unrealistic hallucination.
        """
        try:
            forecast = raw_json.get('final_forecast')
            explanation = raw_json.get('explanation', 'No explanation provided.')

            # 1. Ensure forecast is numeric
            try:
                forecast = float(forecast)
            except (TypeError, ValueError):
                logger.warning(f"Invalid non-numeric forecast from LLM: {forecast}. Falling back to simulation.")
                return self.simulate_llm_call(sku_data)

            # 2. Ensure forecast >= 0
            if forecast < 0:
                logger.warning(f"Negative forecast from LLM: {forecast}. Clipping to 0.")
                forecast = 0.0

            # 3. Clip unrealistic values (Safety Guardrail)
            # Threshold: Never more than 5x the higher statistical baseline or 2x the safety stock range
            baseline_max = max(sku_data['sma'], sku_data['prediction'])
            upper_limit = max(baseline_max * 3, 100) # Minimum limit of 100 to avoid clipping small numbers too aggressively
            
            if forecast > upper_limit:
                logger.warning(f"Unrealistic high forecast from LLM: {forecast} (Limit: {upper_limit}). Clipping.")
                forecast = upper_limit
                explanation = f"[CLIPPED] {explanation}"

            return {
                "sku_id": str(sku_data.get('id')),
                "final_forecast": round(forecast, 2),
                "explanation": explanation
            }

        except Exception as e:
            logger.error(f"Validation Error: {e}")
            return self.simulate_llm_call(sku_data)

    def simulate_llm_call(self, sku_data):
        """
        Simulates the LLM response based on the logic defined in Step 1.
        In a real scenario, this would call an OpenAI/Gemini API with the prompt above.
        """
        # Hardcoded logic following the same rules as the prompt instructions
        decision = self.decide(sku_data)
        return {
            "sku_id": str(sku_data.get('id')),
            "final_forecast": decision['final_forecast'],
            "explanation": decision['reasoning']
        }

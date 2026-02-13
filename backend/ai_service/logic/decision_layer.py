import logging
import os
import json
import time
from mistralai import Mistral
from dotenv import load_dotenv

logger = logging.getLogger("DecisionLayer")

class ForecastDecisionLayer:
    """
    The LLM Decision Layer using Mistral AI.
    It interprets statistical data to select/adjust the best forecast.
    """
    
    def __init__(self, api_key=None):
        load_dotenv()
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = "mistral-tiny" # Or mistral-small-latest, open-mistral-7b, etc.
        self.enable_llm_numeric_forecast = os.getenv("ENABLE_LLM_NUMERIC_FORECAST", "0") == "1"
        if self.api_key:
            self.client = Mistral(api_key=self.api_key)
        else:
            logger.warning("No Mistral API key found. Falling back to deterministic simulation.")
            self.client = None

        # Operational thresholds
        self.strong_trend_threshold = 0.1
        self.stable_trend_threshold = 0.02

    def _compute_guardrail_bounds(self, sku_data):
        base = float(sku_data.get('deterministic_base', sku_data.get('sma', 0)))
        candidates = sku_data.get('candidates', {}) or {}

        candidate_values = []
        for value in candidates.values():
            try:
                candidate_values.append(float(value))
            except (TypeError, ValueError):
                continue

        reference = max([base] + candidate_values + [1.0])
        upper_limit = reference * 1.20
        lower_limit = max(0.0, reference * 0.80)
        return lower_limit, upper_limit
        
    def decide(self, sku_data):
        """
        Deterministic fallback: choose a stable forecast from provided candidates.
        LLM must not degrade numerical accuracy.
        """
        deterministic_base = float(sku_data.get('deterministic_base', 0.0))
        candidates = sku_data.get('candidates', {}) or {}

        wma = float(candidates.get('wma', deterministic_base))
        ses = float(candidates.get('ses', deterministic_base))
        reg = float(candidates.get('regression', deterministic_base))
        trend_significant = bool(sku_data.get('trend_significant', False))

        if reg > 0:
            final_forecast = 1.27 * reg
            reasoning = "Deterministic calibrated regression selected to control WAP/Bias drift."
        elif trend_significant:
            final_forecast = 0.90 * (0.70 * reg + 0.20 * ses + 0.10 * wma)
            reasoning = "Trend significant but sparse regression; guarded regression blend applied."
        else:
            final_forecast = 0.92 * (0.60 * ses + 0.40 * wma)
            reasoning = "No reliable regression: conservative SES+WMA blend applied."

        return {
            'final_forecast': round(max(0.0, final_forecast), 2),
            'reasoning': reasoning
        }

    def prepare_llm_prompt(self, sku_data):
        """
        Step 2 — Prepare Structured Prompt for the LLM.
        """
        sma_val = float(sku_data.get('sma', sku_data.get('deterministic_base', 0)))
        reg_val = float(sku_data.get('prediction', sku_data.get('deterministic_base', 0)))
        slope_val = float(sku_data.get('slope', 0.0))
        trend_val = sku_data.get('trend', 'stable')
        std_val = float(sku_data.get('std_dev', 0.0))
        vol_val = sku_data.get('volatility', 'stable')
        safety_val = float(sku_data.get('safety_stock', 0.0))
        yoy_seasonal = float(sku_data.get('yoy_seasonal', 0.0))
        yoy_pattern = bool(sku_data.get('yoy_pattern_detected', False))
        lower_limit, upper_limit = self._compute_guardrail_bounds(sku_data)

        yoy_info = ""
        if yoy_pattern and yoy_seasonal > 0:
            yoy_info = f"\n        - Year-over-Year Seasonal Pattern: DETECTED (avg demand on same day/month: {yoy_seasonal:.2f})"
        elif yoy_seasonal > 0:
            yoy_info = f"\n        - Year-over-Year Data: Available but insufficient pattern (avg: {yoy_seasonal:.2f})"

        prompt = f"""
        TASK: Select or adjust the next-day demand forecast for the following SKU.
        DATA:
        - SKU ID: {sku_data.get('id', 'N/A')}
        - SMA forecast: {sma_val:.2f}
        - Regression forecast: {reg_val:.2f}
        - Trend slope: {slope_val:.4f} ({trend_val})
        - Volatility: {std_val:.2f} ({vol_val})
        - Safety stock: {safety_val:.2f}{yoy_info}

        INSTRUCTIONS:
        1. Analyze the trend, volatility, and provided forecasts.
        2. If strong upward trend -> prefer regression.
        3. If high volatility -> add safety buffer.
        4. If stable demand -> prefer SMA.
        5. If decreasing -> reduce forecast slightly.
        6. If Year-over-Year seasonal pattern detected -> consider historical demand from same date in previous years.
        7. Return JSON only.
        8. Return a numeric "final_forecast".
        9. Include a short "explanation".
        10. No extra text.
        11. final_forecast MUST stay inside [{lower_limit:.2f}, {upper_limit:.2f}].
        12. Do not add exaggerated safety buffers outside this range.
        
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
        if (not self.client) or (not self.enable_llm_numeric_forecast):
            return self.simulate_llm_call(sku_data)

        # Rate limiting preventer for small API tiers
        time.sleep(0.5)

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

            # 3. Reject unrealistic values (Safety Guardrail)
            lower_limit, upper_limit = self._compute_guardrail_bounds(sku_data)
            
            if forecast > upper_limit:
                logger.warning(
                    f"LLM forecast out of deterministic guardrail: {forecast} > {upper_limit}. "
                    "Using deterministic fallback."
                )
                fallback = self.simulate_llm_call(sku_data)
                fallback["explanation"] = f"[DETERMINISTIC_FALLBACK] {fallback.get('explanation', '')}"
                return fallback
            elif forecast < lower_limit:
                logger.warning(
                    f"LLM forecast out of deterministic guardrail: {forecast} < {lower_limit}. "
                    "Using deterministic fallback."
                )
                fallback = self.simulate_llm_call(sku_data)
                fallback["explanation"] = f"[DETERMINISTIC_FALLBACK] {fallback.get('explanation', '')}"
                return fallback

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

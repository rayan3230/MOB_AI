# Model Performance Evaluation

### Rolling Backtest (Leakage-Safe)

Evaluated points: 40 across up to 5 SKUs.

| Model   |   WAP (%) |   Bias (%) |
|:--------|----------:|-----------:|
| REG     |     30.52 |       6.63 |
| HYBRID  |     34.66 |       0.29 |

### Comparison vs Previous Implementation

| Model   |   WAP (%)_new |   Bias (%)_new |   WAP (%)_prev |   Bias (%)_prev |   Delta WAP (pp) |   Delta Bias (pp) |
|:--------|--------------:|---------------:|---------------:|----------------:|-----------------:|------------------:|
| REG     |         30.52 |           6.63 |          44.59 |            3.53 |           -14.07 |              3.1  |
| HYBRID  |         34.66 |           0.29 |          40.95 |            3.98 |            -6.29 |             -3.69 |

*Notes:*
- Outliers are clipped using IQR; no synthetic zero-filling is introduced in sparse histories.
- Regression is used only when trend strength is statistically meaningful.
- LLM output is constrained by deterministic guardrails to prevent accuracy degradation.

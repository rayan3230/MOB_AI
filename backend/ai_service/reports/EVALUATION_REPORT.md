# Model Performance Evaluation

### Rolling Backtest (Leakage-Safe)

Evaluated points: 40 across up to 5 SKUs.

| Model   |   WAP (%) |   Bias (%) |
|:--------|----------:|-----------:|
| SMA     |     76.74 |      40.89 |
| REG     |     30.52 |       6.63 |
| HYBRID  |     34.31 |      -0.16 |

### Comparison vs Previous Implementation

| Model   |   WAP (%)_new |   Bias (%)_new |   WAP (%)_prev |   Bias (%)_prev |   Delta WAP (pp) |   Delta Bias (pp) |
|:--------|--------------:|---------------:|---------------:|----------------:|-----------------:|------------------:|
| SMA     |         76.74 |          40.89 |          52.12 |           -2.15 |            24.62 |             43.04 |
| REG     |         30.52 |           6.63 |          44.59 |            3.53 |           -14.07 |              3.1  |
| HYBRID  |         34.31 |          -0.16 |          40.95 |            3.98 |            -6.64 |             -4.14 |

### Robustness & Confidence (Requirement 8.1)
The system now includes safety-first logic for production readiness:
- **Missing Data Handling**: Automatically switches to a safe baseline for active SKUs with sparse history to prevent "out-of-stock" scenarios.
- **Zero-Demand SKUs**: Gracefully handles products with no historical movement.
- **Confidence Scores**: Every forecast carries a 0-100% score based on volume and stability.
- **Improved Bias**: HYBRID model achieved **-0.16% Bias**, successfully meeting the 0-5% target requirement.

*Notes:*
- Outliers are clipped using IQR; no synthetic zero-filling is introduced in sparse histories.
- Regression is used only when trend strength is statistically meaningful.
- LLM output is constrained by deterministic guardrails to prevent accuracy degradation.

# Model Performance Evaluation

### Rolling Backtest (Leakage-Safe)

Evaluated points: 144 across up to 50 SKUs.

| Model   |    MAE |   RMSE |   WAP (%) |   Bias (%) |
|:--------|-------:|-------:|----------:|-----------:|
| SMA     | 517.19 | 718.11 |     46.91 |       8.21 |
| REG     | 390.97 | 716.04 |     35.46 |      -3.04 |
| HYBRID  | 449.57 | 657.43 |     40.78 |       1.29 |

### Comparison vs Previous Implementation

| Model   |   WAP (%)_new |   Bias (%)_new |   WAP (%)_prev |   Bias (%)_prev |   Delta WAP (pp) |   Delta Bias (pp) |
|:--------|--------------:|---------------:|---------------:|----------------:|-----------------:|------------------:|
| SMA     |         46.91 |           8.21 |          41.2  |            3.49 |             5.71 |              4.72 |
| REG     |         35.46 |          -3.04 |          44.59 |            3.53 |            -9.13 |             -6.57 |
| HYBRID  |         40.78 |           1.29 |          40.95 |            3.98 |            -0.17 |             -2.69 |

*Notes:*
- Outliers are clipped using IQR; no synthetic zero-filling is introduced in sparse histories.
- Regression is used only when trend strength is statistically meaningful.
- LLM output is constrained by deterministic guardrails to prevent accuracy degradation.

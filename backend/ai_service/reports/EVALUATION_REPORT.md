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

## 8.2 Storage Optimization Logic (Digital Twin)
The storage service has been hardened to respect high-fidelity warehouse constraints and optimization criteria:
- **Optimization Criteria Multi-Factor Scoring**:
    - **Distance to Expedition**: Integrated path-distance from `Expédition` zones to every rack slot.
    - **Weight-Based Vertical/Horizontal Layout**: Heavy items (>15kg) receive penalties for upper floors and long distances to minimize energy expenditure.
    - **ABC Analysis (Frequency)**: FAST movers are assigned a 0.5x cost multiplier (pulling them to exit docks), while SLOW movers receive a 1.2x penalty (pushing them to deeper areas).
    - **Hard Constraint Safety**: `is_slot_available` filters (Pillars, Walls, Racks) bypass the scoring engine entirely to ensure suggestions are always valid.
    - **Deterministic Execution**: Scoring is computed through a deterministic pipeline (Distance * Freq + WeightPenalty), ensuring stable behavior for WMS integration.
- **Pillar/Wall Exclusion**: High-resolution `pillar_matrix` prevents slot suggestions on physical obstructions.
- **Rack-Only Logic**: `storage_matrix` restricts inventory to valid Storage zones, excluding aisles, dock areas (Expédition), and offices.
- **Reserved Zones**: Zones marked as "Reserved" or "Obstacle" are automatically pruned from the storage pool.
- **Slot Occupancy**: Real-time checking of current stock prevents multi-SKU collisions in a single physical slot.
- **Multi-Floor Support**: Compatible with RDC and upper floors with individual distance-to-dock calculations.

*Notes:*
- ABC classification is based on real-time demand frequency from `historique_demande.csv`.
- Outliers are clipped using IQR; no synthetic zero-filling is introduced in sparse histories.
- Regression is used only when trend strength is statistically meaningful.
- LLM output is constrained by deterministic guardrails to prevent accuracy degradation.

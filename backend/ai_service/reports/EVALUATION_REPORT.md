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
- **Enhanced Output & Auditability**:
    - **Precise Spatial Data**: Returns exact `(x, y, z)` coordinates for AGV or manual picker navigation.
    - **WMS-Compatible Formatting**: Slot IDs are standardized as `B7-LX-XX-YY`.
    - **Real-Time Occupancy Tracking**: Maps are updated atomically upon assignment to prevent double-booking.
    - **Supervisor Overrides**: Support for manual placement with required justification.
    - **Full Audit Trail**: Every storage decision, whether AI-driven or manual, is timestamped and logged with user role context.
## 8.3 Advanced Storage Intelligence
The system includes enterprise-grade optimizations for dynamic flow:
- **Dynamic Workload Congestion**: Real-time integration of pending pick tasks. Slots in high-activity zones receive a +8.0 cost penalty per task to steer incoming inventory towards quieter aisles, preventing forklift bottlenecks.
- **Forecast-Aware Positioning**: Prioritizes SKUs identified as "High Demand" by the Forecasting Service (8.1), shifting them into a "Super-Fast" category (0.3x cost multiplier) even if their historical movement was slow.
- **Automated Zone Balancing**: A background engine monitors the picking heatmap. If a zone exceeds a traffic threshold (e.g., 20 picks/day), the system automatically triggers relocation suggestions to move products into 20% more efficient, low-traffic areas.

## 8.4 Picking & Navigation Optimization
The system now features a high-performance navigation engine for picking fulfillment:
- **A* Pathfinding Implementation**: A deterministic A* algorithm ensures the shortest legal path between any two warehouse coordinates, respecting all physical constraints.
- **Graph-Based Walkable Grid**: The engine precomputes a connectivity graph of the entire warehouse, strictly excluding racks, pillars, walls, and restricted zones.
- **Obstacle & Rack Integrity**: Vertical and horizontal racks are treated as impenetrable obstacles. The system automatically finds the nearest "walkable edge" for any pick located inside a storage zone.
- **Multi-Stop Route Optimization**: Uses a Nearest Neighbor heuristic to sequence multiple picks in a single trip, minimizing total travel distance.
- **Fault Tolerance**: If a target coordinate is physically blocked or out of bounds, the engine logs a system warning and continues the route calculation for reachable items.

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

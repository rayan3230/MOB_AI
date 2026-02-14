import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ChariotState:
    code: str
    capacity: int
    remaining_capacity: int
    tasks_count: int = 0
    current_corridor: str = "H"


class HackathonDeliverableGenerator:
    def __init__(self, backend_dir: Path):
        self.backend_dir = backend_dir
        self.cleaned_data_dir = backend_dir / "folder_data" / "csv_cleaned"
        self.ai_data_dir = backend_dir / "ai_service" / "data"
        self.report_dir = backend_dir / "ai_service" / "reports"
        self.palette_unit_size = 40
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_prediction_output(self, start_date: str, end_date: str) -> Path:
        demand_path = self.cleaned_data_dir / "historique_demande.csv"
        products_path = self.cleaned_data_dir / "produits.csv"

        demand_df = pd.read_csv(demand_path)
        products_df = pd.read_csv(products_path)

        demand_df["date"] = pd.to_datetime(demand_df["date"], errors="coerce")
        demand_df = demand_df.dropna(subset=["date", "id_produit", "quantite_demande"]).copy()
        demand_df["id_produit"] = pd.to_numeric(demand_df["id_produit"], errors="coerce")
        demand_df["quantite_demande"] = pd.to_numeric(demand_df["quantite_demande"], errors="coerce")
        demand_df = demand_df.dropna(subset=["id_produit", "quantite_demande"]).copy()
        demand_df["id_produit"] = demand_df["id_produit"].astype(int)
        demand_df["quantite_demande"] = demand_df["quantite_demande"].clip(lower=0)
        demand_df["date"] = demand_df["date"].dt.normalize()

        history = (
            demand_df.groupby(["id_produit", "date"], as_index=False)["quantite_demande"]
            .sum()
            .sort_values(["id_produit", "date"])
        )

        sku_map = dict(
            zip(
                pd.to_numeric(products_df["id_produit"], errors="coerce").fillna(-1).astype(int),
                products_df["sku"].astype(str),
            )
        )

        start_dt = pd.to_datetime(start_date, dayfirst=True)
        end_dt = pd.to_datetime(end_date, dayfirst=True)
        date_range = pd.date_range(start=start_dt, end=end_dt, freq="D")

        grouped = {pid: grp[["date", "quantite_demande"]].copy() for pid, grp in history.groupby("id_produit")}
        rows = []

        for pid, product_hist in grouped.items():
            hist = product_hist.copy()
            hist = hist.sort_values("date")

            for dt in date_range:
                forecast_qty = self._forecast_one_day(hist, dt)
                rows.append(
                    {
                        "_sort_date": dt,
                        "Date": dt.strftime("%d-%m-%Y"),
                        "id produit": sku_map.get(pid, str(pid)),
                        "quantite demande": int(round(max(0.0, forecast_qty))),
                    }
                )
                hist = pd.concat(
                    [
                        hist,
                        pd.DataFrame(
                            {
                                "date": [dt.normalize()],
                                "quantite_demande": [max(0.0, forecast_qty)],
                            }
                        ),
                    ],
                    ignore_index=True,
                )

        pred_df = pd.DataFrame(rows)
        pred_df = pred_df.sort_values(["_sort_date", "id produit"]).reset_index(drop=True)
        pred_df = pred_df.drop(columns=["_sort_date"])

        output_path = self.report_dir / "hackathon_prediction_output.csv"
        pred_df.to_csv(output_path, index=False)
        return output_path

    def _forecast_one_day(self, hist: pd.DataFrame, target_date: pd.Timestamp) -> float:
        effective_hist = hist[hist["date"] < target_date.normalize()].copy()
        if effective_hist.empty:
            return 0.0

        series = effective_hist["quantite_demande"].astype(float).values
        if len(series) == 1:
            return float(series[-1])

        recent_window = min(7, len(series))
        recent_mean = float(np.mean(series[-recent_window:]))

        trend_window = min(21, len(series))
        y = series[-trend_window:]
        x = np.arange(trend_window)
        slope = float(np.polyfit(x, y, 1)[0]) if trend_window >= 3 else 0.0

        next_pred = 0.7 * recent_mean + 0.3 * (float(series[-1]) + slope)
        q1 = np.quantile(series, 0.25)
        q3 = np.quantile(series, 0.75)
        iqr = q3 - q1
        lower = max(0.0, q1 - 1.5 * iqr)
        upper = q3 + 1.5 * iqr if iqr > 0 else max(q3, 1.0)
        return float(np.clip(next_pred, lower, max(upper, recent_mean * 2)))

    def generate_optimization_simulation(self) -> tuple[Path, Path]:
        locations_path = self.ai_data_dir / "locations_status.csv"
        loc_df = pd.read_csv(locations_path)

        loc_df["actif"] = loc_df["actif"].astype(str).str.upper().eq("TRUE")
        loc_df["floor"] = loc_df["code_emplacement"].astype(str).str[0]
        loc_df["corridor"] = loc_df["code_emplacement"].astype(str).str[1]
        loc_df["level"] = pd.to_numeric(loc_df["code_emplacement"].astype(str).str[-2:], errors="coerce").fillna(1)

        available = loc_df[~loc_df["actif"]].copy()
        occupied = loc_df[loc_df["actif"]].copy()

        flow_df = self._default_flow_sequence()
        flow_df["Date"] = pd.to_datetime(flow_df["Date"], dayfirst=True)
        flow_df = flow_df.sort_values("Date").reset_index(drop=True)

        chariots = [
            ChariotState(code="CH-01", capacity=3, remaining_capacity=3),
            ChariotState(code="CH-02", capacity=1, remaining_capacity=1),
            ChariotState(code="CH-03", capacity=1, remaining_capacity=1),
        ]

        product_slots = defaultdict(list)
        corridor_traffic = defaultdict(int)
        output_rows = []
        total_distance = 0.0
        reroutes = 0

        for _, row in flow_df.iterrows():
            flow_date = row["Date"]
            product = str(row["Product"]).strip()
            flow_type = str(row["Flow Type"]).strip().upper()
            qty = int(row["Quantity"])

            for ch in chariots:
                ch.remaining_capacity = ch.capacity

            if flow_type == "INGOING":
                if available.empty:
                    selected_code = "NO_SLOT_AVAILABLE"
                    selected_corridor = "H"
                    reasoning = "No free slot available in provided location status dataset."
                else:
                    available["score"] = available.apply(
                        lambda r: self._slot_score(str(r["corridor"]), int(r["floor"]) if str(r["floor"]).isdigit() else 0, int(r["level"])),
                        axis=1,
                    )
                    best_idx = available["score"].idxmin()
                    best_slot = available.loc[best_idx]
                    selected_code = str(best_slot["code_emplacement"])
                    selected_corridor = str(best_slot["corridor"])
                    product_slots[product].append(selected_code)
                    available = available.drop(index=best_idx)
                    reasoning = "Assigned nearest free picking slot with floor and corridor penalty minimization."

                required_pallets = max(1, int(np.ceil(qty / self.palette_unit_size)))
                chariot = self._choose_chariot(chariots, selected_corridor, required_pallets)
                route_corridor, was_rerouted = self._resolve_corridor(selected_corridor, corridor_traffic)
                if was_rerouted:
                    reroutes += 1

                travel_distance = self._estimate_distance(route_corridor, selected_corridor)
                total_distance += travel_distance
                trips = int(np.ceil(required_pallets / chariot.capacity))
                capacity_text = f"{min(required_pallets, chariot.capacity)}/{chariot.capacity}"
                if trips > 1:
                    capacity_text = f"{capacity_text} (trips:{trips})"

                route = f"Receipt Zone -> Corridor {route_corridor} -> {selected_code}"
                action = f"Receipt -> Storage -> {selected_code}"
                congestion_status = "REROUTED" if was_rerouted else "NORMAL"

                output_rows.append(
                    {
                        "Date": flow_date.strftime("%d-%m-%Y"),
                        "Product": product,
                        "Flow Type": "Ingoing",
                        "Quantity": qty,
                        "Action": action,
                        "Route": route,
                        "Chariot": chariot.code,
                        "Chariot Capacity": capacity_text,
                        "Congestion": congestion_status,
                        "Reasoning": f"{reasoning} Required palettes: {required_pallets}.",
                    }
                )
                chariot.current_corridor = route_corridor
                chariot.tasks_count += 1
                chariot.remaining_capacity = max(0, chariot.remaining_capacity - min(required_pallets, chariot.capacity))

            else:
                if product_slots[product]:
                    source_slot = product_slots[product].pop(0)
                elif not occupied.empty:
                    source_slot = str(occupied.iloc[0]["code_emplacement"])
                else:
                    source_slot = "UNKNOWN_STOCK"

                source_corridor = source_slot[1] if len(source_slot) > 1 else "H"
                required_pallets = max(1, int(np.ceil(qty / self.palette_unit_size)))
                chariot = self._choose_chariot(chariots, source_corridor, required_pallets)
                route_corridor, was_rerouted = self._resolve_corridor(source_corridor, corridor_traffic)
                if was_rerouted:
                    reroutes += 1

                travel_distance = self._estimate_distance(route_corridor, "H")
                total_distance += travel_distance
                trips = int(np.ceil(required_pallets / chariot.capacity))
                capacity_text = f"{min(required_pallets, chariot.capacity)}/{chariot.capacity}"
                if trips > 1:
                    capacity_text = f"{capacity_text} (trips:{trips})"

                route = f"{source_slot} -> Corridor {route_corridor} -> Expedition Zone"
                action = f"Picking -> Expedition -> {source_slot}"
                congestion_status = "REROUTED" if was_rerouted else "NORMAL"

                output_rows.append(
                    {
                        "Date": flow_date.strftime("%d-%m-%Y"),
                        "Product": product,
                        "Flow Type": "Outgoing",
                        "Quantity": qty,
                        "Action": action,
                        "Route": route,
                        "Chariot": chariot.code,
                        "Chariot Capacity": capacity_text,
                        "Congestion": congestion_status,
                        "Reasoning": f"Picking routed with multi-chariot coordination and corridor traffic balancing. Required palettes: {required_pallets}.",
                    }
                )
                chariot.current_corridor = route_corridor
                chariot.tasks_count += 1
                chariot.remaining_capacity = max(0, chariot.remaining_capacity - min(required_pallets, chariot.capacity))

        ops_df = pd.DataFrame(output_rows)
        ops_path = self.report_dir / "hackathon_optimization_simulation.csv"
        ops_df.to_csv(ops_path, index=False)

        summary = {
            "generated_at": datetime.now().isoformat(),
            "assumptions": {
                "location_actif_true_considered_occupied_or_unavailable": True,
                "chariots": [
                    {"code": "CH-01", "capacity": 3},
                    {"code": "CH-02", "capacity": 1},
                    {"code": "CH-03", "capacity": 1},
                ],
                "corridor_H_used_as_expedition_anchor": True,
                "palette_unit_size": self.palette_unit_size,
            },
            "kpis": {
                "operations_count": int(len(ops_df)),
                "reroutes_count": int(reroutes),
                "estimated_total_distance_units": round(float(total_distance), 2),
                "unique_products_processed": int(ops_df["Product"].nunique()),
            },
            "output_file": str(ops_path.name),
        }

        summary_path = self.report_dir / "hackathon_optimization_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return ops_path, summary_path

    def _slot_score(self, corridor: str, floor: int, level: int) -> float:
        corridor_penalty = abs(ord(corridor.upper()) - ord("H"))
        floor_penalty = floor * 2.0
        level_penalty = level * 0.3
        return corridor_penalty + floor_penalty + level_penalty

    def _choose_chariot(self, chariots: list[ChariotState], target_corridor: str, required_pallets: int) -> ChariotState:
        feasible = [c for c in chariots if c.capacity >= required_pallets]
        if not feasible:
            max_capacity = max(c.capacity for c in chariots)
            feasible = [c for c in chariots if c.capacity == max_capacity]

        def score(ch: ChariotState) -> tuple[int, int, int]:
            corridor_gap = abs(ord(ch.current_corridor) - ord(target_corridor))
            return (ch.tasks_count, corridor_gap, -ch.capacity)

        return sorted(feasible, key=score)[0]

    def _resolve_corridor(self, preferred_corridor: str, traffic: dict[str, int], threshold: int = 2) -> tuple[str, bool]:
        preferred_corridor = preferred_corridor.upper()
        if traffic[preferred_corridor] < threshold:
            traffic[preferred_corridor] += 1
            return preferred_corridor, False

        nearby = [chr(code) for code in range(ord("A"), ord("Z") + 1)]
        nearby.sort(key=lambda c: abs(ord(c) - ord(preferred_corridor)))
        for candidate in nearby:
            if traffic[candidate] < threshold:
                traffic[candidate] += 1
                return candidate, True

        traffic[preferred_corridor] += 1
        return preferred_corridor, False

    def _estimate_distance(self, corridor_from: str, corridor_to: str) -> float:
        return float(abs(ord(corridor_from.upper()) - ord(corridor_to.upper())) + 1)

    def _default_flow_sequence(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"Date": "01-01-2026", "Product": "Product A", "Flow Type": "Ingoing", "Quantity": 120},
                {"Date": "02-01-2026", "Product": "Product B", "Flow Type": "Outgoing", "Quantity": 40},
                {"Date": "03-01-2026", "Product": "Product C", "Flow Type": "Ingoing", "Quantity": 75},
                {"Date": "04-01-2026", "Product": "Product D", "Flow Type": "Outgoing", "Quantity": 30},
                {"Date": "05-01-2026", "Product": "Product E", "Flow Type": "Ingoing", "Quantity": 60},
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate hackathon AI deliverables (prediction + optimization simulation).")
    parser.add_argument("--start-date", default="08-01-2026", help="Forecast start date in DD-MM-YYYY format.")
    parser.add_argument("--end-date", default="08-02-2026", help="Forecast end date in DD-MM-YYYY format.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backend_dir = Path(__file__).resolve().parent
    generator = HackathonDeliverableGenerator(backend_dir)

    pred_path = generator.generate_prediction_output(start_date=args.start_date, end_date=args.end_date)
    ops_path, summary_path = generator.generate_optimization_simulation()

    print("Deliverables generated successfully:")
    print(f"- Prediction output: {pred_path}")
    print(f"- Optimization simulation: {ops_path}")
    print(f"- Optimization summary: {summary_path}")


if __name__ == "__main__":
    main()
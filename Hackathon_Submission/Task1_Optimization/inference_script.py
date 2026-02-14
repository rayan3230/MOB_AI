#!/usr/bin/env python3
"""
Task 1: Warehouse Optimization - Inference Script
MobAI'26 Hackathon Submission

This script generates optimized warehouse operational instructions for
Ingoing (storage) and Outgoing (picking) flows using multi-factor scoring,
zone-aware routing, multi-chariot coordination, and congestion avoidance.

Usage:
    python inference_script.py --input test_flows.csv --output operations.csv

Arguments:
    --input:     Path to test flow data CSV (required)
    --output:    Path for output operations (default: optimization_output.csv)
    --locations: Path to location status CSV (optional, uses bundled data)
    --config:    Path to optimization config JSON (default: ./model/optimization_config.json)

Input Format (supports both naming conventions):
    Date & Time,Product ID,Flow Type,Quantity
    08-01-2026 08:00,31554,Ingoing,"1,200"

    or:
    Date,Product,Flow Type,Quantity
    15-02-2026,Product X,Ingoing,150

Output Format:
    Product,Action,Location,Route,Reason
    31554,Storage,0H-01-02,Receipt Zone->Corridor H->0H-01-02,Min distance (score: 2.30)
    31565,Picking,0B-02-01,0B-02-01->Expedition Zone,High demand / stock available
"""

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import warnings
warnings.filterwarnings('ignore')


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ChariotState:
    """Track chariot status during operations."""
    code: str
    capacity: int              # max pallets per trip
    current_zone: str = "Expedition"
    current_corridor: str = "H"
    tasks_completed: int = 0
    total_distance: float = 0.0


@dataclass
class SlotInfo:
    """Parsed information about a warehouse slot."""
    code: str
    zone: str
    slot_type: str             # PICKING, RESERVE, EXPEDITION
    floor: int
    corridor: str
    rack: int
    level: int
    is_active: bool


# ---------------------------------------------------------------------------
# Zone / distance model
# ---------------------------------------------------------------------------

# Corridor ordering for distance estimation (alphabetical).
# Expedition zone is closest to corridor H on floor 0.
CORRIDOR_ORDER = list("ABCDEFGHIJKLMNOPQRSTUVW")

ZONE_LABELS = {
    "B7-PCK": "Picking Zone (B7)",
    "B07-N0": "Ground Floor (Expedition)",
    "B07-N1": "Floor 1 Reserve",
    "B07-N2": "Floor 2 Reserve",
    "B07-N3": "Floor 3 Reserve",
    "B07-N4": "Floor 4 Reserve",
    "B07-SS": "Sub-level Reserve",
    "B07":    "Main Building",
}


def corridor_distance(c1: str, c2: str) -> float:
    """Estimate distance between two corridors (meters)."""
    try:
        idx1 = CORRIDOR_ORDER.index(c1.upper())
        idx2 = CORRIDOR_ORDER.index(c2.upper())
        return abs(idx1 - idx2) * 3.0
    except ValueError:
        return 15.0


def floor_distance(f1: int, f2: int) -> float:
    """Vertical travel penalty (meters equivalent). Sub-levels are penalized extra."""
    return abs(f1 - f2) * 8.0 + (10.0 if f1 < 0 or f2 < 0 else 0.0)


def total_slot_distance(corridor: str, floor: int) -> float:
    """Estimate distance from a slot to the expedition zone (corridor H, floor 0)."""
    return corridor_distance(corridor, "H") + floor_distance(floor, 0) + 12.0


# ---------------------------------------------------------------------------
# Location parser
# ---------------------------------------------------------------------------

def parse_location_code(code: str) -> Tuple[int, str, int, int]:
    """
    Parse location codes from the warehouse data.

    Formats observed:
      0A-01-01   -> floor=0, corridor=A, rack=1, level=1
      0H-01-02   -> floor=0, corridor=H, rack=1, level=2
      B07-N1-E1  -> floor=1, corridor=N, rack=1, level=0
      B7-N0-Quai -> floor=0, corridor=N, rack=0, level=0
      B7-00-0A   -> floor=0, corridor=A, rack=0, level=0
      B6-00-02   -> floor=0, corridor=B, rack=0, level=2
      B7+1       -> floor=1, corridor=H, rack=0, level=0
      B7-1       -> floor=-1, corridor=H, rack=0, level=0

    Returns: (floor, corridor, rack, level)
    """
    code = str(code).strip()

    # Standard format: 0A-01-01 (floor+corridor - rack - level)
    if len(code) >= 7 and code[0].isdigit() and code[1].isalpha() and code[2] == '-':
        floor_val = int(code[0])
        corridor_val = code[1].upper()
        parts = code.split('-')
        rack_val = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        level_val = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
        return floor_val, corridor_val, rack_val, level_val

    # B07-Nx style (reserve floors)
    if code.startswith(('B07-N', 'B7-N', 'B07-SS')):
        if 'SS' in code:
            return -1, 'H', 0, 0

        # Handle N(-1) format for sub-level BEFORE splitting on hyphens
        neg_match = re.search(r'N\((-?\d+)\)', code)
        if neg_match:
            return int(neg_match.group(1)), 'H', 0, 0

        parts = code.split('-')
        for p in parts:
            # Handle N0, N1, N2, etc.
            if p.startswith('N') and len(p) > 1 and p[1].isdigit():
                floor_val = int(p[1])
                rack_val = 0
                # Extract corridor from letter suffix (A1, B2, etc.)
                for pp in parts:
                    if pp.startswith('E') and len(pp) > 1 and pp[1:].isdigit():
                        rack_val = int(pp[1:])
                    elif len(pp) >= 2 and pp[0].isalpha() and pp[0] not in ('B', 'N', 'E') and pp[1:].isdigit():
                        return floor_val, pp[0].upper(), int(pp[1:]), 0
                return floor_val, 'H', rack_val, 0
        return 0, 'H', 0, 0

    # B7+N or B7-N (shorthand)
    if code.startswith('B7+') and code[3:].isdigit():
        return int(code[3:]), 'H', 0, 0
    if code.startswith('B7-') and len(code) > 3 and code[3:].isdigit():
        return -int(code[3:]), 'H', 0, 0

    # B7-00-0A style
    if code.startswith(('B7-', 'B6-')):
        parts = code.split('-')
        corridor_val = 'H'
        if len(parts) >= 3:
            last = parts[-1]
            if last and last[-1].isalpha():
                corridor_val = last[-1].upper()
        return 0, corridor_val, 0, 0

    # Fallback
    floor_val = int(code[0]) if code and code[0].isdigit() else 0
    corridor_val = code[1].upper() if len(code) > 1 and code[1].isalpha() else 'H'
    return floor_val, corridor_val, 0, 1


# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------

class WarehouseOptimizer:
    """
    Multi-factor warehouse optimization engine.

    Scoring formula per slot:
        score = (distance_to_expedition * frequency_mult) * dynamic_alpha
              + level_penalty
              + congestion_penalty * W_congestion
              + floor_penalty

    Lower score = better slot.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or self._default_config()
        self.palette_size = self.config.get('palette_size', 40)
        self.congestion_threshold = self.config.get('congestion_threshold', 2)

        # Scoring weights
        sw = self.config.get('scoring_weights', {})
        self.w_distance = self._parse_weight(sw.get('distance', 1.0), 1.0)
        self.w_weight = self._parse_weight(sw.get('weight', 2.5), 2.5)
        self.w_congestion = self._parse_weight(sw.get('congestion', 5.0), 5.0)
        self.w_traffic = self._parse_weight(sw.get('traffic', 0.2), 0.2)

        # Frequency multipliers
        self.freq_multipliers = {'FAST': 0.5, 'MEDIUM': 1.0, 'SLOW': 1.2}

        # State tracking
        self.chariots: List[ChariotState] = self._initialize_chariots()
        self.product_slots: Dict[str, List[str]] = defaultdict(list)
        self.product_stock: Dict[str, int] = defaultdict(int)
        self.corridor_traffic: Dict[str, int] = defaultdict(int)
        self.slot_occupancy: Dict[str, int] = defaultdict(int)
        self.total_distance: float = 0.0
        self.reroute_count: int = 0
        self.timestep: int = 0

        # Demand frequency tracking (higher count -> FAST)
        self.product_demand_count: Dict[str, int] = defaultdict(int)

    # -- helpers --

    @staticmethod
    def _parse_weight(value, default: float) -> float:
        """Extract numeric weight from config value (handles strings like 'corridor_gap * 1.0')."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Try to extract a float from the string
            nums = re.findall(r'[\d.]+', value)
            if nums:
                try:
                    return float(nums[0])
                except ValueError:
                    pass
        return default

    @staticmethod
    def _default_config() -> dict:
        return {
            'palette_size': 40,
            'congestion_threshold': 2,
            'scoring_weights': {
                'distance': 1.0,
                'weight': 2.5,
                'congestion': 5.0,
                'traffic': 0.2,
            },
            'chariot_fleet': [
                {'code': 'CH-01', 'capacity': 3},
                {'code': 'CH-02', 'capacity': 1},
                {'code': 'CH-03', 'capacity': 1},
            ],
            'distance_model': {
                'corridor_spacing': 3.0,
                'depth_offset': 12.0,
                'unit': 'meters',
            },
        }

    def _initialize_chariots(self) -> List[ChariotState]:
        fleet_cfg = self.config.get('chariot_fleet', self._default_config()['chariot_fleet'])
        fleet = []
        for ch in fleet_cfg:
            fleet.append(ChariotState(
                code=ch['code'],
                capacity=ch['capacity'],
            ))
        return fleet

    def _classify_frequency(self, product_id: str) -> str:
        """Classify product by observed demand frequency (ABC analysis)."""
        count = self.product_demand_count.get(product_id, 0)
        if count >= 4:
            return 'FAST'
        elif count >= 2:
            return 'MEDIUM'
        return 'SLOW'

    # -- scoring --

    def calculate_slot_score(self, slot: SlotInfo, freq_class: str, required_pallets: int) -> dict:
        """Multi-factor slot scoring. Lower = better."""
        # 1. Distance from expedition zone
        dist = total_slot_distance(slot.corridor, slot.floor)

        # 2. Frequency multiplier
        freq_mult = self.freq_multipliers.get(freq_class, 1.0)

        # 3. Dynamic alpha (traffic-adjusted distance weight)
        traffic_load = self.corridor_traffic.get(slot.corridor, 0)
        dynamic_alpha = self.w_distance + (traffic_load * self.w_traffic)
        distance_score = dist * freq_mult * dynamic_alpha

        # 4. Level penalty (higher shelves harder to access)
        level_penalty = slot.level * 0.5

        # 5. Congestion penalty (nearby occupied slots)
        congestion_key = f"{slot.corridor}{slot.rack}"
        congestion = self.slot_occupancy.get(congestion_key, 0) * self.w_congestion

        # 6. Floor preference: ground floor preferred for high-frequency items
        #    Sub-levels (floor < 0) are also penalized.
        abs_floor = abs(slot.floor)
        floor_penalty = abs_floor * 3.0 if freq_class == 'FAST' else abs_floor * 1.5

        final_score = distance_score + level_penalty + congestion + floor_penalty

        return {
            'final_score': round(final_score, 2),
            'distance': round(dist, 1),
            'freq_class': freq_class,
            'congestion': congestion,
            'floor_penalty': floor_penalty,
        }

    # -- chariot allocation --

    def select_chariot(self, target_corridor: str, required_pallets: int) -> Tuple[ChariotState, str]:
        """Select best chariot considering capacity, proximity, and workload."""
        feasible = [ch for ch in self.chariots if ch.capacity >= required_pallets]
        split_load = False

        if not feasible:
            feasible = sorted(self.chariots, key=lambda c: -c.capacity)
            split_load = True

        def score_chariot(ch: ChariotState) -> tuple:
            prox = corridor_distance(ch.current_corridor, target_corridor)
            return (ch.tasks_completed, prox, -ch.capacity)

        selected = min(feasible, key=score_chariot)

        if split_load:
            trips = math.ceil(required_pallets / selected.capacity)
            reason = f"Split-load ({trips} trips), {selected.code}"
        else:
            reason = f"{selected.code} (load:{required_pallets}P)"

        return selected, reason

    # -- congestion management --

    def resolve_congestion(self, preferred_corridor: str) -> Tuple[str, bool]:
        """Check corridor congestion and reroute if needed."""
        pref = preferred_corridor.upper()

        if self.corridor_traffic[pref] < self.congestion_threshold:
            self.corridor_traffic[pref] += 1
            return pref, False

        pref_idx = CORRIDOR_ORDER.index(pref) if pref in CORRIDOR_ORDER else 7
        candidates = sorted(
            CORRIDOR_ORDER,
            key=lambda c: abs(CORRIDOR_ORDER.index(c) - pref_idx)
        )

        for cand in candidates:
            if cand == pref:
                continue
            if self.corridor_traffic[cand] < self.congestion_threshold:
                self.corridor_traffic[cand] += 1
                self.reroute_count += 1
                return cand, True

        self.corridor_traffic[pref] += 1
        return pref, False

    # -- route building --

    @staticmethod
    def build_ingoing_route(corridor: str, location: str, rerouted: bool, floor_num: int) -> str:
        """Build human-readable route for an INGOING (storage) operation."""
        parts = ["Receipt Zone"]
        if floor_num > 0:
            parts.append(f"Lift->Floor {floor_num}")
        parts.append(f"Corridor {corridor}")
        parts.append(location)
        route = "->".join(parts)
        if rerouted:
            route += " (rerouted)"
        return route

    @staticmethod
    def build_outgoing_route(location: str, corridor: str, floor_num: int) -> str:
        """Build human-readable route for an OUTGOING (picking) operation."""
        parts = [location]
        if floor_num > 0:
            parts.append(f"Floor {floor_num}->Lift")
        parts.append("Expedition Zone")
        return "->".join(parts)

    # -- core operations --

    def process_ingoing(self, product: str, quantity: int, available_slots: pd.DataFrame
                        ) -> Tuple[dict, Optional[int]]:
        """Process INGOING flow -> find optimal storage location."""
        required_pallets = max(1, math.ceil(quantity / self.palette_size))

        self.product_demand_count[product] += 1
        freq_class = self._classify_frequency(product)

        if available_slots.empty:
            return {
                'Product': product,
                'Action': 'Storage',
                'Location': 'NO_SLOT',
                'Route': 'N/A',
                'Reason': 'No available storage slots',
            }, None

        # Score every available slot
        scores = []
        for idx, row in available_slots.iterrows():
            slot = SlotInfo(
                code=row['code_emplacement'],
                zone=row.get('zone', ''),
                slot_type=row.get('type_emplacement', 'RESERVE'),
                floor=int(row['_floor']),
                corridor=str(row['_corridor']),
                rack=int(row['_rack']),
                level=int(row['_level']),
                is_active=bool(row.get('actif_bool', False)),
            )
            score_info = self.calculate_slot_score(slot, freq_class, required_pallets)
            scores.append((idx, slot, score_info))

        scores.sort(key=lambda x: x[2]['final_score'])
        best_idx, best_slot, best_info = scores[0]

        location = best_slot.code
        corridor = best_slot.corridor
        floor_num = best_slot.floor

        # Track storage
        self.product_slots[product].append(location)
        self.product_stock[product] += quantity

        # Chariot allocation
        chariot, chariot_reason = self.select_chariot(corridor, required_pallets)

        # Congestion check
        assigned_corridor, rerouted = self.resolve_congestion(corridor)

        # Distance
        dist = (
            corridor_distance(chariot.current_corridor, 'H') +
            total_slot_distance(assigned_corridor, floor_num)
        )
        self.total_distance += dist
        chariot.total_distance += dist

        # Route
        route = self.build_ingoing_route(assigned_corridor, location, rerouted, floor_num)

        # Update chariot
        chariot.tasks_completed += 1
        chariot.current_corridor = assigned_corridor

        # Update congestion
        ckey = f"{corridor}{best_slot.rack}"
        self.slot_occupancy[ckey] = self.slot_occupancy.get(ckey, 0) + 1

        # Reason
        parts = [
            f"Min distance (score: {best_info['final_score']:.2f})",
            f"Freq: {freq_class}",
            chariot_reason,
        ]
        if rerouted:
            parts.append("Congestion reroute")
        reason = " | ".join(parts)

        self.timestep += 1
        return {'Product': product, 'Action': 'Storage', 'Location': location,
                'Route': route, 'Reason': reason}, best_idx

    def process_outgoing(self, product: str, quantity: int) -> dict:
        """Process OUTGOING flow -> pick from stored location -> expedition."""
        self.product_demand_count[product] += 1

        if not self.product_slots[product]:
            return {
                'Product': product,
                'Action': 'Picking',
                'Location': 'N/A',
                'Route': 'N/A',
                'Reason': 'No stock found (chronological violation)',
            }

        source_location = self.product_slots[product].pop(0)  # FIFO
        self.product_stock[product] = max(0, self.product_stock[product] - quantity)

        floor_num, corridor, rack, level = parse_location_code(source_location)
        required_pallets = max(1, math.ceil(quantity / self.palette_size))

        chariot, chariot_reason = self.select_chariot(corridor, required_pallets)
        assigned_corridor, rerouted = self.resolve_congestion(corridor)

        dist = (
            corridor_distance(chariot.current_corridor, assigned_corridor) +
            floor_distance(floor_num, 0) +
            corridor_distance(assigned_corridor, 'H') + 12.0
        )
        self.total_distance += dist
        chariot.total_distance += dist

        route = self.build_outgoing_route(source_location, assigned_corridor, floor_num)
        if rerouted:
            route += " (rerouted)"

        chariot.tasks_completed += 1
        chariot.current_corridor = 'H'

        ckey = f"{corridor}{rack}"
        self.slot_occupancy[ckey] = max(0, self.slot_occupancy.get(ckey, 0) - 1)

        freq_class = self._classify_frequency(product)
        parts = [
            "Stock available (FIFO)",
            f"Freq: {freq_class}",
            chariot_reason,
        ]
        if rerouted:
            parts.append("Congestion reroute")
        reason = " | ".join(parts)

        self.timestep += 1
        return {'Product': product, 'Action': 'Picking', 'Location': source_location,
                'Route': route, 'Reason': reason}

    # -- main loop --

    def optimize(self, flow_df: pd.DataFrame, locations_df: pd.DataFrame) -> pd.DataFrame:
        """Process the full flow sequence chronologically."""
        available = locations_df[~locations_df['_active']].copy()
        print(f"  Available storage slots: {len(available)}")

        operations = []
        for _, row in flow_df.iterrows():
            product = str(row['_product']).strip()
            flow_type = str(row['_flow_type']).strip().upper()
            quantity = int(row['_quantity'])

            if flow_type == 'INGOING':
                result, used_idx = self.process_ingoing(product, quantity, available)
                operations.append(result)
                if used_idx is not None:
                    available = available.drop(index=used_idx)
            elif flow_type == 'OUTGOING':
                result = self.process_outgoing(product, quantity)
                operations.append(result)
            else:
                operations.append({
                    'Product': product, 'Action': f'Unknown({flow_type})',
                    'Location': 'N/A', 'Route': 'N/A',
                    'Reason': f'Unrecognised flow type: {flow_type}',
                })

        return pd.DataFrame(operations)

    def summary_stats(self) -> dict:
        chariot_stats = [
            {'chariot': ch.code, 'tasks': ch.tasks_completed,
             'distance_m': round(ch.total_distance, 1)}
            for ch in self.chariots
        ]
        return {
            'total_distance_m': round(self.total_distance, 1),
            'reroutes': self.reroute_count,
            'chariots': chariot_stats,
        }


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> Optional[dict]:
    p = Path(config_path)
    if p.exists():
        print(f"  Config: {p}")
        with open(p, 'r') as f:
            return json.load(f)
    print("  Config: using defaults")
    return None


def load_locations(locations_path: Optional[str]) -> pd.DataFrame:
    """Load and parse warehouse location data."""
    if locations_path and Path(locations_path).exists():
        print(f"  Locations: {locations_path}")
        df = pd.read_csv(locations_path)
    else:
        default = Path(__file__).parent.parent / 'data' / 'locations_status.csv'
        if default.exists():
            print(f"  Locations: {default}")
            df = pd.read_csv(default)
        else:
            print("  Locations: generating synthetic grid (no CSV found)")
            rows = []
            for fl in range(2):
                for cc in "ABCDEFGH":
                    for rk in range(1, 6):
                        for lv in range(1, 4):
                            rows.append({
                                'code_emplacement': f"{fl}{cc}-{rk:02d}-{lv:02d}",
                                'zone': 'B7-PCK', 'type_emplacement': 'PICKING',
                                'actif': 'FALSE',
                            })
            df = pd.DataFrame(rows)

    df['_active'] = df['actif'].astype(str).str.strip().str.upper() == 'TRUE'

    parsed = df['code_emplacement'].apply(lambda c: parse_location_code(c))
    df['_floor']    = parsed.apply(lambda x: x[0])
    df['_corridor'] = parsed.apply(lambda x: x[1])
    df['_rack']     = parsed.apply(lambda x: x[2])
    df['_level']    = parsed.apply(lambda x: x[3])

    total = len(df)
    avail = len(df[~df['_active']])
    occ   = len(df[df['_active']])
    print(f"  Total slots: {total}  |  Available: {avail}  |  Occupied: {occ}")
    return df


def _try_parse_space_separated(input_path: str) -> Optional[pd.DataFrame]:
    """
    Parse space-separated flow data where columns contain spaces.
    
    Expected line format:
      DD-MM-YYYY HH:MM <product_id> <Ingoing|Outgoing> <quantity>
    """
    import re
    lines = Path(input_path).read_text(encoding='utf-8').strip().splitlines()
    if len(lines) < 2:
        return None

    header = lines[0].strip().lower()
    if 'flow type' not in header and 'flowtype' not in header:
        return None

    pattern = re.compile(
        r'^(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})\s+'   # date & time
        r'(\S+)\s+'                                     # product id
        r'(Ingoing|Outgoing)\s+'                        # flow type
        r'([\d,]+)$',                                   # quantity (may have commas)
        re.IGNORECASE,
    )

    # Also handle format without time: DD-MM-YYYY <product> <flow> <qty>
    pattern_no_time = re.compile(
        r'^(\d{2}-\d{2}-\d{4})\s+'
        r'(\S+)\s+'
        r'(Ingoing|Outgoing)\s+'
        r'([\d,]+)$',
        re.IGNORECASE,
    )

    rows = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            rows.append({
                '_date': f"{m.group(1)} {m.group(2)}",
                '_product': m.group(3),
                '_flow_type': m.group(4),
                '_quantity': m.group(5).replace(',', ''),
            })
        else:
            m2 = pattern_no_time.match(line)
            if m2:
                rows.append({
                    '_date': m2.group(1),
                    '_product': m2.group(2),
                    '_flow_type': m2.group(3),
                    '_quantity': m2.group(4).replace(',', ''),
                })

    if not rows:
        return None
    return pd.DataFrame(rows)


def load_flow_data(input_path: str) -> pd.DataFrame:
    """
    Load the product flow CSV with flexible column detection.
    
    Supports:
      - Comma / tab / space delimiters
      - "Date & Time" or "Date"
      - "Product ID" or "Product"
      - Comma-formatted quantities ("1,200")
    """
    print(f"  Input: {input_path}")

    # 1. Try standard CSV / TSV first
    raw = Path(input_path).read_text(encoding='utf-8')
    first_line = raw.split('\n')[0]

    df = None
    if ',' in first_line and first_line.count(',') >= 2:
        df = pd.read_csv(input_path)
    elif '\t' in first_line:
        df = pd.read_csv(input_path, sep='\t')

    if df is not None:
        df.columns = [c.strip() for c in df.columns]
        col_map = {}
        for col in df.columns:
            cl = col.lower().strip()
            if cl in ('date & time', 'date', 'datetime', 'date_time'):
                col_map[col] = '_date'
            elif cl in ('product id', 'product', 'product_id', 'produit', 'id_produit'):
                col_map[col] = '_product'
            elif cl in ('flow type', 'flow_type', 'flowtype', 'type'):
                col_map[col] = '_flow_type'
            elif cl in ('quantity', 'quantite', 'qty', 'quantite_demande'):
                col_map[col] = '_quantity'

        df = df.rename(columns=col_map)

        required = ['_product', '_flow_type', '_quantity']
        missing = [c for c in required if c not in df.columns]
        if missing:
            df = None   # fall through to space-separated parser

    # 2. Try space-separated format
    if df is None:
        df = _try_parse_space_separated(input_path)
        if df is None:
            raise ValueError(
                "Could not parse input file. "
                "Expected columns: Date/Date & Time, Product/Product ID, Flow Type, Quantity"
            )

    # Clean quantity
    df['_quantity'] = (
        df['_quantity'].astype(str)
        .str.replace(',', '', regex=False)
        .str.strip()
    )
    df['_quantity'] = pd.to_numeric(df['_quantity'], errors='coerce').fillna(0).astype(int)

    if '_date' in df.columns:
        df['_date_parsed'] = pd.to_datetime(df['_date'], dayfirst=True, errors='coerce')
        df = df.sort_values('_date_parsed').reset_index(drop=True)

    n_in = len(df[df['_flow_type'].str.upper() == 'INGOING'])
    n_out = len(df[df['_flow_type'].str.upper() == 'OUTGOING'])
    print(f"  Operations: {len(df)} total  |  Ingoing: {n_in}  |  Outgoing: {n_out}")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Warehouse Optimization - generate operational instructions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python inference_script.py --input ../data/inputOptimisation.csv --output results.csv
    python inference_script.py --input test.csv --locations ../data/locations_status.csv
        """,
    )
    parser.add_argument('--input', required=True, help='Path to test flow data CSV')
    parser.add_argument('--output', default='optimization_output.csv',
                        help='Output CSV path (default: optimization_output.csv)')
    parser.add_argument('--locations', default=None,
                        help='Path to locations_status.csv (optional)')
    parser.add_argument('--config', default='./model/optimization_config.json',
                        help='Path to config JSON (default: ./model/optimization_config.json)')

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    print("=" * 70)
    print("  WAREHOUSE OPTIMIZATION - INFERENCE")
    print("=" * 70)

    try:
        print("\n[1/3] Loading resources...")
        config = load_config(args.config)
        locations_df = load_locations(args.locations)
        flow_df = load_flow_data(args.input)

        print("\n[2/3] Running optimization...")
        optimizer = WarehouseOptimizer(config=config)
        results = optimizer.optimize(flow_df, locations_df)

        print("\n[3/3] Saving results...")
        output_path = Path(args.output)
        results.to_csv(output_path, index=False)

        stats = optimizer.summary_stats()

        print(f"\n{'=' * 70}")
        print(f"  RESULTS SUMMARY")
        print(f"{'=' * 70}")
        print(f"  Output file     : {output_path}")
        print(f"  Total operations: {len(results)}")
        successful = len(results[
            (results['Location'] != 'N/A') & (results['Location'] != 'NO_SLOT')
        ])
        print(f"  Successful      : {successful} / {len(results)}")
        print(f"  Total distance  : {stats['total_distance_m']:.1f} m")
        print(f"  Reroutes        : {stats['reroutes']}")

        print(f"\n  Chariot utilisation:")
        for ch in stats['chariots']:
            print(f"    {ch['chariot']}: {ch['tasks']} tasks, {ch['distance_m']} m")

        print(f"\n  First 10 operations:")
        print(results.head(10).to_string(index=False))

        print(f"\n{'=' * 70}")
        print("  INFERENCE COMPLETE")
        print(f"{'=' * 70}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

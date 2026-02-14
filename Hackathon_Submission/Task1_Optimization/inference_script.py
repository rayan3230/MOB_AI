#!/usr/bin/env python3
"""
Task 1: Warehouse Optimization - Inference Script
MobAI'26 Hackathon Submission

This script generates optimized warehouse operational instructions for
Ingoing (storage) and Outgoing (picking) flows using multi-factor scoring
and constraint satisfaction algorithms.

Usage:
    python inference_script.py --input test_flows.csv --output operations.csv

Arguments:
    --input: Path to test flow data CSV (required)
    --output: Path for output operations (default: optimization_output.csv)
    --locations: Path to location status CSV (optional)
    --config: Path to optimization config (default: ./model/optimization_config.json)

Input Format:
    Date,Product,Flow Type,Quantity
    15-02-2026,Product X,Ingoing,150
    16-02-2026,Product Y,Outgoing,60

Output Format:
    Product,Action,Location,Route,Reason
    Product X,Storage,0H-01-02,Receipt→H→L1,Optimized score: 0.65
    Product Y,Picking,0G-02-05,G→Expedition,Stock available
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd


@dataclass
class ChariotState:
    """Track chariot status during operations"""
    code: str
    capacity: int
    remaining_capacity: int
    tasks_count: int = 0
    current_corridor: str = "H"


class WarehouseOptimizer:
    """Main optimization engine"""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.palette_size = self.config.get('palette_size', 40)
        self.congestion_threshold = self.config.get('congestion_threshold', 2)
        
        # Initialize state
        self.chariots = self._initialize_chariots()
        self.product_slots = defaultdict(list)
        self.traffic = defaultdict(int)
        self.total_distance = 0.0
        self.reroute_count = 0
    
    def _default_config(self):
        """Default configuration"""
        return {
            'palette_size': 40,
            'congestion_threshold': 2,
            'chariot_fleet': [
                {'code': 'CH-01', 'capacity': 3},
                {'code': 'CH-02', 'capacity': 1},
                {'code': 'CH-03', 'capacity': 1}
            ]
        }
    
    def _initialize_chariots(self):
        """Create chariot fleet"""
        fleet = []
        for ch_config in self.config.get('chariot_fleet', []):
            fleet.append(ChariotState(
                code=ch_config['code'],
                capacity=ch_config['capacity'],
                remaining_capacity=ch_config['capacity']
            ))
        return fleet
    
    def calculate_slot_score(self, corridor, floor, level, frequency_rank=1.0):
        """
        Calculate optimization score for a storage slot.
        Lower score = Better location
        """
        # Distance from expedition (Corridor H)
        corridor_gap = abs(ord(corridor.upper()) - ord('H'))
        dist_score = float(corridor_gap)
        
        # Floor penalty (higher floors are worse)
        floor_penalty = float(floor * 2.5)
        
        # Level penalty (higher shelves are worse)
        level_penalty = float(level * 0.3)
        
        # Frequency weight (fast movers get better spots)
        frequency_weight = float(frequency_rank)
        
        # Final score
        final_score = (dist_score + floor_penalty + level_penalty) * frequency_weight
        
        return {
            'dist_score': dist_score,
            'floor_penalty': floor_penalty,
            'level_penalty': level_penalty,
            'frequency_weight': frequency_weight,
            'final_score': final_score
        }
    
    def select_chariot(self, target_corridor, required_pallets):
        """Select optimal chariot for task"""
        # Filter chariots that can handle the load
        feasible = [ch for ch in self.chariots if ch.capacity >= required_pallets]
        
        if not feasible:
            # Need split load
            max_capacity = max(ch.capacity for ch in self.chariots)
            feasible = [ch for ch in self.chariots if ch.capacity == max_capacity]
            reason = f"Split-load (req:{required_pallets}, max:{max_capacity})"
        else:
            reason = f"Capacity OK ({required_pallets} pallets)"
        
        # Score: prioritize fewer tasks, proximity, larger capacity
        def score(ch):
            corridor_gap = abs(ord(ch.current_corridor) - ord(target_corridor))
            return (ch.tasks_count, corridor_gap, -ch.capacity)
        
        selected = min(feasible, key=score)
        return selected, f"{reason}, {selected.code} (tasks:{selected.tasks_count})"
    
    def resolve_congestion(self, preferred_corridor):
        """Handle corridor congestion"""
        preferred_corridor = preferred_corridor.upper()
        
        if self.traffic[preferred_corridor] < self.congestion_threshold:
            self.traffic[preferred_corridor] += 1
            return preferred_corridor, False
        
        # Find nearby alternative
        nearby = [chr(code) for code in range(ord('A'), ord('Z') + 1)]
        nearby.sort(key=lambda c: abs(ord(c) - ord(preferred_corridor)))
        
        for candidate in nearby:
            if self.traffic[candidate] < self.congestion_threshold:
                self.traffic[candidate] += 1
                return candidate, True
        
        # All congested - use preferred anyway
        self.traffic[preferred_corridor] += 1
        return preferred_corridor, False
    
    def estimate_distance(self, corridor_from, corridor_to):
        """Estimate travel distance in meters"""
        corridor_diff = abs(ord(corridor_from.upper()) - ord(corridor_to.upper()))
        return float(corridor_diff * 3.0 + 12.0)
    
    def process_ingoing(self, product, quantity, available_slots):
        """Process incoming storage operation"""
        required_pallets = max(1, int(np.ceil(quantity / self.palette_size)))
        
        if available_slots.empty:
            return {
                'Product': product,
                'Action': 'Storage',
                'Location': 'NO_SLOT',
                'Route': 'N/A',
                'Reason': 'No available slots'
            }
        
        # Calculate scores for all slots
        freq_rank = 0.5 if 'A' in product else 1.2  # Mock frequency
        
        scores = available_slots.apply(
            lambda r: self.calculate_slot_score(
                r['corridor'],
                int(r['floor']) if str(r['floor']).isdigit() else 0,
                r['level'],
                freq_rank
            )['final_score'],
            axis=1
        )
        
        # Select best slot
        best_idx = scores.idxmin()
        best_slot = available_slots.loc[best_idx]
        best_score = scores[best_idx]
        
        location = best_slot['code_emplacement']
        corridor = best_slot['corridor']
        
        # Track slot usage
        self.product_slots[product].append(location)
        
        # Select chariot
        chariot, chariot_reason = self.select_chariot(corridor, required_pallets)
        
        # Handle congestion
        assigned_corridor, rerouted = self.resolve_congestion(corridor)
        if rerouted:
            self.reroute_count += 1
        
        # Calculate distance
        distance = self.estimate_distance('H', corridor)
        self.total_distance += distance
        
        # Update chariot state
        chariot.tasks_count += 1
        chariot.current_corridor = assigned_corridor
        
        # Build route
        route = f"Receipt→{assigned_corridor}→{location}"
        reason = f"Optimized score:{best_score:.2f}, {chariot_reason}"
        
        return {
            'Product': product,
            'Action': 'Storage',
            'Location': location,
            'Route': route,
            'Reason': reason
        }, best_idx
    
    def process_outgoing(self, product, quantity):
        """Process outgoing picking operation"""
        required_pallets = max(1, int(np.ceil(quantity / self.palette_size)))
        
        if not self.product_slots[product]:
            return {
                'Product': product,
                'Action': 'Picking',
                'Location': 'N/A',
                'Route': 'N/A',
                'Reason': 'No stock available (violated chronology)'
            }
        
        # Get stored location
        source = self.product_slots[product].pop(0)
        corridor = source[1] if len(source) > 1 else 'H'
        
        # Select chariot
        chariot, chariot_reason = self.select_chariot(corridor, required_pallets)
        
        # Handle congestion
        assigned_corridor, rerouted = self.resolve_congestion(corridor)
        if rerouted:
            self.reroute_count += 1
        
        # Calculate distance
        distance = self.estimate_distance(corridor, 'H')
        self.total_distance += distance
        
        # Update chariot state
        chariot.tasks_count += 1
        chariot.current_corridor = assigned_corridor
        
        # Build route
        route = f"{source}→{assigned_corridor}→Expedition"
        reason = f"Stock available, {chariot_reason}"
        
        return {
            'Product': product,
            'Action': 'Picking',
            'Location': source,
            'Route': route,
            'Reason': reason
        }
    
    def optimize(self, flow_df, locations_df):
        """Run complete optimization"""
        # Filter available slots
        available = locations_df[~locations_df['actif']].copy()
        
        operations = []
        
        for _, row in flow_df.iterrows():
            product = str(row['Product']).strip()
            flow_type = str(row['Flow Type']).strip().upper()
            quantity = int(row['Quantity'])
            
            if flow_type == 'INGOING':
                result, used_idx = self.process_ingoing(product, quantity, available)
                operations.append(result)
                # Remove used slot
                if used_idx is not None and not available.empty:
                    available = available.drop(index=used_idx)
                    
            elif flow_type == 'OUTGOING':
                result = self.process_outgoing(product, quantity)
                operations.append(result)
        
        return pd.DataFrame(operations)


def load_config(config_path):
    """Load optimization configuration"""
    import json
    
    if Path(config_path).exists():
        print(f"Loading config from: {config_path}")
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        print("Using default configuration")
        return None


def load_locations(locations_path):
    """Load location status data"""
    if locations_path and Path(locations_path).exists():
        print(f"Loading locations from: {locations_path}")
        df = pd.read_csv(locations_path)
    else:
        # Create default locations
        print("Generating default location grid...")
        locations = []
        for floor in ['0', '1']:
            for corridor in 'ABCDEFGHIJKLMN':
                for level in range(1, 11):
                    locations.append({
                        'code_emplacement': f"{floor}{corridor}-{level:02d}",
                        'actif': np.random.random() > 0.7  # 70% available
                    })
        df = pd.DataFrame(locations)
    
    # Parse location codes
    df['actif'] = df['actif'].astype(str).str.upper() == 'TRUE'
    df['floor'] = df['code_emplacement'].astype(str).str[0]
    df['corridor'] = df['code_emplacement'].astype(str).str[1]
    df['level'] = pd.to_numeric(
        df['code_emplacement'].astype(str).str[-2:], 
        errors='coerce'
    ).fillna(1)
    
    print(f"  Loaded {len(df)} locations")
    print(f"  Available: {len(df[~df['actif']])}")
    print(f"  Occupied: {len(df[df['actif']])}")
    
    return df


def load_flow_data(input_path):
    """Load test flow data"""
    print(f"Loading flow data from: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required = ['Product', 'Flow Type', 'Quantity']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    print(f"  Loaded {len(df)} operations")
    print(f"  Ingoing: {len(df[df['Flow Type'].str.upper() == 'INGOING'])}")
    print(f"  Outgoing: {len(df[df['Flow Type'].str.upper() == 'OUTGOING'])}")
    
    return df


def main():
    """Main inference pipeline"""
    parser = argparse.ArgumentParser(
        description='Generate optimized warehouse operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python inference_script.py --input test_flows.csv --output operations.csv

Output format:
    Product,Action,Location,Route,Reason
    Product A,Storage,0H-01-02,Receipt→H→L1,Optimized score:0.65
    Product B,Picking,0G-02-05,G→Expedition,Stock available
        """
    )
    
    parser.add_argument('--input', required=True,
                        help='Path to test flow data CSV')
    parser.add_argument('--output', default='optimization_output.csv',
                        help='Path for output operations (default: optimization_output.csv)')
    parser.add_argument('--locations', default=None,
                        help='Path to location status CSV (optional)')
    parser.add_argument('--config', default='./model/optimization_config.json',
                        help='Path to config file (default: ./model/optimization_config.json)')
    
    args = parser.parse_args()
    
    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)
    
    print("="*70)
    print("WAREHOUSE OPTIMIZATION - INFERENCE")
    print("="*70)
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Load locations
        locations_df = load_locations(args.locations)
        
        # Load flow data
        flow_df = load_flow_data(input_path)
        
        # Run optimization
        print("\nRunning optimization...")
        optimizer = WarehouseOptimizer(config=config)
        results = optimizer.optimize(flow_df, locations_df)
        
        # Save output
        output_path = Path(args.output)
        results.to_csv(output_path, index=False)
        
        print(f"\n✓ Operations saved to: {output_path}")
        print(f"  Total operations: {len(results)}")
        print(f"  Successful: {len(results[results['Location'] != 'N/A'])}")
        print(f"  Total distance: {optimizer.total_distance:.2f}m")
        print(f"  Reroutes: {optimizer.reroute_count}")
        
        # Show sample
        print("\nSample operations (first 10 rows):")
        print(results.head(10).to_string(index=False))
        
        print("\n" + "="*70)
        print("INFERENCE COMPLETE ✓")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR during inference: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from ..engine.base import StorageClass

class ProductStorageManager:
    def __init__(self, products_csv: str, demand_csv: str):
        self.products_path = products_csv
        self.demand_path = demand_csv
        self.products_df = pd.DataFrame()
        self.demand_df = pd.DataFrame()
        self.product_scores: Dict[int, str] = {} # id_produit -> StorageClass
        
        self.load_data()
        self.calculate_product_classes()

    def load_data(self):
        try:
            self.products_df = pd.read_csv(self.products_path)
            self.products_df.columns = self.products_df.columns.str.strip()
            self.demand_df = pd.read_csv(self.demand_path)
            self.demand_df.columns = self.demand_df.columns.str.strip()
        except Exception as e:
            print(f"Error loading CSV data: {e}")

    def calculate_product_classes(self):
        """
        Classifies products into FAST, MEDIUM, SLOW based on demand frequency.
        """
        if self.demand_df.empty:
            return

        # Calculate demand frequency (number of times ordered in the history)
        demand_freq = self.demand_df.groupby('id_produit').size().reset_index(name='frequency')
        
        # Merge with products to get all IDs
        full_products = self.products_df[['id_produit', 'sku']].merge(demand_freq, on='id_produit', how='left').fillna(0)
        
        # Determine thresholds for ABC classification (Zoning)
        # Fast: top 10% by frequency
        # Medium: next 30%
        # Slow: remaining 60%
        
        quantiles = full_products['frequency'].quantile([0.6, 0.9])
        slow_thresh = quantiles[0.6]
        medium_thresh = quantiles[0.9]
        
        for _, row in full_products.iterrows():
            pid = int(row['id_produit'])
            freq = row['frequency']
            
            if freq >= medium_thresh:
                p_class = StorageClass.FAST
            elif freq >= slow_thresh:
                p_class = StorageClass.MEDIUM
            else:
                p_class = StorageClass.SLOW
                
            self.product_scores[pid] = p_class

    def get_product_class(self, product_id: int) -> StorageClass:
        return self.product_scores.get(product_id, StorageClass.SLOW)

    def is_hazardous(self, product_id: int) -> bool:
        """Determines if a product is hazardous based on category or name."""
        details = self.get_product_details(product_id)
        category = str(details.get('categorie', '')).upper()
        # Heuristic: Categories like CHIMIE, PEINTURE, or items containing 'DANG'
        return any(k in category for k in ["CHIMIE", "PEINTURE", "DANG"])

    def is_fragile(self, product_id: int) -> bool:
        """Determines if a product is fragile based on name or SKU."""
        details = self.get_product_details(product_id)
        name = str(details.get('nom_produit', '')).upper()
        # Heuristic: Items containing 'VERRE', 'MIROIR', 'CERAM'
        return any(k in name for k in ["VERRE", "MIROIR", "CERAM"])

    def get_product_details(self, product_id: int) -> Dict:
        prod = self.products_df[self.products_df['id_produit'] == product_id]
        if prod.empty:
            return {}
        details = prod.iloc[0].to_dict()
        
        # REQ 8.2: If weight (poidsu) is missing, apply a category-based heuristic
        if 'poidsu' not in details or pd.isna(details['poidsu']):
            category = str(details.get('categorie', '')).upper()
            # Heuristic weights in KG
            if any(k in category for k in ["TABLEAU", "DISJONCTEUR", "METALIC"]):
                details['poidsu'] = 18.5 # "Heavy"
            elif any(k in category for k in ["TUBE", "MOULURE", "ACCESSOIRES"]):
                details['poidsu'] = 2.0  # "Light"
            else:
                details['poidsu'] = 5.0  # "Medium"
                
        return details

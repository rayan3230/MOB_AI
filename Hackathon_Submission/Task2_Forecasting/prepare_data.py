
import pandas as pd
from datetime import datetime
import os

def prepare_full_history():
    print("Preparing full demand history...")
    
    # 1. Load existing history
    history_path = 'backend/folder_data/csv_cleaned/historique_demande.csv'
    history_df = pd.read_csv(history_path)
    history_df['date'] = pd.to_datetime(history_df['date'])
    print(f"  Existing history: {len(history_df)} rows, up to {history_df['date'].max()}")

    # 2. Load prediction transaction headers
    # The file has some junk in first 2 rows based on previous reads
    headers_path = 'Hackathon_Submission/data/predectiondata.csv'
    headers_df = pd.read_csv(headers_path, skiprows=2)
    headers_df.columns = ['id_transaction', 'type_transaction', 'reference_transaction', 'cree_le', 'cree_par', 'statut', 'notes']
    
    # Filter for deliveries
    deliveries = headers_df[headers_df['type_transaction'] == 'DELIVERY'].copy()
    deliveries['cree_le'] = pd.to_datetime(deliveries['cree_le'], errors='coerce')
    print(f"  New deliveries found: {len(deliveries)}")

    # 3. Load transaction lines
    lines_path = 'backend/folder_data/csv_cleaned/lignes_transaction.csv'
    # Based on previous check, it has mixed types and no header
    lines_df = pd.read_csv(lines_path, header=None, low_memory=False)
    lines_df.columns = ['id_transaction', 'line_id', 'id_produit', 'quantite_demande', 'c4', 'c5', 'c6', 'c7']

    # 4. Join
    new_demand = pd.merge(deliveries[['id_transaction', 'cree_le']], lines_df[['id_transaction', 'id_produit', 'quantite_demande']], on='id_transaction')
    new_demand = new_demand.rename(columns={'cree_le': 'date'})
    
    # Clean new demand
    new_demand = new_demand.dropna(subset=['date', 'id_produit', 'quantite_demande'])
    new_demand['id_produit'] = new_demand['id_produit'].astype(str)
    new_demand['quantite_demande'] = pd.to_numeric(new_demand['quantite_demande'], errors='coerce')
    
    print(f"  Extracted demand lines: {len(new_demand)}")

    # 5. Concatenate and deduplicate
    full_history = pd.concat([history_df, new_demand[['date', 'id_produit', 'quantite_demande']]])
    
    # Deduplicate by day, SKU
    full_history['date_only'] = full_history['date'].dt.normalize()
    full_history = full_history.groupby(['date_only', 'id_produit'], as_index=False)['quantite_demande'].sum()
    full_history = full_history.rename(columns={'date_only': 'date'})
    full_history = full_history.sort_values(['date', 'id_produit'])

    print(f"  Final consolidated history: {len(full_history)} rows, up to {full_history['date'].max()}")
    
    output_path = 'Hackathon_Submission/data/consolidated_history.csv'
    full_history.to_csv(output_path, index=False)
    print(f"  Saved to: {output_path}")

if __name__ == "__main__":
    prepare_full_history()

"""
Visualization data preparation for map visualization.
Generates VIZ_DATA in the format expected by map_visualization.html
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
CSV_DIR = SCRIPT_DIR.parent / "csvs"
OUTPUT_FILE = SCRIPT_DIR / "viz_data.js"

# Manual Coordinates [Lat, Lon] - Matching countries.csv
LOCATION_COORDS = {
    'Ukraine': [48.3794, 31.1656],
    'Austria': [47.5162, 14.5501],
    'Denmark': [56.2639, 9.5018],
    'France': [46.2276, 2.2137],
    'Germany': [51.1657, 10.4515],
    'Hungary': [47.1625, 19.5033],
    'Hungry': [47.1625, 19.5033],  # Alias for typo
    'Moldova': [47.4116, 28.3699],
    'Belgium': [50.5039, 4.4699],
    'Poland': [51.9194, 19.1451],
    'Switzerland': [46.8182, 8.2275],
    'Romania': [45.9432, 24.9668],
    'Slovakia': [48.6690, 19.6990],
    'UnitedStates': [37.0902, -95.7129],
    'UnitedState': [37.0902, -95.7129]  # Alias
}

# Item name mapping - p1, p2, p3, s1, s2 format
NAME_MAPPING = {
    'food_clothing': 'p1',
    'nonfood_items_clothing': 'p2',
    'housing': 'p3',
    'medical': 's1',
    'info_legal': 's2'
}


def clean_value(val):
    """Zero out small numbers and round properly."""
    if pd.isna(val):
        return 0
    try:
        f = float(val)
        if abs(f) < 0.01:
            return 0
        return round(f, 2)
    except:
        return 0


def get_item_name(item):
    """Return mapped item name (p1, p2, p3, s1, s2)."""
    return NAME_MAPPING.get(item, item)


def load_data():
    """Load all required CSVs."""
    csv_files = {
        'shipments': 'x_Shipment.csv',
        'inventory': 'Inv_Inventory.csv',
        'staff': 'staff_Deployment.csv',
        'product_fulfilled': 'product_fulfilled.csv',
        'service_delivered': 'service_delivered.csv',
        'backlog_prod': 'backlog_prod.csv',
        'backlog_serv': 'backlog_serv.csv',
        'expired': 'Exp_ExpiredDemand.csv',
        'relocation': 'reloc_StaffRelocation.csv'
    }
    
    dfs = {}
    print("Loading CSVs...")
    for key, filename in csv_files.items():
        filepath = CSV_DIR / filename
        if filepath.exists():
            dfs[key] = pd.read_csv(filepath)
            print(f"  Loaded {filename}: {len(dfs[key])} records")
    
    return dfs


def process_data(dfs):
    """Process loaded data into VIZ_DATA format."""
    # Get all time periods
    all_t = set()
    for df in dfs.values():
        if 't' in df.columns:
            all_t.update(df['t'].unique())
    
    time_periods = sorted([f"T{int(t)}" if str(t).isdigit() else str(t) for t in all_t], 
                         key=lambda x: int(x[1:]) if x.startswith('T') and x[1:].isdigit() else 0)
    print(f"Time periods: {len(time_periods)}")
    
    # Build locations dict
    all_locations = set()
    for df in dfs.values():
        if 'i' in df.columns:
            all_locations.update(df['i'].unique())
        if 'j' in df.columns:
            all_locations.update(df['j'].unique())
    
    locations = {}
    for loc in all_locations:
        if loc in LOCATION_COORDS:
            locations[loc] = LOCATION_COORDS[loc]
        else:
            locations[loc] = [0, 0]
    print(f"Locations: {len(locations)}")
    
    # Build frames - one per time period
    frames = {}
    
    # Calculate cumulative expired demand
    cumulative_expired = 0
    
    for t_str in time_periods:
        t_num = int(t_str[1:]) if t_str.startswith('T') else t_str
        
        frame = {
            'nodes': {},
            'flows': [],
            'cumulative_expired': 0
        }
        
        # Initialize nodes for this frame
        for loc in locations.keys():
            frame['nodes'][loc] = {
                'products_delivered': {},
                'products_unmet': {},
                'services_delivered': {},
                'services_unmet': {},
                'inventory': {},
                'staff': {}
            }
        
        # Process expired demand (cumulative)
        if 'expired' in dfs:
            expired_t = dfs['expired'][dfs['expired']['t'] == t_num]
            period_expired = expired_t['level'].sum() if 'level' in expired_t.columns else 0
            cumulative_expired += clean_value(period_expired)
        frame['cumulative_expired'] = cumulative_expired
        
        # Process product fulfillment
        if 'product_fulfilled' in dfs:
            df = dfs['product_fulfilled']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                loc = row['i']
                if loc in frame['nodes']:
                    item = get_item_name(row['p'])
                    age = row.get('a', 1)
                    val = clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item}" if age == 1 else f"{item} - age{age}"
                        frame['nodes'][loc]['products_delivered'][key] = \
                            frame['nodes'][loc]['products_delivered'].get(key, 0) + val
        
        # Process service delivery
        if 'service_delivered' in dfs:
            df = dfs['service_delivered']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                loc = row['i']
                if loc in frame['nodes']:
                    item = get_item_name(row['s'])
                    age = row.get('a', 1)
                    val = clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item}" if age == 1 else f"{item} - age{age}"
                        frame['nodes'][loc]['services_delivered'][key] = \
                            frame['nodes'][loc]['services_delivered'].get(key, 0) + val
        
        # Process product backlogs (unmet demand)
        if 'backlog_prod' in dfs:
            df = dfs['backlog_prod']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                loc = row['i']
                if loc in frame['nodes']:
                    item = get_item_name(row['p'])
                    age = row.get('a', 1)
                    val = clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item} - age{age}"
                        frame['nodes'][loc]['products_unmet'][key] = val
        
        # Process service backlogs (unmet demand)
        if 'backlog_serv' in dfs:
            df = dfs['backlog_serv']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                loc = row['i']
                if loc in frame['nodes']:
                    item = get_item_name(row['s'])
                    age = row.get('a', 1)
                    val = clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item} - age{age}"
                        frame['nodes'][loc]['services_unmet'][key] = val
        
        # Process inventory
        if 'inventory' in dfs:
            df = dfs['inventory']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                loc = row['i']
                if loc in frame['nodes']:
                    item = get_item_name(row['p'])
                    val = clean_value(row.get('level', 0))
                    if val > 0:
                        frame['nodes'][loc]['inventory'][item] = val
        
        # Process staff
        if 'staff' in dfs:
            df = dfs['staff']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                loc = row['i']
                if loc in frame['nodes']:
                    item = get_item_name(row['s'])
                    val = clean_value(row.get('level', 0))
                    if val > 0:
                        frame['nodes'][loc]['staff'][item] = val
        
        # Process shipment flows (products)
        if 'shipments' in dfs:
            df = dfs['shipments']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                val = clean_value(row.get('level', 0))
                if val > 0:
                    frame['flows'].append({
                        'from': row['i'],
                        'to': row['j'],
                        'item': get_item_name(row['p']),
                        'type': 'product',
                        'qty': val
                    })
        
        # Process staff relocation flows
        if 'relocation' in dfs:
            df = dfs['relocation']
            df_t = df[df['t'] == t_num]
            for _, row in df_t.iterrows():
                val = clean_value(row.get('level', 0))
                if val > 0:
                    frame['flows'].append({
                        'from': row['i'],
                        'to': row['j'],
                        'item': get_item_name(row['s']),
                        'type': 'staff',
                        'qty': val
                    })
        
        # Remove empty nodes (only keep active locations)
        frame['nodes'] = {k: v for k, v in frame['nodes'].items() 
                        if any(v[cat] for cat in v)}
        
        frames[t_str] = frame
    
    print(f"Frames: {len(frames)}")
    total_flows = sum(len(f['flows']) for f in frames.values())
    print(f"Total flows: {total_flows}")
    
    return {
        'time_periods': time_periods,
        'locations': locations,
        'frames': frames
    }


def convert_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(i) for i in obj]
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def save_js(data):
    """Save data as JavaScript file."""
    serializable_data = convert_types(data)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write("// Auto-generated visualization data\n")
        f.write(f"const VIZ_DATA = {json.dumps(serializable_data, indent=2)};\n")
    
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    print("="*60)
    print("Preparing visualization data...")
    print("="*60)
    dfs = load_data()
    viz_data = process_data(dfs)
    save_js(viz_data)
    print("="*60)
    print("Done! Open map_visualization.html in a browser.")
    print("="*60)

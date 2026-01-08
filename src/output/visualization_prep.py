
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, List

from ..core.base_component import BaseComponent

LOCATION_COORDS = {
    'Ukraine': [48.3794, 31.1656],
    'Austria': [47.5162, 14.5501],
    'Denmark': [56.2639, 9.5018],
    'France': [46.2276, 2.2137],
    'Germany': [51.1657, 10.4515],
    'Hungary': [47.1625, 19.5033],
    'Hungry': [47.1625, 19.5033],
    'Moldova': [47.4116, 28.3699],
    'Belgium': [50.5039, 4.4699],
    'Poland': [51.9194, 19.1451],
    'Switzerland': [46.8182, 8.2275],
    'Romania': [45.9432, 24.9668],
    'Slovakia': [48.6690, 19.6990],
    'UnitedStates': [37.0902, -95.7129],
    'UnitedState': [37.0902, -95.7129]
}

NAME_MAPPING = {
    'food_clothing': 'p1',
    'nonfood_items_clothing': 'p2',
    'housing': 'p3',
    'medical': 's1',
    'info_legal': 's2'
}

class VisualizationPrep(BaseComponent):
    
    def __init__(self, config: Dict[str, Any], csv_dir: Path, output_dir: Path):
        super().__init__(config)
        self.csv_dir = Path(csv_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_visualization_data(self) -> None:
        self.log_info("Preparing visualization data...")
        
        dfs = self._load_data()
        
        viz_data = self._process_data(dfs)
        self._save_js(viz_data)
        
        self.log_info(f"  Visualization data saved to {self.output_dir}")
    
    def _load_data(self) -> Dict[str, pd.DataFrame]:
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
        for key, filename in csv_files.items():
            filepath = self.csv_dir / filename
            if filepath.exists():
                dfs[key] = pd.read_csv(filepath)
                self.log_info(f"    Loaded {filename}")
        
        return dfs
    
    def _clean_value(self, val) -> float:
        if pd.isna(val):
            return 0
        try:
            f = float(val)
            if abs(f) < 0.01:
                return 0
            return round(f, 2)
        except:
            return 0
    
    def _get_item_name(self, item: str) -> str:
        return NAME_MAPPING.get(item, item)
    
    def _process_data(self, dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        all_t = set()
        for df in dfs.values():
            if 't' in df.columns:
                all_t.update(df['t'].unique())
        
        time_periods = []
        for t in sorted(all_t, key=lambda x: int(x) if isinstance(x, (int, np.integer)) or (isinstance(x, str) and x.isdigit()) else 0):
            t_int = int(t) if isinstance(t, (int, np.integer)) or (isinstance(t, str) and str(t).isdigit()) else t
            time_periods.append(f"T{t_int}")
        
        all_locations = set()
        for df in dfs.values():
            if 'i' in df.columns:
                all_locations.update(df['i'].unique())
            if 'j' in df.columns:
                all_locations.update(df['j'].unique())
        
        locations = {}
        for loc in all_locations:
            if loc in LOCATION_COORDS:
                locations[str(loc)] = LOCATION_COORDS[loc]
            else:
                locations[str(loc)] = [0, 0]
        
        frames = {}
        cumulative_expired = 0.0
        
        for t_str in time_periods:
            t_num = int(t_str[1:]) if t_str.startswith('T') else t_str
            
            frame = {
                'nodes': {},
                'flows': [],
                'cumulative_expired': 0.0
            }
            
            if 'expired' in dfs:
                expired_t = dfs['expired'][dfs['expired']['t'] == t_num]
                period_expired = expired_t['level'].sum() if 'level' in expired_t.columns else 0
                cumulative_expired += self._clean_value(period_expired)
            frame['cumulative_expired'] = cumulative_expired
            
            node_data = {}
            
            if 'product_fulfilled' in dfs:
                df = dfs['product_fulfilled']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    loc = str(row['i'])
                    if loc not in node_data:
                        node_data[loc] = {'products_delivered': {}, 'products_unmet': {}, 
                                         'services_delivered': {}, 'services_unmet': {},
                                         'inventory': {}, 'staff': {}}
                    item = self._get_item_name(row['p'])
                    age = int(row.get('a', 1))
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item}" if age == 1 else f"{item} - age{age}"
                        node_data[loc]['products_delivered'][key] = \
                            node_data[loc]['products_delivered'].get(key, 0) + val
            
            if 'service_delivered' in dfs:
                df = dfs['service_delivered']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    loc = str(row['i'])
                    if loc not in node_data:
                        node_data[loc] = {'products_delivered': {}, 'products_unmet': {}, 
                                         'services_delivered': {}, 'services_unmet': {},
                                         'inventory': {}, 'staff': {}}
                    item = self._get_item_name(row['s'])
                    age = int(row.get('a', 1))
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item}" if age == 1 else f"{item} - age{age}"
                        node_data[loc]['services_delivered'][key] = \
                            node_data[loc]['services_delivered'].get(key, 0) + val
            
            if 'backlog_prod' in dfs:
                df = dfs['backlog_prod']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    loc = str(row['i'])
                    if loc not in node_data:
                        node_data[loc] = {'products_delivered': {}, 'products_unmet': {}, 
                                         'services_delivered': {}, 'services_unmet': {},
                                         'inventory': {}, 'staff': {}}
                    item = self._get_item_name(row['p'])
                    age = int(row.get('a', 1))
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item} - age{age}"
                        node_data[loc]['products_unmet'][key] = val
            
            if 'backlog_serv' in dfs:
                df = dfs['backlog_serv']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    loc = str(row['i'])
                    if loc not in node_data:
                        node_data[loc] = {'products_delivered': {}, 'products_unmet': {}, 
                                         'services_delivered': {}, 'services_unmet': {},
                                         'inventory': {}, 'staff': {}}
                    item = self._get_item_name(row['s'])
                    age = int(row.get('a', 1))
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        key = f"{item} - age{age}"
                        node_data[loc]['services_unmet'][key] = val
            
            if 'inventory' in dfs:
                df = dfs['inventory']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    loc = str(row['i'])
                    if loc not in node_data:
                        node_data[loc] = {'products_delivered': {}, 'products_unmet': {}, 
                                         'services_delivered': {}, 'services_unmet': {},
                                         'inventory': {}, 'staff': {}}
                    item = self._get_item_name(row['p'])
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        node_data[loc]['inventory'][item] = val
            
            if 'staff' in dfs:
                df = dfs['staff']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    loc = str(row['i'])
                    if loc not in node_data:
                        node_data[loc] = {'products_delivered': {}, 'products_unmet': {}, 
                                         'services_delivered': {}, 'services_unmet': {},
                                         'inventory': {}, 'staff': {}}
                    item = self._get_item_name(row['s'])
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        node_data[loc]['staff'][item] = val
            
            frame['nodes'] = {k: v for k, v in node_data.items() if any(v[cat] for cat in v)}
            
            if 'shipments' in dfs:
                df = dfs['shipments']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        frame['flows'].append({
                            'from': str(row['i']),
                            'to': str(row['j']),
                            'item': self._get_item_name(row['p']),
                            'type': 'product',
                            'qty': val
                        })
            
            if 'relocation' in dfs:
                df = dfs['relocation']
                df_t = df[df['t'] == t_num]
                for _, row in df_t.iterrows():
                    val = self._clean_value(row.get('level', 0))
                    if val > 0:
                        frame['flows'].append({
                            'from': str(row['i']),
                            'to': str(row['j']),
                            'item': self._get_item_name(row['s']),
                            'type': 'staff',
                            'qty': val
                        })
            
            frames[t_str] = frame
        
        return {
            'time_periods': time_periods,
            'locations': locations,
            'frames': frames
        }
    
    def _convert_types(self, obj):
        if isinstance(obj, dict):
            return {str(k): self._convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_types(i) for i in obj]
        elif isinstance(obj, (np.int64, np.int32, np.integer)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    def _save_js(self, data: Dict[str, Any]) -> None:
        output_file = self.output_dir / "viz_data.js"
        
        serializable_data = self._convert_types(data)
        
        with open(output_file, 'w') as f:
            f.write("// Auto-generated visualization data\n")
            f.write(f"const VIZ_DATA = {json.dumps(serializable_data, indent=2)};\n")
        
        total_flows = sum(len(f.get('flows', [])) for f in data.get('frames', {}).values())
        self.log_info(f"    Saved viz_data.js ({total_flows} flows, {len(data.get('locations', {}))} locations)")

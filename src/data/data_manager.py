
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any

from ..core.base_component import BaseComponent
from ..core.constants import RISK_LEVELS
from .validators import DataValidator

class DataManager(BaseComponent):
    
    def __init__(self, config: Dict[str, Any], input_dir: Path):
        super().__init__(config)
        self.input_dir = Path(input_dir)
        self.validator = DataValidator()
        
        self.demand_df: pd.DataFrame = None
        self.locations: List[str] = []
        self.time_periods: List[int] = []
        self.products: List[str] = []
        self.services: List[str] = []
        
    def load_all_data(self) -> None:
        self.log_info("Loading all input data...")
        
        self.demand_df = self.load_demand_data()
        self._extract_sets_from_demand()
        
        self.log_info(f"  Sets: {len(self.locations)} locations, "
                     f"{len(self.time_periods)} periods, "
                     f"{len(self.products)} products, "
                     f"{len(self.services)} services")
    
    def load_demand_data(self) -> pd.DataFrame:
        demand_file = self.input_dir / self.get_config_value('data_files', 'demand')
        self.log_info(f"  Loading demand from {demand_file.name}...")
        
        df = pd.read_csv(demand_file)
        
        self.validator.validate_required_columns(
            df, ['Location', 't'], 'Demand data'
        )
        
        return df
    
    def _extract_sets_from_demand(self) -> None:
        self.locations = sorted(self.demand_df['Location'].unique().tolist())
        self.time_periods = sorted(self.demand_df['t'].unique().tolist())
        
        demand_columns = self.demand_df.columns.tolist()
        
        products_set = set()
        services_set = set()
        
        for col in demand_columns:
            if col in ['t', 'Location', 'month']:
                continue
            
            if col.startswith('product_'):
                parts = col.split('_')
                item_name = '_'.join(parts[1:-1])
                products_set.add(item_name)
            elif col.startswith('service_'):
                parts = col.split('_')
                item_name = '_'.join(parts[1:-1])
                services_set.add(item_name)
        
        self.products = sorted(list(products_set))
        self.services = sorted(list(services_set))
    
    def load_network_data(self) -> Dict[str, pd.DataFrame]:
        location_mapping = self.get_config_value('location_mapping', default={})
        
        aij_file = self.input_dir / self.get_config_value('data_files', 'shipment_feasibility')
        aij_df = pd.read_csv(aij_file)
        aij_df['i'] = aij_df['i'].replace(location_mapping)
        aij_df['j'] = aij_df['j'].replace(location_mapping)
        aij_df = aij_df[(aij_df['i'].isin(self.locations)) & 
                        (aij_df['j'].isin(self.locations))]
        
        dist_file = self.input_dir / self.get_config_value('data_files', 'distance_matrix')
        dist_df = pd.read_csv(dist_file)
        dist_df['i'] = dist_df['i'].replace(location_mapping)
        dist_df['j'] = dist_df['j'].replace(location_mapping)
        dist_df = dist_df[(dist_df['i'].isin(self.locations)) & 
                         (dist_df['j'].isin(self.locations))]
        
        self.log_info(f"  Loaded network data: {len(aij_df)} arcs, {len(dist_df)} distances")
        
        return {
            'aij': aij_df,
            'distances': dist_df
        }
    
    def load_initial_conditions(self) -> Dict[str, Any]:
        initial_data = {}
        
        try:
            inv_file = self.input_dir / 'initial_inventory.csv'
            inv_df = pd.read_csv(inv_file)
            initial_data['inventory'] = inv_df
            self.log_info(f"  Loaded initial inventory: {len(inv_df)} records")
        except FileNotFoundError:
            self.log_warning("  Initial inventory file not found, using zeros")
            initial_data['inventory'] = None
        
        try:
            allow_file = self.input_dir / 'procurement_allowance.csv'
            allow_df = pd.read_csv(allow_file)
            initial_data['procurement_allowance'] = allow_df
            self.log_info(f"  Loaded procurement allowance: {len(allow_df)} records")
        except FileNotFoundError:
            self.log_warning("  Procurement allowance file not found, using origin only")
            initial_data['procurement_allowance'] = None
        
        return initial_data
    
    def get_sets(self) -> Dict[str, List]:
        return {
            'locations': self.locations,
            'time_periods': self.time_periods,
            'products': self.products,
            'services': self.services,
            'risk_levels': RISK_LEVELS,
            'backlog_ages': [1, 2, 3]
        }

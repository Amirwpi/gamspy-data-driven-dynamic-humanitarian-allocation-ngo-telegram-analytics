
import pandas as pd
from pathlib import Path
from typing import Dict

from ..core.base_component import BaseComponent

class CSVWriter(BaseComponent):
    
    def save_variable_csvs(self, solution_data: Dict[str, pd.DataFrame], 
                          output_dir: Path) -> None:
        self.log_info("Saving CSV files...")
        
        csv_dir = Path(output_dir) / "csvs"
        csv_dir.mkdir(exist_ok=True, parents=True)
        
        var_mapping = {
            'x': 'x_Shipment.csv',
            'y': 'y_Procurement.csv',
            'Inv': 'Inv_Inventory.csv',
            'reloc': 'reloc_StaffRelocation.csv',
            'staff': 'staff_Deployment.csv',
            'product_fulfilled': 'product_fulfilled.csv',
            'service_delivered': 'service_delivered.csv',
            'backlog_prod': 'backlog_prod.csv',
            'backlog_serv': 'backlog_serv.csv',
            'Exp': 'Exp_ExpiredDemand.csv',
            'theta': 'theta_Fairness.csv'
        }
        
        saved_count = 0
        for var_name, filename in var_mapping.items():
            if var_name in solution_data and not solution_data[var_name].empty:
                csv_path = csv_dir / filename
                solution_data[var_name].to_csv(csv_path, index=False)
                self.log_info(f"  + {filename} ({len(solution_data[var_name])} records)")
                saved_count += 1
            else:
                self.log_info(f"  - {filename} (empty)")
        
        self.log_info(f"  Saved {saved_count} CSV files to {csv_dir}")

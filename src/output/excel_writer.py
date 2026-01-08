
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from ..core.base_component import BaseComponent

class ExcelWriter(BaseComponent):
    
    def save_excel_report(self, solution_data: Dict[str, pd.DataFrame],
                         breakdown: Dict[str, float],
                         stats: Dict[str, Any],
                         output_path: Path) -> None:
        self.log_info(f"Saving Excel report to {output_path.name}...")
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                self._write_summary_sheet(writer, breakdown, stats)
                
                var_order = [
                    'theta', 'x', 'y', 'Inv', 'staff', 'reloc',
                    'product_fulfilled', 'service_delivered',
                    'backlog_prod', 'backlog_serv', 'Exp'
                ]
                
                for var_name in var_order:
                    if var_name in solution_data and not solution_data[var_name].empty:
                        df = solution_data[var_name]
                        sheet_name = var_name[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            self.log_info(f"  Excel report saved successfully")
        
        except Exception as e:
            self.log_error(f"Error saving Excel: {e}")
    
    def _write_summary_sheet(self, writer, breakdown: Dict, stats: Dict) -> None:
        summary_data = []
        
        summary_data.append(['SOLUTION STATUS', ''])
        summary_data.append(['Status', stats.get('status', 'N/A')])
        summary_data.append(['Solve Status', stats.get('solve_status', 'N/A')])
        summary_data.append(['', ''])
        
        summary_data.append(['OBJECTIVES', ''])
        summary_data.append(['Total Cost', f"${breakdown.get('total', 0):,.2f}"])
        summary_data.append(['Fairness (ThetaStar)', f"{stats.get('theta_star', 0):.6f}"])
        summary_data.append(['', ''])
        
        summary_data.append(['COST BREAKDOWN', ''])
        summary_data.append(['Shipment Cost', f"${breakdown.get('shipment', 0):,.2f}"])
        summary_data.append(['Procurement Cost', f"${breakdown.get('procurement', 0):,.2f}"])
        summary_data.append(['Holding Cost', f"${breakdown.get('holding', 0):,.2f}"])
        summary_data.append(['Wage Cost', f"${breakdown.get('wages', 0):,.2f}"])
        summary_data.append(['Relocation Cost', f"${breakdown.get('relocation', 0):,.2f}"])
        summary_data.append(['Backlog Penalty', f"${breakdown.get('backlog', 0):,.2f}"])
        summary_data.append(['Late Service Cost', f"${breakdown.get('late', 0):,.2f}"])
        
        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

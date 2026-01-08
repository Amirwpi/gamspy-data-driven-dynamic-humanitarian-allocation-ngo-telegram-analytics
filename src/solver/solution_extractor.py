
import pandas as pd
from typing import Dict, Any
from gamspy import Variable

from ..core.base_component import BaseComponent

class SolutionExtractor(BaseComponent):
    
    def extract_all_variables(self, variables: Dict[str, Variable]) -> Dict[str, pd.DataFrame]:
        self.log_info("Extracting solution data...")
        
        solution_data = {}
        
        var_list = [
            ('x', 'x'), ('y', 'y'), ('Inv', 'Inv'),
            ('reloc', 'reloc'), ('staff', 'staff'),
            ('product_fulfilled', 'product_fulfilled'),
            ('service_delivered', 'service_delivered'),
            ('backlog_prod', 'backlog_prod'),
            ('backlog_serv', 'backlog_serv'),
            ('Exp', 'Exp'), ('theta', 'theta')
        ]
        
        for var_key, var_name in var_list:
            if var_key in variables:
                var = variables[var_key]
                rec = var.records
                if rec is not None and not rec.empty:
                    solution_data[var_name] = rec
                    self.log_info(f"  + {var_name}: {len(rec)} records")
                else:
                    self.log_info(f"  - {var_name}: EMPTY")
                    solution_data[var_name] = pd.DataFrame()
        
        return solution_data
    
    def compute_objective_breakdown(self, variables: Dict, parameters: Dict) -> Dict[str, float]:
        self.log_info("Computing objective breakdown...")
        
        breakdown = {}
        
        try:
            breakdown['shipment'] = self._compute_term(
                variables['x'], parameters['CS'], "Shipment"
            )
            
            breakdown['procurement'] = self._compute_term(
                variables['y'], parameters['CP'], "Procurement"
            )
            
            breakdown['holding'] = self._compute_term(
                variables['Inv'], parameters['CH'], "Holding"
            )
            
            breakdown['wages'] = self._compute_term(
                variables['staff'], parameters['CW'], "Wages"
            )
            
            breakdown['relocation'] = self._compute_term(
                variables['reloc'], parameters['CM'], "Relocation"
            )
            
            breakdown['backlog_prod'] = self._compute_term(
                variables['backlog_prod'], parameters['gamma'], "Backlog (Products)"
            )
            breakdown['backlog_serv'] = self._compute_term(
                variables['backlog_serv'], parameters['gamma'], "Backlog (Services)"
            )
            breakdown['backlog'] = breakdown['backlog_prod'] + breakdown['backlog_serv']
            
            breakdown['late_prod'] = self._compute_term(
                variables['product_fulfilled'], parameters['delta'], "Late Products"
            )
            breakdown['late_serv'] = self._compute_term(
                variables['service_delivered'], parameters['delta'], "Late Services"
            )
            breakdown['late'] = breakdown['late_prod'] + breakdown['late_serv']
            
            breakdown['total'] = (
                breakdown['shipment'] + breakdown['procurement'] + 
                breakdown['holding'] + breakdown['wages'] + 
                breakdown['relocation'] + breakdown['backlog'] + breakdown['late']
            )
            
        except Exception as e:
            self.log_error(f"Error computing breakdown: {e}")
        
        return breakdown
    
    def _compute_term(self, variable: Variable, parameter=None, name="Term") -> float:
        try:
            val = 0
            if variable.records is None or variable.records.empty:
                return 0.0
            
            v_df = variable.records
            
            if parameter is not None:
                p_df = parameter.records
                if p_df is None or p_df.empty:
                    try:
                        scalar_val = parameter.toValue()
                        val = (v_df['level'] * scalar_val).sum()
                    except:
                        val = 0
                else:
                    p_df_merge = p_df.copy()
                    
                    if 'k' in p_df_merge.columns:
                        if 'p' in v_df.columns:
                            p_df_merge.rename(columns={'k': 'p'}, inplace=True)
                        elif 's' in v_df.columns:
                            p_df_merge.rename(columns={'k': 's'}, inplace=True)
                    
                    common_cols = list(set(v_df.columns) & set(p_df_merge.columns))
                    if not common_cols:
                        if len(p_df) == 1:
                            scalar_val = p_df.iloc[0]['value']
                            val = (v_df['level'] * scalar_val).sum()
                        else:
                            val = 0
                    else:
                        merged = pd.merge(v_df, p_df_merge, on=common_cols, how='inner')
                        val = (merged['level'] * merged['value']).sum()
            else:
                val = v_df['level'].sum()
            
            return val
        except Exception as e:
            self.log_error(f"Error computing {name}: {e}")
            return 0.0
    
    def compute_expired_statistics(self, exp_var: Variable) -> Dict[str, Any]:
        stats = {}
        
        if exp_var.records is None or exp_var.records.empty:
            self.log_info("No expired demand data")
            stats['total'] = 0
            stats['by_period'] = pd.DataFrame()
            return stats
        
        exp_df = exp_var.records
        
        stats['total'] = exp_df['level'].sum()
        stats['by_period'] = exp_df.groupby('t')['level'].sum().reset_index()
        stats['by_period'].columns = ['Period', 'Expired']
        
        non_zero = stats['by_period'][stats['by_period']['Expired'] > 0]
        if len(non_zero) > 0:
            stats['average'] = non_zero['Expired'].mean()
            stats['max'] = non_zero['Expired'].max()
            stats['max_period'] = non_zero[non_zero['Expired'] == stats['max']]['Period'].values[0]
        else:
            stats['average'] = 0
            stats['max'] = 0
            stats['max_period'] = None
        
        return stats

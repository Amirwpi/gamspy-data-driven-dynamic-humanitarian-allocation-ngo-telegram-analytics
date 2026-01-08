
import pandas as pd
from gamspy import Container, Parameter
from typing import Dict, List, Any

from ..core.base_component import BaseComponent
from ..core.constants import RISK_LEVELS, BACKLOG_AGES, ITEM_TO_CONFIG_KEY

class ParameterManager(BaseComponent):
    
    def __init__(self, config: Dict[str, Any], container: Container):
        super().__init__(config)
        self.container = container
    
    def create_demand_parameter(self, demand_df: pd.DataFrame, 
                               sets: Dict, products: List[str], 
                               services: List[str]) -> Parameter:
        self.log_info("  Creating demand parameter...")
        
        D_ikrt = Parameter(self.container, name="D_ikrt", 
                          domain=[sets['i'], sets['k'], sets['r'], sets['t']])
        
        demand_records = []
        
        for _, row in demand_df.iterrows():
            location = row['Location']
            time_period = row['t']
            
            for item in (products + services):
                for risk in RISK_LEVELS:
                    if item in services:
                        col_name = f"service_{item}_{risk}"
                    else:
                        col_name = f"product_{item}_{risk}"
                    
                    if col_name in demand_df.columns:
                        demand_value = row[col_name]
                        if pd.notna(demand_value) and demand_value > 0:
                            demand_records.append({
                                'i': location,
                                'k': item,
                                'r': risk,
                                't': time_period,
                                'value': demand_value
                            })
        
        D_ikrt.setRecords(demand_records)
        self.log_info(f"    {len(demand_records)} demand records created")
        
        return D_ikrt
    
    def create_cost_parameters(self, sets: Dict, products: List[str], 
                              services: List[str], locations: List[str]) -> Dict[str, Parameter]:
        self.log_info("  Creating cost parameters...")
        
        costs = self.get_config_value('costs')
        origin = self.get_config_value('policy', 'procurement_origin')
        
        CS = Parameter(self.container, name="CS", domain=[sets['i'], sets['j']])
        cs_records = [
            {'i': l1, 'j': l2, 'value': costs['shipment']['value']}
            for l1 in locations for l2 in locations if l1 != l2
        ]
        CS.setRecords(cs_records)
        
        CP = Parameter(self.container, name="CP", domain=[sets['i'], sets['p']])
        cp_records = [
            {'i': origin, 'p': prod, 'value': costs['procurement'][prod]}
            for prod in products if prod in costs['procurement']
        ]
        CP.setRecords(cp_records)
        
        CH = Parameter(self.container, name="CH", domain=[sets['p']])
        ch_records = [
            {'p': prod, 'value': costs['holding']['value']}
            for prod in products
        ]
        CH.setRecords(ch_records)
        
        CW = Parameter(self.container, name="CW", domain=[sets['s']])
        cw_records = [
            {'s': serv, 'value': costs['wage'][serv]}
            for serv in services
        ]
        CW.setRecords(cw_records)
        
        CM = Parameter(self.container, name="CM", domain=[sets['i'], sets['j'], sets['s']])
        cm_records = [
            {'i': l1, 'j': l2, 's': serv, 'value': costs['relocation']['value']}
            for l1 in locations for l2 in locations 
            for serv in services if l1 != l2
        ]
        CM.setRecords(cm_records)
        
        return {'CS': CS, 'CP': CP, 'CH': CH, 'CW': CW, 'CM': CM}
    
    def create_capacity_parameters(self, sets: Dict, services: List[str], 
                                   time_periods: List[int]) -> Dict[str, Parameter]:
        capacity = self.get_config_value('capacity')
        
        alpha = Parameter(self.container, name="alpha", domain=[sets['s']])
        alpha_records = [
            {'s': serv, 'value': capacity['staff_service_capacity'][serv]}
            for serv in services
        ]
        alpha.setRecords(alpha_records)
        
        G = Parameter(self.container, name="G", domain=[sets['s'], sets['t']])
        g_records = [
            {'s': serv, 't': time, 'value': capacity['total_staff_available'][serv]}
            for serv in services for time in time_periods
        ]
        G.setRecords(g_records)
        
        return {'alpha': alpha, 'G': G}
    
    def create_penalty_parameters(self, sets: Dict, products: List[str], 
                                  services: List[str]) -> Dict[str, Parameter]:
        penalties_config = self.get_config_value('penalties')
        
        gamma = Parameter(self.container, name="gamma", 
                         domain=[sets['k'], sets['r'], sets['a']])
        
        gamma_records = []
        for item in (products + services):
            config_key = ITEM_TO_CONFIG_KEY.get(item)
            if config_key and config_key in penalties_config:
                item_penalties = penalties_config[config_key]
                for risk in RISK_LEVELS:
                    for age in BACKLOG_AGES:
                        gamma_records.append({
                            'k': item,
                            'r': risk,
                            'a': age,
                            'value': item_penalties[risk][age]
                        })
        
        gamma.setRecords(gamma_records)
        self.log_info(f"    Loaded {len(gamma_records)} penalty values")
        
        delta = Parameter(self.container, name="delta", 
                         domain=[sets['k'], sets['r'], sets['a']])
        delta_records = [
            {'k': item, 'r': risk, 'a': age, 'value': 0}
            for item in (products + services)
            for risk in RISK_LEVELS
            for age in BACKLOG_AGES
        ]
        delta.setRecords(delta_records)
        
        return {'gamma': gamma, 'delta': delta}
    
    def create_network_parameters(self, network_data: Dict, sets: Dict) -> Dict[str, Parameter]:
        Aij = Parameter(self.container, name="Aij", domain=[sets['i'], sets['j']])
        Aij.setRecords(network_data['aij'].rename(columns={'BC': 'value'}))
        
        dist_ij = Parameter(self.container, name="dist_ij", domain=[sets['i'], sets['j']])
        dist_ij.setRecords(network_data['distances'].rename(columns={'dist_km': 'value'}))
        
        return {'Aij': Aij, 'dist_ij': dist_ij}
    
    def create_policy_parameters(self, sets: Dict, locations: List[str], 
                                 time_periods: List[int], 
                                 initial_conditions: Dict) -> Dict[str, Parameter]:
        origin = self.get_config_value('policy', 'procurement_origin')
        
        eta = Parameter(self.container, name="eta", domain=[sets['i']])
        
        if initial_conditions.get('procurement_allowance') is not None:
            allow_df = initial_conditions['procurement_allowance']
            eta_recs = [
                {'i': row['Location'], 'value': row['Allowed']}
                for _, row in allow_df.iterrows()
            ]
            eta.setRecords(eta_recs)
        else:
            eta_recs = [
                {'i': loc, 'value': 1 if loc == origin else 0}
                for loc in locations
            ]
            eta.setRecords(eta_recs)
        
        mu = Parameter(self.container, name="mu")
        mu.setRecords(self.get_config_value('policy', 'fairness_weight'))
        
        M_param = Parameter(self.container, name="M")
        M_param.setRecords(self.get_config_value('policy', 'big_M'))
        
        beta = Parameter(self.container, name="beta", domain=[sets['t']])
        beta_records = [
            {'t': time, 'value': self.get_config_value('budget', 'per_period')}
            for time in time_periods
        ]
        beta.setRecords(beta_records)
        
        return {'eta': eta, 'mu': mu, 'M': M_param, 'beta': beta}
    
    def create_initial_condition_parameters(self, sets: Dict, products: List[str], 
                                           services: List[str], locations: List[str], 
                                           initial_conditions: Dict) -> Dict[str, Parameter]:
        origin = self.get_config_value('policy', 'procurement_origin')
        capacity = self.get_config_value('capacity')
        
        Inv0 = Parameter(self.container, name="Inv0", domain=[sets['i'], sets['p']])
        
        if initial_conditions.get('inventory') is not None:
            inv_df = initial_conditions['inventory']
            inv0_records = [
                {'i': row['location'], 'p': row['product'], 'value': row['initial_quantity']}
                for _, row in inv_df.iterrows()
            ]
            Inv0.setRecords(inv0_records)
            self.log_info(f"    Loaded {len(inv0_records)} initial inventory records")
        else:
            inv0_records = [
                {'i': loc, 'p': prod, 'value': 0}
                for loc in locations for prod in products
            ]
            Inv0.setRecords(inv0_records)
            self.log_info("    Using zero initial inventory")
        
        staff0 = Parameter(self.container, name="staff0", domain=[sets['i'], sets['s']])
        staff0_records = []
        for loc in locations:
            for serv in services:
                if loc == origin:
                    staff0_records.append({
                        'i': loc, 's': serv, 
                        'value': capacity['total_staff_available'][serv]
                    })
                else:
                    staff0_records.append({'i': loc, 's': serv, 'value': 0})
        
        staff0.setRecords(staff0_records)
        
        return {'Inv0': Inv0, 'staff0': staff0}

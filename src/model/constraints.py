
from gamspy import Container, Equation, Parameter, Sum
from typing import Dict, List

from ..core.base_component import BaseComponent

class ConstraintBuilder(BaseComponent):
    
    def __init__(self, config: Dict, container: Container):
        super().__init__(config)
        self.container = container
    
    def build_all_constraints(self, variables: Dict, parameters: Dict, 
                             sets: Dict, time_periods: List[int]) -> List[Equation]:
        self.log_info("Building constraints...")
        
        constraints = []
        
        t0 = time_periods[0]
        run_periods = Parameter(self.container, name="run_periods", domain=[sets['t']])
        run_periods_records = [{'t': p, 'value': 1} for p in time_periods if p != t0]
        run_periods.setRecords(run_periods_records)
        
        constraints.extend(self.build_initial_conditions(variables, parameters, sets, t0))
        constraints.extend(self.build_flow_balance_constraints(variables, parameters, sets, run_periods))
        constraints.extend(self.build_capacity_constraints(variables, parameters, sets))
        constraints.extend(self.build_backlog_constraints(variables, parameters, sets, run_periods))
        constraints.extend(self.build_fairness_constraints(variables, parameters, sets, run_periods))
        constraints.extend(self.build_policy_constraints(variables, parameters, sets, run_periods, t0))
        
        self.log_info(f"  Created {len(constraints)} equation groups")
        
        return constraints
    
    def build_initial_conditions(self, variables: Dict, parameters: Dict, 
                                 sets: Dict, t0) -> List[Equation]:
        self.log_info("  Building initial conditions...")
        
        i, j, p, s, r, a = (sets['i'], sets['j'], sets['p'], 
                           sets['s'], sets['r'], sets['a'])
        
        constraints = []
        
        init_inv = Equation(self.container, name="init_inv", domain=[i, p])
        init_inv[i, p] = variables['Inv'][i, p, t0] == parameters['Inv0'][i, p] + variables['y'][i, p, t0]
        constraints.append(init_inv)
        
        init_backlog_prod = Equation(self.container, name="init_backlog_prod", domain=[i, p, r, a])
        init_backlog_prod[i, p, r, a] = variables['backlog_prod'][i, p, r, a, t0] == 0
        constraints.append(init_backlog_prod)
        
        init_backlog_serv = Equation(self.container, name="init_backlog_serv", domain=[i, s, r, a])
        init_backlog_serv[i, s, r, a] = variables['backlog_serv'][i, s, r, a, t0] == 0
        constraints.append(init_backlog_serv)
        
        init_shipment = Equation(self.container, name="init_shipment", domain=[i, j, p])
        init_shipment[i, j, p] = variables['x'][i, j, p, t0] == 0
        constraints.append(init_shipment)
        
        init_product_fulfilled = Equation(self.container, name="init_product_fulfilled", domain=[i, p, r, a])
        init_product_fulfilled[i, p, r, a] = variables['product_fulfilled'][i, p, r, a, t0] == 0
        constraints.append(init_product_fulfilled)
        
        init_service_delivered = Equation(self.container, name="init_service_delivered", domain=[i, s, r, a])
        init_service_delivered[i, s, r, a] = variables['service_delivered'][i, s, r, a, t0] == 0
        constraints.append(init_service_delivered)
        
        init_reloc = Equation(self.container, name="init_reloc", domain=[i, j, s])
        init_reloc[i, j, s] = variables['reloc'][i, j, s, t0] == 0
        constraints.append(init_reloc)
        
        staff_flow_t0 = Equation(self.container, name="staff_flow_t0", domain=[i, s])
        staff_flow_t0[i, s] = variables['staff'][i, s, t0] == parameters['staff0'][i, s] + Sum(j, variables['reloc'][j, i, s, t0]) - Sum(j, variables['reloc'][i, j, s, t0])
        constraints.append(staff_flow_t0)
        
        expire_init = Equation(self.container, name="expire_init", domain=[i, sets['k'], r])
        expire_init[i, sets['k'], r] = variables['Exp'][i, sets['k'], r, t0] == 0
        constraints.append(expire_init)
        
        return constraints
    
    def build_flow_balance_constraints(self, variables: Dict, parameters: Dict, 
                                      sets: Dict, run_periods: Parameter) -> List[Equation]:
        self.log_info("  Building flow balance constraints...")
        
        i, j, p, s, t, r, a = (sets['i'], sets['j'], sets['p'], 
                               sets['s'], sets['t'], sets['r'], sets['a'])
        
        constraints = []
        
        inv_balance = Equation(self.container, name="inv_balance", domain=[i, p, t])
        inv_balance[i, p, t].where[run_periods[t]] = (
            variables['Inv'][i, p, t] == 
            variables['Inv'][i, p, t.lag(1)] + 
            variables['y'][i, p, t] + 
            Sum(j, variables['x'][j, i, p, t.lag(1)]) - 
            Sum(j, variables['x'][i, j, p, t]) - 
            Sum([r, a], variables['product_fulfilled'][i, p, r, a, t])
        )
        constraints.append(inv_balance)
        
        no_seq_ship = Equation(self.container, name="no_seq_ship", domain=[i, p, t])
        no_seq_ship[i, p, t].where[run_periods[t]] = (
            Sum(j, variables['x'][i, j, p, t]) <= 
            variables['Inv'][i, p, t.lag(1)] + 
            variables['y'][i, p, t] + 
            Sum(j, variables['x'][j, i, p, t.lag(1)])
        )
        constraints.append(no_seq_ship)
        
        staff_flow = Equation(self.container, name="staff_flow", domain=[i, s, t])
        staff_flow[i, s, t].where[run_periods[t]] = (
            variables['staff'][i, s, t] == 
            variables['staff'][i, s, t.lag(1)] + 
            Sum(j, variables['reloc'][j, i, s, t]) - 
            Sum(j, variables['reloc'][i, j, s, t])
        )
        constraints.append(staff_flow)
        
        return constraints
    
    def build_capacity_constraints(self, variables: Dict, parameters: Dict, 
                                   sets: Dict) -> List[Equation]:
        self.log_info("  Building capacity constraints...")
        
        i, j, p, s, t, r, a = (sets['i'], sets['j'], sets['p'], 
                               sets['s'], sets['t'], sets['r'], sets['a'])
        
        constraints = []
        
        border = Equation(self.container, name="border", domain=[i, j, p, t])
        border[i, j, p, t] = variables['x'][i, j, p, t] <= parameters['M'] * parameters['Aij'][i, j]
        constraints.append(border)
        
        service_cap = Equation(self.container, name="service_cap", domain=[i, s, t])
        service_cap[i, s, t] = (
            Sum([r, a], variables['service_delivered'][i, s, r, a, t]) <= 
            parameters['alpha'][s] * variables['staff'][i, s, t]
        )
        constraints.append(service_cap)
        
        staff_global = Equation(self.container, name="staff_global", domain=[s, t])
        staff_global[s, t] = Sum(i, variables['staff'][i, s, t]) <= parameters['G'][s, t]
        constraints.append(staff_global)
        
        budget_constraint = Equation(self.container, name="budget_constraint", domain=[t])
        budget_constraint[t] = (
            Sum([i, j, p], parameters['CS'][i, j] * variables['x'][i, j, p, t]) +
            Sum([i, p], parameters['CP'][i, p] * variables['y'][i, p, t]) +
            Sum([i, p], parameters['CH'][p] * variables['Inv'][i, p, t]) +
            Sum([i, s], parameters['CW'][s] * variables['staff'][i, s, t]) +
            Sum([i, j, s], parameters['CM'][i, j, s] * variables['reloc'][i, j, s, t])
        ) <= parameters['beta'][t]
        constraints.append(budget_constraint)
        
        return constraints
    
    def build_backlog_constraints(self, variables: Dict, parameters: Dict, 
                                  sets: Dict, run_periods: Parameter) -> List[Equation]:
        self.log_info("  Building backlog constraints...")
        
        i, p, s, t, r, a = (sets['i'], sets['p'], sets['s'], 
                           sets['t'], sets['r'], sets['a'])
        
        constraints = []
        
        age1_backlog_prod = Equation(self.container, name="age1_backlog_prod", domain=[i, p, r, t])
        age1_backlog_prod[i, p, r, t].where[run_periods[t]] = (
            variables['backlog_prod'][i, p, r, 1, t] == 
            parameters['D_ikrt'][i, p, r, t] - 
            variables['product_fulfilled'][i, p, r, 1, t]
        )
        constraints.append(age1_backlog_prod)
        
        age2_backlog_prod = Equation(self.container, name="age2_backlog_prod", domain=[i, p, r, t])
        age2_backlog_prod[i, p, r, t].where[run_periods[t]] = (
            variables['backlog_prod'][i, p, r, 2, t] == 
            variables['backlog_prod'][i, p, r, 1, t.lag(1)] - 
            variables['product_fulfilled'][i, p, r, 2, t]
        )
        constraints.append(age2_backlog_prod)
        
        age3_backlog_prod = Equation(self.container, name="age3_backlog_prod", domain=[i, p, r, t])
        age3_backlog_prod[i, p, r, t].where[run_periods[t]] = (
            variables['backlog_prod'][i, p, r, 3, t] == 
            variables['backlog_prod'][i, p, r, 2, t.lag(1)] - 
            variables['product_fulfilled'][i, p, r, 3, t]
        )
        constraints.append(age3_backlog_prod)
        
        u_cap1_prod = Equation(self.container, name="u_cap1_prod", domain=[i, p, r, t])
        u_cap1_prod[i, p, r, t].where[run_periods[t]] = (
            variables['product_fulfilled'][i, p, r, 1, t] <= parameters['D_ikrt'][i, p, r, t]
        )
        constraints.append(u_cap1_prod)
        
        u_cap2_prod = Equation(self.container, name="u_cap2_prod", domain=[i, p, r, t])
        u_cap2_prod[i, p, r, t].where[run_periods[t]] = (
            variables['product_fulfilled'][i, p, r, 2, t] <= variables['backlog_prod'][i, p, r, 1, t.lag(1)]
        )
        constraints.append(u_cap2_prod)
        
        u_cap3_prod = Equation(self.container, name="u_cap3_prod", domain=[i, p, r, t])
        u_cap3_prod[i, p, r, t].where[run_periods[t]] = (
            variables['product_fulfilled'][i, p, r, 3, t] <= variables['backlog_prod'][i, p, r, 2, t.lag(1)]
        )
        constraints.append(u_cap3_prod)
        
        expire_def_prod = Equation(self.container, name="expire_def_prod", domain=[i, p, r, t])
        expire_def_prod[i, p, r, t].where[run_periods[t]] = (
            variables['Exp'][i, p, r, t] == variables['backlog_prod'][i, p, r, 3, t.lag(1)]
        )
        constraints.append(expire_def_prod)
        
        age1_backlog_serv = Equation(self.container, name="age1_backlog_serv", domain=[i, s, r, t])
        age1_backlog_serv[i, s, r, t].where[run_periods[t]] = (
            variables['backlog_serv'][i, s, r, 1, t] == 
            parameters['D_ikrt'][i, s, r, t] - 
            variables['service_delivered'][i, s, r, 1, t]
        )
        constraints.append(age1_backlog_serv)
        
        age2_backlog_serv = Equation(self.container, name="age2_backlog_serv", domain=[i, s, r, t])
        age2_backlog_serv[i, s, r, t].where[run_periods[t]] = (
            variables['backlog_serv'][i, s, r, 2, t] == 
            variables['backlog_serv'][i, s, r, 1, t.lag(1)] - 
            variables['service_delivered'][i, s, r, 2, t]
        )
        constraints.append(age2_backlog_serv)
        
        age3_backlog_serv = Equation(self.container, name="age3_backlog_serv", domain=[i, s, r, t])
        age3_backlog_serv[i, s, r, t].where[run_periods[t]] = (
            variables['backlog_serv'][i, s, r, 3, t] == 
            variables['backlog_serv'][i, s, r, 2, t.lag(1)] - 
            variables['service_delivered'][i, s, r, 3, t]
        )
        constraints.append(age3_backlog_serv)
        
        u_cap1_serv = Equation(self.container, name="u_cap1_serv", domain=[i, s, r, t])
        u_cap1_serv[i, s, r, t].where[run_periods[t]] = (
            variables['service_delivered'][i, s, r, 1, t] <= parameters['D_ikrt'][i, s, r, t]
        )
        constraints.append(u_cap1_serv)
        
        u_cap2_serv = Equation(self.container, name="u_cap2_serv", domain=[i, s, r, t])
        u_cap2_serv[i, s, r, t].where[run_periods[t]] = (
            variables['service_delivered'][i, s, r, 2, t] <= variables['backlog_serv'][i, s, r, 1, t.lag(1)]
        )
        constraints.append(u_cap2_serv)
        
        u_cap3_serv = Equation(self.container, name="u_cap3_serv", domain=[i, s, r, t])
        u_cap3_serv[i, s, r, t].where[run_periods[t]] = (
            variables['service_delivered'][i, s, r, 3, t] <= variables['backlog_serv'][i, s, r, 2, t.lag(1)]
        )
        constraints.append(u_cap3_serv)
        
        expire_def_serv = Equation(self.container, name="expire_def_serv", domain=[i, s, r, t])
        expire_def_serv[i, s, r, t].where[run_periods[t]] = (
            variables['Exp'][i, s, r, t] == variables['backlog_serv'][i, s, r, 3, t.lag(1)]
        )
        constraints.append(expire_def_serv)
        
        return constraints
    
    def build_fairness_constraints(self, variables: Dict, parameters: Dict, 
                                   sets: Dict, run_periods: Parameter) -> List[Equation]:
        self.log_info("  Building fairness constraints...")
        
        i, p, s, t, r, a = (sets['i'], sets['p'], sets['s'], 
                           sets['t'], sets['r'], sets['a'])
        
        constraints = []
        
        fairness_prod = Equation(self.container, name="fairness_prod", domain=[p, t])
        fairness_prod[p, t].where[run_periods[t]] = (
            Sum([i, r, a], variables['product_fulfilled'][i, p, r, a, t]) >= 
            variables['theta'][t] * Sum([i, r], parameters['D_ikrt'][i, p, r, t])
        )
        constraints.append(fairness_prod)
        
        fairness_serv = Equation(self.container, name="fairness_serv", domain=[s, t])
        fairness_serv[s, t].where[run_periods[t]] = (
            Sum([i, r, a], variables['service_delivered'][i, s, r, a, t]) >= 
            variables['theta'][t] * Sum([i, r], parameters['D_ikrt'][i, s, r, t])
        )
        constraints.append(fairness_serv)
        
        return constraints
    
    def build_policy_constraints(self, variables: Dict, parameters: Dict, 
                                 sets: Dict, run_periods: Parameter, t0) -> List[Equation]:
        self.log_info("  Building policy constraints...")
        
        i, p, t = sets['i'], sets['p'], sets['t']
        
        constraints = []
        
        procure_standard = Equation(self.container, name="procure_standard", domain=[i, p, t])
        procure_standard[i, p, t].where[run_periods[t]] = (
            variables['y'][i, p, t] <= parameters['M'] * parameters['eta'][i]
        )
        constraints.append(procure_standard)
        
        procure_t0 = Equation(self.container, name="procure_t0", domain=[i, p])
        procure_t0[i, p] = variables['y'][i, p, t0] <= parameters['M'] * parameters['eta'][i]
        constraints.append(procure_t0)
        
        return constraints

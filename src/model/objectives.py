
from gamspy import Container, Equation, Sum
from typing import Dict

from ..core.base_component import BaseComponent

class ObjectiveBuilder(BaseComponent):
    
    def __init__(self, config: Dict, container: Container):
        super().__init__(config)
        self.container = container
    
    def build_fairness_objective(self, variables: Dict, sets: Dict) -> Equation:
        self.log_info("  Building fairness objective...")
        
        fair_objective = Equation(self.container, name="fair_objective")
        fair_objective[...] = variables['fair_obj'] == Sum(sets['t'], variables['theta'][sets['t']])
        
        return fair_objective
    
    def build_cost_objective(self, variables: Dict, parameters: Dict, sets: Dict) -> Equation:
        self.log_info("  Building cost objective...")
        
        i, j, p, s, t, r, a = (sets['i'], sets['j'], sets['p'], 
                                sets['s'], sets['t'], sets['r'], sets['a'])
        
        cost_objective = Equation(self.container, name="cost_objective")
        cost_objective[...] = variables['cost_obj'] == Sum(t, 
            Sum([i, j, p], parameters['CS'][i, j] * variables['x'][i, j, p, t]) +
            Sum([i, p], parameters['CP'][i, p] * variables['y'][i, p, t]) +
            Sum([i, p], parameters['CH'][p] * variables['Inv'][i, p, t]) +
            Sum([i, s], parameters['CW'][s] * variables['staff'][i, s, t]) +
            Sum([i, j, s], parameters['CM'][i, j, s] * variables['reloc'][i, j, s, t]) +
            Sum([i, p, r, a], parameters['gamma'][p, r, a] * variables['backlog_prod'][i, p, r, a, t]) +
            Sum([i, s, r, a], parameters['gamma'][s, r, a] * variables['backlog_serv'][i, s, r, a, t]) +
            Sum([i, p, r, a], parameters['delta'][p, r, a] * variables['product_fulfilled'][i, p, r, a, t]) +
            Sum([i, s, r, a], parameters['delta'][s, r, a] * variables['service_delivered'][i, s, r, a, t])
        )
        
        return cost_objective

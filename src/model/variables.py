
from gamspy import Container, Variable
from typing import Dict

from ..core.base_component import BaseComponent

class VariableBuilder(BaseComponent):
    
    def __init__(self, config: Dict, container: Container):
        super().__init__(config)
        self.container = container
    
    def build_all_variables(self, sets: Dict) -> Dict[str, Variable]:
        self.log_info("Building variables...")
        
        variables = {}
        
        variables['x'] = Variable(self.container, name="x", 
                                 domain=[sets['i'], sets['j'], sets['p'], sets['t']], 
                                 type="integer")
        
        variables['y'] = Variable(self.container, name="y", 
                                 domain=[sets['i'], sets['p'], sets['t']], 
                                 type="integer")
        
        variables['Inv'] = Variable(self.container, name="Inv", 
                                   domain=[sets['i'], sets['p'], sets['t']], 
                                   type="integer")
        
        variables['reloc'] = Variable(self.container, name="reloc", 
                                     domain=[sets['i'], sets['j'], sets['s'], sets['t']], 
                                     type="integer")
        
        variables['staff'] = Variable(self.container, name="staff", 
                                     domain=[sets['i'], sets['s'], sets['t']], 
                                     type="integer")
        
        variables['product_fulfilled'] = Variable(
            self.container, name="product_fulfilled", 
            domain=[sets['i'], sets['p'], sets['r'], sets['a'], sets['t']], 
            type="integer"
        )
        
        variables['service_delivered'] = Variable(
            self.container, name="service_delivered", 
            domain=[sets['i'], sets['s'], sets['r'], sets['a'], sets['t']], 
            type="integer"
        )
        
        variables['backlog_prod'] = Variable(
            self.container, name="backlog_prod", 
            domain=[sets['i'], sets['p'], sets['r'], sets['a'], sets['t']], 
            type="integer"
        )
        
        variables['backlog_serv'] = Variable(
            self.container, name="backlog_serv", 
            domain=[sets['i'], sets['s'], sets['r'], sets['a'], sets['t']], 
            type="integer"
        )
        
        variables['Exp'] = Variable(
            self.container, name="Exp", 
            domain=[sets['i'], sets['k'], sets['r'], sets['t']], 
            type="integer"
        )
        
        variables['theta'] = Variable(
            self.container, name="theta", 
            domain=[sets['t']], 
            type="positive"
        )
        
        variables['fair_obj'] = Variable(self.container, name="fair_obj")
        variables['cost_obj'] = Variable(self.container, name="cost_obj")
        
        self._set_bounds(variables, sets)
        
        self.log_info(f"  Created {len(variables)} variables")
        
        return variables
    
    def _set_bounds(self, variables: Dict, sets: Dict) -> None:
        i, j, p, s, t, r, a, k = (sets['i'], sets['j'], sets['p'], 
                                   sets['s'], sets['t'], sets['r'], 
                                   sets['a'], sets['k'])
        
        variables['x'].lo[i, j, p, t] = 0
        variables['y'].lo[i, p, t] = 0
        variables['Inv'].lo[i, p, t] = 0
        variables['reloc'].lo[i, j, s, t] = 0
        variables['staff'].lo[i, s, t] = 0
        variables['product_fulfilled'].lo[i, p, r, a, t] = 0
        variables['service_delivered'].lo[i, s, r, a, t] = 0
        variables['backlog_prod'].lo[i, p, r, a, t] = 0
        variables['backlog_serv'].lo[i, s, r, a, t] = 0
        variables['Exp'].lo[i, k, r, t] = 0
        
        variables['theta'].lo[t] = 0
        variables['theta'].up[t] = 1

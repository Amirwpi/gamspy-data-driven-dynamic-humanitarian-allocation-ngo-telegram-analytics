
from gamspy import Container, Set, Alias
from typing import Dict, List

from ..core.base_component import BaseComponent
from ..core.constants import RISK_LEVELS, BACKLOG_AGES

class SetBuilder(BaseComponent):
    
    def __init__(self, config: Dict, container: Container):
        super().__init__(config)
        self.container = container
    
    def build_all_sets(self, sets_data: Dict[str, List]) -> Dict[str, Set]:
        self.log_info("Building sets...")
        
        sets = {}
        
        sets['i'] = Set(self.container, name="i", 
                       records=sets_data['locations'])
        sets['j'] = Alias(self.container, name="j", alias_with=sets['i'])
        
        sets['t'] = Set(self.container, name="t", 
                       records=sets_data['time_periods'])
        
        sets['t_pos'] = Set(self.container, name="t_pos", domain=[sets['t']], 
                           records=sets_data['time_periods'][1:])
        
        sets['r'] = Set(self.container, name="r", records=RISK_LEVELS)
        
        all_items = sets_data['products'] + sets_data['services']
        sets['k'] = Set(self.container, name="k", records=all_items)
        
        sets['p'] = Set(self.container, name="p", domain=[sets['k']], 
                       records=sets_data['products'])
        
        sets['s'] = Set(self.container, name="s", domain=[sets['k']], 
                       records=sets_data['services'])
        
        sets['a'] = Set(self.container, name="a", records=BACKLOG_AGES)
        
        self.log_info(f"  Created {len(sets)} sets")
        
        return sets


from gamspy import Container, Model, Sense
from pathlib import Path
from typing import Dict, Any

from ..core.base_component import BaseComponent
from .sets import SetBuilder
from .variables import VariableBuilder
from .objectives import ObjectiveBuilder
from .constraints import ConstraintBuilder
from ..data.data_manager import DataManager
from ..data.parameter_manager import ParameterManager

class HumanitarianLogisticsModel(BaseComponent):
    
    def __init__(self, config: Dict[str, Any], data_manager: DataManager):
        super().__init__(config)
        self.data_manager = data_manager
        
        self.container = Container()
        
        self.set_builder = SetBuilder(config, self.container)
        self.variable_builder = VariableBuilder(config, self.container)
        self.objective_builder = ObjectiveBuilder(config, self.container)
        self.constraint_builder = ConstraintBuilder(config, self.container)
        self.parameter_manager = ParameterManager(config, self.container)
        
        self.sets = None
        self.parameters = None
        self.variables = None
        self.equations = None
        self.objectives = None
    
    def build_model(self) -> None:
        self.log_info("="*80)
        self.log_info("BUILDING HUMANITARIAN LOGISTICS OPTIMIZATION MODEL")
        self.log_info("="*80)
        
        sets_data = self.data_manager.get_sets()
        self.sets = self.set_builder.build_all_sets(sets_data)
        
        self.log_info("\nBuilding parameters...")
        self.parameters = self._build_all_parameters()
        
        self.variables = self.variable_builder.build_all_variables(self.sets)
        
        self.log_info("\nBuilding objectives...")
        self.objectives = {
            'fair_objective': self.objective_builder.build_fairness_objective(
                self.variables, self.sets
            ),
            'cost_objective': self.objective_builder.build_cost_objective(
                self.variables, self.parameters, self.sets
            )
        }
        
        self.equations = self.constraint_builder.build_all_constraints(
            self.variables, self.parameters, self.sets, 
            self.data_manager.time_periods
        )
        
        self.log_info("\n" + "="*80)
        self.log_info("MODEL BUILD COMPLETE")
        self.log_info("="*80)
    
    def _build_all_parameters(self) -> Dict[str, Any]:
        params = {}
        
        network_data = self.data_manager.load_network_data()
        params.update(self.parameter_manager.create_network_parameters(
            network_data, self.sets
        ))
        
        params['D_ikrt'] = self.parameter_manager.create_demand_parameter(
            self.data_manager.demand_df,
            self.sets,
            self.data_manager.products,
            self.data_manager.services
        )
        
        params.update(self.parameter_manager.create_cost_parameters(
            self.sets,
            self.data_manager.products,
            self.data_manager.services,
            self.data_manager.locations
        ))
        
        params.update(self.parameter_manager.create_capacity_parameters(
            self.sets,
            self.data_manager.services,
            self.data_manager.time_periods
        ))
        
        params.update(self.parameter_manager.create_penalty_parameters(
            self.sets,
            self.data_manager.products,
            self.data_manager.services
        ))
        
        initial_conditions = self.data_manager.load_initial_conditions()
        params.update(self.parameter_manager.create_policy_parameters(
            self.sets,
            self.data_manager.locations,
            self.data_manager.time_periods,
            initial_conditions
        ))
        
        params.update(self.parameter_manager.create_initial_condition_parameters(
            self.sets,
            self.data_manager.products,
            self.data_manager.services,
            self.data_manager.locations,
            initial_conditions
        ))
        
        self.log_info(f"  Created {len(params)} parameter groups")
        
        return params
    
    def get_stage1_model(self) -> Model:
        equations = [eq for eq in self.container.getEquations() 
                    if eq.name not in ['cost_objective']]
        
        model = Model(
            self.container,
            name="Stage1_Fairness",
            equations=equations,
            problem="MIP",
            sense=Sense.MAX,
            objective=self.variables['fair_obj']
        )
        
        return model
    
    def get_stage2_model(self, theta_star: float) -> Model:
        from gamspy import Equation, Sum
        
        eps = self.get_config_value('policy', 'fairness_eps', default=1e-6)
        
        keep_fairness = Equation(self.container, name="keep_fairness")
        keep_fairness[...] = Sum(self.sets['t'], self.variables['theta'][self.sets['t']]) >= theta_star - eps
        
        equations = [eq for eq in self.container.getEquations() 
                    if eq.name not in ['fair_objective']]
        
        model = Model(
            self.container,
            name="Stage2_Cost",
            equations=equations,
            problem="MIP",
            sense=Sense.MIN,
            objective=self.variables['cost_obj']
        )
        
        return model

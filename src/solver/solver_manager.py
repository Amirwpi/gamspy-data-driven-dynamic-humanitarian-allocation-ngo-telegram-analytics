
import sys
from gamspy import Model, Options
from typing import Dict, Any, Tuple

from ..core.base_component import BaseComponent
from .solution_extractor import SolutionExtractor

class TwoStageSolver(BaseComponent):
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.solution_extractor = SolutionExtractor(config)
    
    def solve_stage1(self, model: Model) -> float:
        self.log_info("="*80)
        self.log_info("STAGE 1: FAIRNESS MAXIMIZATION")
        self.log_info("="*80)
        
        solver = self.get_config_value('model', 'solver', default='CPLEX')
        
        self.log_info(f"  Solver: {solver}")
        self.log_info(f"  Problem: MIP")
        self.log_info(f"  Objective: Maximize Sum(theta[t])")
        
        model.solve(solver=solver, output=sys.stdout)
        theta_star = model.objective_value
        
        self.log_info("\n" + "="*80)
        self.log_info(f"STAGE 1 COMPLETE")
        self.log_info(f"  ThetaStar: {theta_star:.6f}")
        self.log_info(f"  Status: {model.status}")
        self.log_info("="*80)
        
        return theta_star
    
    def solve_stage2(self, model: Model, theta_star: float) -> Tuple[float, Dict]:
        self.log_info("\n" + "="*80)
        self.log_info("STAGE 2: COST MINIMIZATION")
        self.log_info("="*80)
        
        solver = self.get_config_value('model', 'solver', default='CPLEX')
        time_limit = self.get_config_value('model', 'time_limit', default=300)
        gap_tolerance = self.get_config_value('model', 'gap_tolerance', default=0.05)
        
        self.log_info(f"  Solver: {solver}")
        self.log_info(f"  Problem: MIP")
        self.log_info(f"  Objective: Minimize Total Cost")
        self.log_info(f"  Fairness preserved: >= {theta_star:.6f}")
        
        solve_options = Options(
            relative_optimality_gap=gap_tolerance,
            time_limit=time_limit
        )
        
        model.solve(solver=solver, options=solve_options, output=sys.stdout)
        total_cost = model.objective_value
        
        stats = {
            'total_cost': total_cost,
            'theta_star': theta_star,
            'status': str(model.status),
            'solve_status': str(model.solve_status)
        }
        
        self.log_info("\n" + "="*80)
        self.log_info(f"STAGE 2 COMPLETE")
        self.log_info(f"  Total Cost: ${total_cost:,.2f}")
        self.log_info(f"  Status: {model.status}")
        self.log_info("="*80)
        
        return total_cost, stats
    
    def extract_solution(self, variables: Dict, parameters: Dict) -> Dict[str, Any]:
        self.log_info("\n" + "="*80)
        self.log_info("EXTRACTING SOLUTION DATA")
        self.log_info("="*80)
        
        self.log_info("\nLoading variable records...")
        for var in variables.values():
            try:
                _ = var.records
            except:
                pass
        
        solution_data = self.solution_extractor.extract_all_variables(variables)
        breakdown = self.solution_extractor.compute_objective_breakdown(
            variables, parameters
        )
        expired_stats = self.solution_extractor.compute_expired_statistics(
            variables.get('Exp')
        )
        
        return {
            'variables': solution_data,
            'breakdown': breakdown,
            'expired_stats': expired_stats
        }

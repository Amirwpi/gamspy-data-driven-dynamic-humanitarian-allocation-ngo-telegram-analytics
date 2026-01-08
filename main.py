
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_manager import DataManager
from src.model.optimization_model import HumanitarianLogisticsModel
from src.solver.solver_manager import TwoStageSolver
from src.output.output_manager import OutputManager

def setup_logging(output_dir: Path) -> logging.Logger:
    log_dir = output_dir / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"optimization_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger('HumanitarianLogistics')
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger

def load_configuration(config_path: Path) -> dict:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    print("="*80)
    print("HUMANITARIAN LOGISTICS OPTIMIZATION SYSTEM")
    print("Object-Oriented GAMSPy Model - Version 2.0")
    print("="*80)
    print()
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "model_config.yaml"
    input_dir = base_dir / "Input_Data"
    output_dir = base_dir / "output"
    
    logger = setup_logging(output_dir)
    logger.info("Starting optimization system")
    
    try:
        logger.info("Loading configuration...")
        config = load_configuration(config_path)
        logger.info(f"  Configuration loaded from {config_path.name}")
        
        logger.info("\n" + "="*80)
        logger.info("PHASE 1: DATA LOADING")
        logger.info("="*80)
        
        data_manager = DataManager(config, input_dir)
        data_manager.load_all_data()
        
        logger.info("\n" + "="*80)
        logger.info("PHASE 2: MODEL BUILDING")
        logger.info("="*80)
        
        opt_model = HumanitarianLogisticsModel(config, data_manager)
        opt_model.build_model()
        
        logger.info("\n" + "="*80)
        logger.info("PHASE 3: OPTIMIZATION")
        logger.info("="*80)
        
        solver = TwoStageSolver(config)
        
        stage1_model = opt_model.get_stage1_model()
        theta_star = solver.solve_stage1(stage1_model)
        
        stage2_model = opt_model.get_stage2_model(theta_star)
        total_cost, solution_stats = solver.solve_stage2(stage2_model, theta_star)
        
        logger.info("\n" + "="*80)
        logger.info("PHASE 4: SOLUTION EXTRACTION")
        logger.info("="*80)
        
        solution_result = solver.extract_solution(
            opt_model.variables,
            opt_model.parameters
        )
        
        logger.info("\n" + "="*80)
        logger.info("PHASE 5: OUTPUT GENERATION")
        logger.info("="*80)
        
        output_manager = OutputManager(config, output_dir)
        output_manager.save_all_outputs(solution_result, solution_stats)
        
        logger.info("\n" + "="*80)
        logger.info("OPTIMIZATION COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        logger.info(f"Total Cost: ${total_cost:,.2f}")
        logger.info(f"Fairness (ThetaStar): {theta_star:.6f}")
        logger.info(f"Outputs saved to: {output_dir}")
        logger.info("="*80)
        
        return 0
    
    except Exception as e:
        logger.error("="*80)
        logger.error("OPTIMIZATION FAILED")
        logger.error("="*80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("="*80)
        return 1

if __name__ == "__main__":
    sys.exit(main())

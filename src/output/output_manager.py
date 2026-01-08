
from pathlib import Path
from typing import Dict, Any

from ..core.base_component import BaseComponent
from .csv_writer import CSVWriter
from .excel_writer import ExcelWriter
from .report_generator import ReportGenerator
from .visualization_prep import VisualizationPrep

class OutputManager(BaseComponent):
    
    def __init__(self, config: Dict[str, Any], output_dir: Path):
        super().__init__(config)
        self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(exist_ok=True, parents=True)
        (self.output_dir / "csvs").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "visualizations").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        self.csv_writer = CSVWriter(config)
        self.excel_writer = ExcelWriter(config)
        self.report_generator = ReportGenerator(config)
    
    def save_all_outputs(self, solution_result: Dict[str, Any],
                        solution_stats: Dict[str, Any]) -> None:
        self.log_info("="*80)
        self.log_info("GENERATING OUTPUTS")
        self.log_info("="*80)
        
        solution_data = solution_result['variables']
        breakdown = solution_result['breakdown']
        expired_stats = solution_result['expired_stats']
        
        if self.get_config_value('output', 'save_csv', default=True):
            self.csv_writer.save_variable_csvs(solution_data, self.output_dir)
        
        if self.get_config_value('output', 'save_excel', default=True):
            excel_path = self.output_dir / "reports" / "optimization_results.xlsx"
            self.excel_writer.save_excel_report(
                solution_data, breakdown, solution_stats, excel_path
            )
        
        self._save_text_reports(breakdown, solution_stats, expired_stats)
        
        if self.get_config_value('output', 'generate_plots', default=True):
            self._generate_visualization_data()
        
        self.log_info("\n" + "="*80)
        self.log_info("ALL OUTPUTS SAVED SUCCESSFULLY")
        self.log_info(f"Output directory: {self.output_dir}")
        self.log_info("="*80)
    
    def _generate_visualization_data(self) -> None:
        self.log_info("\nGenerating visualization data...")
        
        try:
            viz_prep = VisualizationPrep(
                self.config,
                self.output_dir / "csvs",
                self.output_dir / "visualizations"
            )
            viz_prep.prepare_visualization_data()
        except Exception as e:
            self.log_warning(f"  Visualization prep failed: {e}")
    
    def _save_text_reports(self, breakdown: Dict, stats: Dict, 
                          expired_stats: Dict) -> None:
        self.log_info("\nGenerating text reports...")
        
        reports_dir = self.output_dir / "reports"
        
        summary_text = self.report_generator.generate_summary_report(
            breakdown, stats, expired_stats
        )
        summary_path = reports_dir / "summary_report.txt"
        with open(summary_path, 'w') as f:
            f.write(summary_text)
        self.log_info(f"  + summary_report.txt")
        
        print("\n" + summary_text)
        
        if expired_stats.get('total', 0) > 0:
            expired_text = self.report_generator.generate_expired_demand_report(
                expired_stats
            )
            expired_path = reports_dir / "expired_demand_report.txt"
            with open(expired_path, 'w') as f:
                f.write(expired_text)
            self.log_info(f"  + expired_demand_report.txt")
            
            print("\n" + expired_text)


from typing import Dict, Any

from ..core.base_component import BaseComponent

class ReportGenerator(BaseComponent):
    
    def generate_summary_report(self, breakdown: Dict[str, float], 
                               stats: Dict[str, Any],
                               expired_stats: Dict[str, Any]) -> str:
        lines = []
        lines.append("="*80)
        lines.append("OPTIMIZATION SUMMARY REPORT")
        lines.append("="*80)
        lines.append("")
        
        lines.append("SOLUTION STATUS")
        lines.append("-"*80)
        lines.append(f"  Status: {stats.get('status', 'N/A')}")
        lines.append(f"  Solve Status: {stats.get('solve_status', 'N/A')}")
        lines.append("")
        
        lines.append("OBJECTIVES")
        lines.append("-"*80)
        lines.append(f"  Total Cost: ${breakdown.get('total', 0):,.2f}")
        lines.append(f"  Fairness (ThetaStar): {stats.get('theta_star', 0):.6f}")
        lines.append("")
        
        lines.append("COST BREAKDOWN")
        lines.append("-"*80)
        lines.append(f"  1. Shipment Cost:      ${breakdown.get('shipment', 0):>15,.2f}")
        lines.append(f"  2. Procurement Cost:   ${breakdown.get('procurement', 0):>15,.2f}")
        lines.append(f"  3. Holding Cost:       ${breakdown.get('holding', 0):>15,.2f}")
        lines.append(f"  4. Wage Cost:          ${breakdown.get('wages', 0):>15,.2f}")
        lines.append(f"  5. Relocation Cost:    ${breakdown.get('relocation', 0):>15,.2f}")
        lines.append(f"  6. Backlog Penalty:    ${breakdown.get('backlog', 0):>15,.2f}")
        lines.append(f"  7. Late Service Cost:  ${breakdown.get('late', 0):>15,.2f}")
        lines.append("-"*80)
        lines.append(f"  TOTAL:                 ${breakdown.get('total', 0):>15,.2f}")
        lines.append("")
        
        lines.append("EXPIRED DEMAND")
        lines.append("-"*80)
        lines.append(f"  Total Expired: {expired_stats.get('total', 0):,.0f} units")
        if expired_stats.get('total', 0) > 0:
            lines.append(f"  Average (non-zero periods): {expired_stats.get('average', 0):,.0f} units")
            lines.append(f"  Maximum: {expired_stats.get('max', 0):,.0f} units (Period {expired_stats.get('max_period', 'N/A')})")
        lines.append("")
        
        lines.append("="*80)
        
        return "\n".join(lines)
    
    def generate_expired_demand_report(self, expired_stats: Dict[str, Any]) -> str:
        lines = []
        lines.append("="*80)
        lines.append("EXPIRED DEMAND DETAILED REPORT")
        lines.append("="*80)
        lines.append("")
        
        total = expired_stats.get('total', 0)
        lines.append(f"Total Demand Lost (Expired After Age 3): {total:,.0f} units")
        lines.append("")
        
        if 'by_period' in expired_stats and not expired_stats['by_period'].empty:
            lines.append("Expired Demand by Time Period:")
            lines.append("-"*40)
            
            for _, row in expired_stats['by_period'].iterrows():
                if row['Expired'] > 0:
                    lines.append(f"  Period {row['Period']:>3}: {row['Expired']:>10,.0f} units")
            
            lines.append("-"*40)
            if expired_stats.get('average', 0) > 0:
                lines.append(f"  Average (non-zero): {expired_stats['average']:>10,.0f} units")
                lines.append(f"  Maximum: {expired_stats['max']:>10,.0f} units (Period {expired_stats['max_period']})")
        else:
            lines.append("No expired demand data available.")
        
        lines.append("")
        lines.append("="*80)
        
        return "\n".join(lines)

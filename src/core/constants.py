
from enum import Enum
from pathlib import Path

class ModelStatus(Enum):
    NOT_SOLVED = "not_solved"
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    ERROR = "error"

class StageType(Enum):
    FAIRNESS = "fairness"
    COST = "cost"

RISK_LEVELS = ['L', 'M', 'H']

BACKLOG_AGES = [1, 2, 3]

DEFAULT_FAIRNESS_WEIGHT = 0.1
DEFAULT_FAIRNESS_EPSILON = 1e-6
DEFAULT_BIG_M = 10_000_000_000

ITEM_TO_CONFIG_KEY = {
    'food_clothing': 'backlog_p1',
    'nonfood_items_clothing': 'backlog_p2',
    'housing': 'backlog_p3',
    'medical': 'backlog_s1',
    'info_legal': 'backlog_s2'
}

CSV_FORMAT = "csv"
EXCEL_FORMAT = "xlsx"
JSON_FORMAT = "json"

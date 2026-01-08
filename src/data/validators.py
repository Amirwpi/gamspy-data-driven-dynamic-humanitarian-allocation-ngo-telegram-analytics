
import pandas as pd
from typing import List, Optional

class DataValidator:
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required_columns: List[str], 
                                  data_name: str) -> None:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(
                f"{data_name} missing required columns: {missing}"
            )
    
    @staticmethod
    def validate_positive_values(df: pd.DataFrame, columns: List[str], 
                                 data_name: str) -> None:
        for col in columns:
            if col in df.columns:
                if (df[col] < 0).any():
                    raise ValueError(
                        f"{data_name} contains negative values in column '{col}'"
                    )
    
    @staticmethod
    def validate_no_nulls(df: pd.DataFrame, columns: List[str], 
                         data_name: str) -> None:
        for col in columns:
            if col in df.columns:
                if df[col].isnull().any():
                    raise ValueError(
                        f"{data_name} contains null values in column '{col}'"
                    )

"""
Data Ingestion Module
Loads and cleans the patient data CSV file for the RAG system.
"""

import pandas as pd
import os
from pathlib import Path


def load_and_clean_data(data_path: str = None) -> pd.DataFrame:
    """
    Load the patient data CSV and clean column names.
    
    Args:
        data_path: Path to the CSV file (defaults to dataset folder)
        
    Returns:
        Cleaned DataFrame with standardized column names
    """
    if data_path is None:
        # Default to dataset folder in project root
        base_dir = Path(__file__).parent.parent
        full_path = base_dir / "dataset" / "Patient_data - Data.csv"
    else:
        # Use provided path
        full_path = Path(data_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Data file not found: {full_path}")
    
    # Load the CSV
    df = pd.read_csv(full_path)
    
    # Clean column names: remove spaces, keep underscores
    df.columns = df.columns.str.strip().str.replace(' ', '_')
    
    # Handle NaN values - convert to None for SQL compatibility
    # We'll handle this in SQL generation, but ensure consistent representation
    df = df.replace({pd.NA: None, 'NULL': None})
    
    print(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    
    return df


def load_schema_description(schema_path: str = None) -> pd.DataFrame:
    """
    Load the schema description CSV.
    
    Args:
        schema_path: Path to the schema description CSV (defaults to dataset folder)
        
    Returns:
        DataFrame with column descriptions
    """
    if schema_path is None:
        # Default to dataset folder in project root
        base_dir = Path(__file__).parent.parent
        full_path = base_dir / "dataset" / "Patient_data - Description.csv"
    else:
        # Use provided path
        full_path = Path(schema_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Schema file not found: {full_path}")
    
    schema_df = pd.read_csv(full_path)
    
    # Clean column names
    schema_df.columns = schema_df.columns.str.strip().str.replace(' ', '_')
    
    return schema_df


if __name__ == "__main__":
    # Test the ingestion
    df = load_and_clean_data()
    schema_df = load_schema_description()
    
    print("\nSchema Description:")
    print(schema_df.head())
    print(f"\nData shape: {df.shape}")
    print(f"\nFirst few rows:")
    print(df.head())

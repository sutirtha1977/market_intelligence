from typing import List, Optional, Set
import pandas as pd

# --------------------------------------------------------------------------
def validate_dataframe_columns(
    df: pd.DataFrame,
    required_cols: List[str],
    context: str = "Operation"
) -> None:
    """Validate DataFrame contains required columns.
    
    Args:
        df: DataFrame to validate
        required_cols: List of required column names
        context: Operation context for error message (e.g., "Symbol data import")
        
    Raises:
        ValueError: If required columns are missing
        
    Example:
        >>> validate_dataframe_columns(df, ['open', 'close'], context="Price data")
        # Raises ValueError if columns missing
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{context}: Expected DataFrame, got {type(df).__name__}")
    
    if df.empty:
        raise ValueError(f"{context}: DataFrame is empty")
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        available = list(df.columns)
        raise ValueError(
            f"{context}: Missing columns {missing_cols}. "
            f"Available columns: {available}"
        )

# --------------------------------------------------------------------------
def validate_asset_type(
    asset_type: str,
    valid_types: Optional[Set[str]] = None,
    context: str = "Operation"
) -> str:
    if not isinstance(asset_type, str):
        raise TypeError(
            f"{context}: Asset type must be string, got {type(asset_type).__name__}"
        )

    asset_type = asset_type.strip().lower()

    # 🔑 SINGLE SOURCE OF TRUTH
    if valid_types is None:
        try:
            from config.db_table import ASSET_TABLE_CONFIG
            valid_types = set(ASSET_TABLE_CONFIG.keys())
        except Exception as e:
            raise RuntimeError(
                f"{context}: Failed to load ASSET_TABLE_CONFIG | {e}"
            )

    if asset_type not in valid_types:
        raise ValueError(
            f"{context}: Invalid asset_type '{asset_type}'. "
            f"Valid options: {sorted(valid_types)}"
        )

    return asset_type

# --------------------------------------------------------------------------
def validate_connection(conn) -> None:
    """Validate database connection is open and usable.
    
    Args:
        conn: Connection object to validate
        
    Raises:
        RuntimeError: If connection not available or closed
        
    Example:
        >>> validate_connection(conn)
        # Raises RuntimeError if connection is None or closed
    """
    if conn is None:
        raise RuntimeError("Database connection not available (None)")
    
    if hasattr(conn, 'closed') and conn.closed:
        raise RuntimeError("Database connection is closed")
    
# --------------------------------------------------------------------------

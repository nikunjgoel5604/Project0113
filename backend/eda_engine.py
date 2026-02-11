import pandas as pd
import numpy as np


# ---------------------------------------------------
# CONVERT EVERYTHING JSON SAFE
# ---------------------------------------------------
def make_json_safe(obj):

    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]

    # numpy numbers → python numbers
    elif isinstance(obj, (np.integer,)):
        return int(obj)

    elif isinstance(obj, (np.floating,)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)

    # pandas NaN
    elif pd.isna(obj):
        return None

    return obj


# ---------------------------------------------------
# MAIN EDA FUNCTION
# ---------------------------------------------------
def run_eda(df):

    # BASIC INFO
    rows = int(len(df))
    columns = int(len(df.columns))
    column_names = list(df.columns)

    # DATA TYPES
    data_types = df.dtypes.astype(str).to_dict()

    # MISSING VALUES
    missing_count = df.isnull().sum().to_dict()

    missing_percent = (
        (df.isnull().sum() / len(df)) * 100
    ).round(2).to_dict()

    # NUMERIC SUMMARY
    numeric_summary = {}

    numeric_cols = df.select_dtypes(include="number").columns

    for col in numeric_cols:
        numeric_summary[col] = {
            "mean": df[col].mean(),
            "min": df[col].min(),
            "max": df[col].max(),
            "std": df[col].std()
        }

    # PREVIEW
    preview = df.head(5).to_dict(orient="records")

    result = {
        "rows": rows,
        "columns": columns,
        "column_names": column_names,
        "data_types": data_types,
        "missing_count": missing_count,
        "missing_percent": missing_percent,
        "numeric_summary": numeric_summary,
        "preview": preview
    }

    return make_json_safe(result)

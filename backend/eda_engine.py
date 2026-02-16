import pandas as pd
import numpy as np


# ------------------------
# CLEAN JSON (NaN FIX)
# ------------------------
def clean_json(data):

    if isinstance(data, dict):
        return {k: clean_json(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [clean_json(v) for v in data]

    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            return None
        return data

    return data


# ------------------------
# MAIN EDA FUNCTION
# ------------------------
def perform_eda(df):

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    overview = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols
    }

    data_quality = {
        "missing_values": df.isnull().sum().to_dict(),
        "duplicates": int(df.duplicated().sum())
    }

    statistics = {}
    if len(numeric_cols) > 0:
        statistics = df[numeric_cols].describe().to_dict()

    preview = df.head(5).fillna("").to_dict(orient="records")

    insights = [
        f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns.",
        f"{len(numeric_cols)} numeric columns detected.",
        f"{len(categorical_cols)} categorical columns detected.",
        f"{data_quality['duplicates']} duplicate rows found."
    ]

    result = {
        "overview": overview,
        "data_quality": data_quality,
        "statistics": statistics,
        "preview": preview,
        "insights": insights
    }

    return clean_json(result)

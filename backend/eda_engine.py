import pandas as pd
import numpy as np


# ---------------------------
# CLEAN JSON (Fix NaN issue)
# ---------------------------
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


# ---------------------------
# MAIN EDA FUNCTION
# ---------------------------
def perform_eda(df):

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    # OVERVIEW
    overview = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols
    }

    # DATA QUALITY
    data_quality = {
        "missing_values": df.isnull().sum().to_dict(),
        "duplicates": int(df.duplicated().sum())
    }

    # DESCRIPTIVE STATS
    if len(numeric_cols) > 0:
        statistics = df[numeric_cols].describe().to_dict()
    else:
        statistics = {}

    # PREVIEW
    preview = df.head(5).fillna("").to_dict(orient="records")

    # INSIGHTS
    insights = []

    if data_quality["duplicates"] > 0:
        insights.append(
            f"{data_quality['duplicates']} duplicate rows detected."
        )

    total_missing = df.isnull().sum().sum()

    if total_missing > 0:
        insights.append(
            f"{total_missing} missing values detected."
        )
    else:
        insights.append("No missing values found.")

    insights.append(
        f"{len(numeric_cols)} numeric columns available for analysis."
    )

    insights.append(
        f"{len(categorical_cols)} categorical columns available."
    )

    result = {
        "overview": overview,
        "data_quality": data_quality,
        "statistics": statistics,
        "preview": preview,
        "insights": insights
    }

    return clean_json(result)

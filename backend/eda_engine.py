import pandas as pd
import numpy as np


# ------------------------------------------------
# CLEAN JSON (NaN -> None for FastAPI response)
# ------------------------------------------------
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


# ------------------------------------------------
# MAIN EDA ENGINE
# ------------------------------------------------
def perform_eda(df):

    # ---------------------------
    # BASIC INFO
    # ---------------------------
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=np.number).columns.tolist()

    overview = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols
    }

    # ---------------------------
    # DATA QUALITY
    # ---------------------------
    missing_values = df.isnull().sum().to_dict()

    data_quality = {
        "missing_values": missing_values,
        "duplicates": int(df.duplicated().sum()),
        "unique_counts": df.nunique().to_dict()
    }

    # ---------------------------
    # DESCRIPTIVE STATISTICS
    # ---------------------------
    statistics = {}

    if len(numeric_cols) > 0:

        desc = df[numeric_cols].describe().to_dict()

        skewness = df[numeric_cols].skew().to_dict()
        kurtosis = df[numeric_cols].kurt().to_dict()

        statistics = {
            "describe": desc,
            "skewness": skewness,
            "kurtosis": kurtosis
        }

    # ---------------------------
    # CORRELATION MATRIX
    # ---------------------------
    correlation = {}

    if len(numeric_cols) > 1:
        correlation = df[numeric_cols].corr().to_dict()

    # ---------------------------
    # OUTLIER DETECTION (IQR)
    # ---------------------------
    outliers = {}

    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        outliers[col] = int(
            ((df[col] < lower) | (df[col] > upper)).sum()
        )

    # ---------------------------
    # DATA PREVIEW
    # ---------------------------
    preview = df.head(5).fillna("").to_dict(orient="records")

    # ---------------------------
    # AUTO INSIGHTS
    # ---------------------------
    insights = []

    insights.append(
        f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns."
    )

    if data_quality["duplicates"] > 0:
        insights.append(
            f"{data_quality['duplicates']} duplicate rows detected."
        )

    for col, val in missing_values.items():
        if val > 0:
            insights.append(f"{col} has {val} missing values.")

    for col, skew in statistics.get("skewness", {}).items():
        if abs(skew) > 1:
            insights.append(f"{col} is highly skewed.")

    # ---------------------------
    # FINAL RESULT
    # ---------------------------
    result = {
        "overview": overview,
        "data_quality": data_quality,
        "statistics": statistics,
        "correlation": correlation,
        "outliers": outliers,
        "preview": preview,
        "insights": insights
    }

    return clean_json(result)

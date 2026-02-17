import pandas as pd
import numpy as np


# =====================================================
# SAFE JSON CONVERSION (FASTAPI SAFE)
# =====================================================
def clean_json(obj):

    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [clean_json(v) for v in obj]

    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None

    return obj


# =====================================================
# DATE DETECTION
# Supports:
# dd-mm-yyyy
# dd/mm/yyyy
# yyyy-mm-dd
# mixed formats
# =====================================================
def try_parse_dates(df):

    for col in df.columns:

        if df[col].dtype == "object":

            try:
                parsed = pd.to_datetime(
                    df[col],
                    errors="coerce",
                    dayfirst=True
                )

                # convert only if majority parsed
                if parsed.notna().sum() > len(df) * 0.6:
                    df[col] = parsed

            except:
                pass

    return df


# =====================================================
# SAFE NUMERIC CONVERSION
# =====================================================
def safe_to_numeric(series):

    try:
        return pd.to_numeric(series, errors="coerce")
    except:
        return series


# =====================================================
# MISSING VALUE HANDLING (ETL)
# =====================================================
def handle_missing_values(df):

    for col in df.columns:

        # Try numeric conversion safely
        converted = safe_to_numeric(df[col])

        # If conversion successful → use numeric column
        if converted.notna().sum() > len(df) * 0.6:
            df[col] = converted

        # ---------- NUMERIC ----------
        if pd.api.types.is_numeric_dtype(df[col]):

            mean_val = df[col].mean()

            if not np.isnan(mean_val):
                df[col] = df[col].fillna(mean_val)

        # ---------- STRING ----------
        elif df[col].dtype == "object":

            mode_val = df[col].mode()

            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])

    return df


# =====================================================
# MAIN EDA FUNCTION
# =====================================================
def perform_eda(df):

    df = df.copy()

    # ---------- ETL ----------
    df = try_parse_dates(df)
    df = handle_missing_values(df)

    rows, columns = df.shape

    # ---------- COLUMN TYPES ----------
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    datetime_cols = df.select_dtypes(include="datetime").columns.tolist()

    # ---------- COLUMN PROFILE ----------
    column_profile = {}

    for col in df.columns:
        column_profile[col] = {
            "dtype": str(df[col].dtype),
            "unique_values": int(df[col].nunique()),
            "missing_values": int(df[col].isnull().sum())
        }

    # ---------- HISTOGRAM DATA ----------
    histograms = {}
    for col in numeric_cols:
        histograms[col] = (
            df[col]
            .dropna()
            .astype(float)
            .tolist()
        )

    # ---------- CATEGORY COUNTS ----------
    category_counts = {}
    for col in categorical_cols:
        category_counts[col] = (
            df[col]
            .astype(str)
            .value_counts()
            .to_dict()
        )

    # ---------- CORRELATION ----------
    correlation = {}
    numeric_df = df.select_dtypes(include=np.number)

    if not numeric_df.empty:
        correlation = (
            numeric_df
            .corr()
            .fillna(0)
            .to_dict()
        )

    # ---------- INSIGHTS ----------
    insights = [
        f"Dataset contains {rows} rows and {columns} columns",
        f"{len(numeric_cols)} numeric columns detected",
        f"{len(categorical_cols)} categorical columns detected"
    ]

    if datetime_cols:
        insights.append(
            f"{len(datetime_cols)} datetime columns detected"
        )

    # ---------- PREVIEW ----------
    preview = df.head(10).to_dict(orient="records")

    # ---------- FINAL RESPONSE ----------
    result = {

        "overview": {
            "rows": rows,
            "columns": columns,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols
        },

        "column_profile": column_profile,

        "data_quality": {
            "missing_values": df.isnull().sum().to_dict()
        },

        "preview": preview,

        "visualization": {
            "histograms": histograms,
            "category_counts": category_counts
        },

        "advanced_visualization": {
            "correlation": correlation
        },

        "insights": insights
    }

    return clean_json(result)

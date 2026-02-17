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
# Supports multiple formats automatically
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

                # Convert only if majority parsed
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
# HANDLE MISSING VALUES (ETL)
# =====================================================
def handle_missing_values(df):

    for col in df.columns:

        converted = safe_to_numeric(df[col])

        # convert to numeric if majority numeric
        if converted.notna().sum() > len(df) * 0.6:
            df[col] = converted

        # NUMERIC
        if pd.api.types.is_numeric_dtype(df[col]):

            mean_val = df[col].mean()

            if not np.isnan(mean_val):
                df[col] = df[col].fillna(mean_val)

        # STRING
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

    # ---------------- ETL ----------------
    df = try_parse_dates(df)
    df = handle_missing_values(df)

    rows, columns = df.shape

    # ---------------- COLUMN TYPES ----------------
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    datetime_cols = df.select_dtypes(include="datetime").columns.tolist()

    # ---------------- COLUMN PROFILE ----------------
    column_profile = {}

    for col in df.columns:
        column_profile[col] = {
            "dtype": str(df[col].dtype),
            "unique_values": int(df[col].nunique()),
            "missing_values": int(df[col].isnull().sum())
        }

    # ---------------- HISTOGRAM DATA ----------------
    histograms = {}

    for col in numeric_cols:

        values = df[col].dropna()

        if len(values) > 0:

            counts, bins = np.histogram(values, bins=20)

            histograms[col] = {
                "bins": bins[:-1].tolist(),
                "counts": counts.tolist()
            }

    # ---------------- CATEGORY COUNTS ----------------
    category_counts = {}

    for col in categorical_cols:
        category_counts[col] = (
            df[col]
            .astype(str)
            .value_counts()
            .head(20)       # performance safe
            .to_dict()
        )

    # ---------------- CORRELATION ----------------
    correlation = {}

    numeric_df = df.select_dtypes(include=np.number)

    if not numeric_df.empty:

        sample_df = numeric_df.sample(
            min(len(numeric_df), 1000),
            random_state=42
        )

        correlation = (
            sample_df
            .corr()
            .fillna(0)
            .to_dict()
        )

    # ---------------- DATA QUALITY ----------------
    missing_values = df.isnull().sum().to_dict()
    duplicates = int(df.duplicated().sum())

    # ---------------- INSIGHTS ----------------
    insights = [
        f"Dataset contains {rows} rows and {columns} columns",
        f"{len(numeric_cols)} numeric columns detected",
        f"{len(categorical_cols)} categorical columns detected"
    ]

    if datetime_cols:
        insights.append(
            f"{len(datetime_cols)} datetime columns detected"
        )

    # ---------------- PREVIEW ----------------
    preview = df.head(10).to_dict(orient="records")

    # ---------------- FINAL RESPONSE ----------------
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
            "missing_values": missing_values,
            "duplicates": duplicates
        },

        "preview": preview,

        "visualization": {
            "histograms": histograms,
            "category_counts": category_counts
        },

        "advanced_visualization": {
            "correlation": correlation,
            "missing_values": missing_values
        },

        "insights": insights
    }

    return clean_json(result)

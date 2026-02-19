import pandas as pd
import numpy as np
from io import StringIO


# =====================================================
# SAFE JSON CONVERSION
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
# =====================================================
def try_parse_dates(df):

    detected_dates = []

    for col in df.columns:

        if df[col].dtype == "object":

            parsed = pd.to_datetime(
                df[col],
                errors="coerce",
                dayfirst=True
            )

            if parsed.notna().sum() > len(df) * 0.6:
                df[col] = parsed
                detected_dates.append(col)

    return df, detected_dates


# =====================================================
# HANDLE MISSING VALUES + REPORT
# =====================================================
def handle_missing_values(df):

    handling_report = {}

    for col in df.columns:

        missing_before = int(df[col].isnull().sum())
        method = "No Missing"

        # Try numeric conversion
        converted = pd.to_numeric(df[col], errors="coerce")

        if converted.notna().sum() > len(df) * 0.6:
            df[col] = converted

        # ---------- NUMERIC ----------
        if pd.api.types.is_numeric_dtype(df[col]):

            mean_val = df[col].mean()

            if not np.isnan(mean_val):
                df[col] = df[col].fillna(mean_val)
                method = "Filled with Mean"

        # ---------- STRING ----------
        elif df[col].dtype == "object":

            mode_val = df[col].mode()

            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])
                method = "Filled with Mode"

        missing_after = int(df[col].isnull().sum())

        handling_report[col] = {
            "missing_before": missing_before,
            "missing_after": missing_after,
            "method": method
        }

    return df, handling_report


# =====================================================
# MAIN EDA FUNCTION
# =====================================================
def perform_eda(df):

    df = df.copy()

    rows, columns = df.shape

    # ================= RAW DATA STRUCTURE =================
    buffer = StringIO()
    df.info(buf=buffer)
    info_string = buffer.getvalue()

    nunique_data = df.nunique().to_dict()

    # ================= DATE DETECTION =================
    df, detected_dates = try_parse_dates(df)

    # ================= MISSING HANDLING =================
    df, handling_report = handle_missing_values(df)

    # ================= COLUMN TYPES =================
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    datetime_cols = df.select_dtypes(include="datetime").columns.tolist()

    # ================= VALUE COUNTS =================
    value_counts = {}

    for col in categorical_cols:
        value_counts[col] = (
            df[col]
            .astype(str)
            .value_counts()
            .to_dict()
        )

    # ================= HISTOGRAM =================
    histograms = {}

    for col in numeric_cols:
        values = df[col].dropna()

        if len(values) > 0:
            counts, bins = np.histogram(values, bins=20)

            histograms[col] = {
                "bins": bins[:-1].tolist(),
                "counts": counts.tolist()
            }

    # ================= CORRELATION =================
    correlation = {}

    numeric_df = df.select_dtypes(include=np.number)

    if not numeric_df.empty:
        correlation = (
            numeric_df
            .corr()
            .fillna(0)
            .to_dict()
        )

    # ================= DUPLICATES =================
    duplicates = int(df.duplicated().sum())

    # ================= PREVIEW =================
    preview = df.head(10).to_dict(orient="records")

    # ================= INSIGHTS =================
    insights = [
        f"Dataset contains {rows} rows and {columns} columns.",
        f"{len(numeric_cols)} Numeric Columns detected.",
        f"{len(categorical_cols)} Categorical Columns detected.",
        f"{len(datetime_cols)} Date Columns detected.",
        f"{duplicates} Duplicate rows found."
    ]

    # ================= FINAL RESPONSE =================
    result = {

        "overview": {
            "rows": rows,
            "columns": columns,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols
        },

        "dataset_info": info_string,

        "nunique": nunique_data,

        "missing_handling_process": handling_report,

        "value_counts": value_counts,

        "data_quality": {
            "duplicates": duplicates
        },

        "preview": preview,

        "visualization": {
            "histograms": histograms
        },

        "advanced_visualization": {
            "correlation": correlation
        },

        "insights": insights
    }

    return clean_json(result)

import pandas as pd
import numpy as np


# =============================
# SAFE JSON CLEANER
# =============================
def clean_json(obj):
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json(v) for v in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
    return obj


# =============================
# DATE DETECTION FUNCTION
# =============================
def try_parse_dates(df):

    for col in df.columns:

        if df[col].dtype == "object":
            try:
                parsed = pd.to_datetime(
                    df[col],
                    errors="coerce",
                    dayfirst=True
                )

                # if more than 60% values converted → date column
                if parsed.notna().sum() > len(df) * 0.6:
                    df[col] = parsed

            except:
                pass

    return df


# =============================
# MISSING VALUE HANDLING
# =============================
def handle_missing_values(df):

    for col in df.columns:

        if df[col].dtype in ["int64", "float64"]:
            df[col].fillna(df[col].mean(), inplace=True)

        elif df[col].dtype == "object":
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df[col].fillna(mode_val[0], inplace=True)

    return df


# =============================
# MAIN EDA FUNCTION
# =============================
def perform_eda(df):

    # ---------- DATE DETECTION ----------
    df = try_parse_dates(df)

    # ---------- MISSING VALUE HANDLING ----------
    def handle_missing_values(df):

    for col in df.columns:

        # TRY NUMERIC CONVERSION
        df[col] = pd.to_numeric(df[col], errors="ignore")

        # NUMERIC COLUMN
        if pd.api.types.is_numeric_dtype(df[col]):

            mean_val = df[col].mean()

            if not np.isnan(mean_val):
                df[col] = df[col].fillna(mean_val)

        # STRING COLUMN
        elif df[col].dtype == "object":

            mode_val = df[col].mode()

            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])

    return df



    # ---------- COLUMN PROFILE ----------
    column_profile = {}

    for col in df.columns:
        column_profile[col] = {
            "dtype": str(df[col].dtype),
            "unique_values": int(df[col].nunique()),
            "missing_values": int(df[col].isnull().sum())
        }


    # ---------- CATEGORY COUNTS ----------
    category_counts = {}

    for col in categorical_cols:
        category_counts[col] = (
            df[col]
            .astype(str)
            .value_counts()
            .to_dict()
        )


    # ---------- HISTOGRAM DATA ----------
    histograms = {}

    for col in numeric_cols:
        histograms[col] = (
            df[col]
            .dropna()
            .astype(float)
            .tolist()
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
    insights = []
    insights.append(
        f"Dataset contains {rows} rows and {columns} columns"
    )

    insights.append(
        f"{len(numeric_cols)} numeric columns detected"
    )

    insights.append(
        f"{len(categorical_cols)} categorical columns detected"
    )


    # ---------- FINAL OUTPUT ----------
    result = {

        "overview": {
            "rows": rows,
            "columns": columns,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols
        },

        "column_profile": column_profile,

        "preview": df.head(10)
        .to_dict(orient="records"),

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

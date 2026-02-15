import pandas as pd
import numpy as np


# =====================================================
# JSON SAFE CONVERSION
# =====================================================
def make_json_safe(obj):

    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]

    elif isinstance(obj, (np.integer,)):
        return int(obj)

    elif isinstance(obj, (np.floating,)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)

    elif pd.isna(obj):
        return None

    return obj


# =====================================================
# MAIN EDA FUNCTION
# =====================================================
def run_eda(df):

    total_rows = len(df)
    total_columns = len(df.columns)

    # =================================================
    # MODE DETECTION (HYBRID EDA)
    # =================================================
    SAMPLE_LIMIT = 50000
    SAMPLE_SIZE = 10000

    if total_rows > SAMPLE_LIMIT:
        mode = "sampled"
        df_analysis = df.sample(min(SAMPLE_SIZE, total_rows))
    else:
        mode = "full"
        df_analysis = df

    # =================================================
    # COLUMN TYPES
    # =================================================
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    # =================================================
    # OVERVIEW
    # =================================================
    overview = {
        "rows": total_rows,
        "columns": total_columns,
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(categorical_cols)
    }

    # =================================================
    # DATA QUALITY (ANALYST VIEW)
    # =================================================
    data_types = df.dtypes.astype(str).to_dict()

    missing_count = df.isnull().sum().to_dict()

    missing_percent = (
        (df.isnull().sum() / total_rows) * 100
    ).round(2).to_dict()

    unique_counts = df.nunique().to_dict()

    top_values = {}
    for col in categorical_cols:
        try:
            top_values[col] = df[col].value_counts().idxmax()
        except:
            top_values[col] = None

    data_quality = {
        "data_types": data_types,
        "missing_count": missing_count,
        "missing_percent": missing_percent,
        "unique_counts": unique_counts,
        "top_values": top_values
    }

    # =================================================
    # STATISTICS (DATA SCIENTIST VIEW)
    # =================================================
    numeric_summary = {}

    for col in numeric_cols:
        numeric_summary[col] = {
            "mean": df_analysis[col].mean(),
            "median": df_analysis[col].median(),
            "min": df_analysis[col].min(),
            "max": df_analysis[col].max(),
            "std": df_analysis[col].std()
        }

    # correlation only if multiple numeric columns
    if len(numeric_cols) > 1:
        correlation_matrix = (
            df_analysis[numeric_cols]
            .corr()
            .round(3)
            .to_dict()
        )
    else:
        correlation_matrix = {}

    statistics = {
        "numeric_summary": numeric_summary,
        "correlation_matrix": correlation_matrix
    }

    # =================================================
    # VISUALIZATION DATA (CHART READY)
    # =================================================
    categorical_distribution = {}

    for col in categorical_cols[:5]:
        categorical_distribution[col] = (
            df[col]
            .value_counts()
            .head(10)
            .to_dict()
        )

    visualization = {
        "categorical_distribution": categorical_distribution
    }

    # =================================================
    # AUTO INSIGHTS (PRODUCT LAYER)
    # =================================================
    insights = []

    insights.append(
        f"Dataset contains {total_rows} rows and {total_columns} columns."
    )

    missing_cols = [
        col for col, val in missing_count.items() if val > 0
    ]

    if missing_cols:
        insights.append(
            f"{len(missing_cols)} columns contain missing values."
        )

    if numeric_cols:
        insights.append(
            f"Dataset contains {len(numeric_cols)} numeric columns."
        )

    if categorical_cols:
        insights.append(
            f"Dataset contains {len(categorical_cols)} categorical columns."
        )

    if mode == "sampled":
        insights.append(
            "Large dataset detected. Analysis performed on sampled data for speed."
        )

    # =================================================
    # DATA PREVIEW
    # =================================================
    preview = df.head(5).to_dict(orient="records")

    # =================================================
    # FINAL RESULT
    # =================================================
    result = {
        "mode": mode,
        "overview": overview,
        "data_quality": data_quality,
        "statistics": statistics,
        "visualization": visualization,
        "insights": insights,
        "preview": preview
    }

    return make_json_safe(result)

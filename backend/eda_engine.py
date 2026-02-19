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
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


# =====================================================
# DATE DETECTION
# =====================================================
def try_parse_dates(df):
    detected_dates = []
    for col in df.columns:
        if df[col].dtype == "object":
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
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

        # NUMERIC → fill with median (more robust than mean)
        if pd.api.types.is_numeric_dtype(df[col]):
            if missing_before > 0:
                median_val = df[col].median()
                if not np.isnan(median_val):
                    df[col] = df[col].fillna(median_val)
                    method = "Filled with Median"

        # STRING → fill with mode
        elif df[col].dtype == "object":
            if missing_before > 0:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
                    method = "Filled with Mode"

        missing_after = int(df[col].isnull().sum())

        handling_report[col] = {
            "missing_before": missing_before,
            "missing_after":  missing_after,
            "method":         method
        }

    return df, handling_report


# =====================================================
# OUTLIER DETECTION (IQR Method)
# =====================================================
def detect_outliers(df, numeric_cols):
    outlier_report = {}

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue

        Q1  = series.quantile(0.25)
        Q3  = series.quantile(0.75)
        IQR = Q3 - Q1

        lower  = Q1 - 1.5 * IQR
        upper  = Q3 + 1.5 * IQR

        n_outliers = int(((series < lower) | (series > upper)).sum())

        outlier_report[col] = {
            "outliers_count": n_outliers,
            "lower_bound":    round(float(lower), 4),
            "upper_bound":    round(float(upper), 4),
            "Q1":             round(float(Q1), 4),
            "Q3":             round(float(Q3), 4),
            "IQR":            round(float(IQR), 4)
        }

    return outlier_report


# =====================================================
# STATISTICAL SUMMARY
# =====================================================
def statistical_summary(df, numeric_cols):
    if not numeric_cols:
        return {}

    desc = df[numeric_cols].describe().T

    summary = {}
    for col in numeric_cols:
        try:
            summary[col] = {
                "mean":   round(float(desc.loc[col, "mean"]),  4),
                "median": round(float(df[col].median()),        4),
                "std":    round(float(desc.loc[col, "std"]),   4),
                "min":    round(float(desc.loc[col, "min"]),   4),
                "max":    round(float(desc.loc[col, "max"]),   4),
                "25%":    round(float(desc.loc[col, "25%"]),   4),
                "75%":    round(float(desc.loc[col, "75%"]),   4),
                "skewness": round(float(df[col].skew()),       4),
                "kurtosis": round(float(df[col].kurtosis()),   4),
            }
        except Exception:
            pass

    return summary


# =====================================================
# SMART INSIGHTS GENERATOR
# =====================================================
def generate_insights(df, numeric_cols, categorical_cols, datetime_cols,
                       handling_report, outlier_report, duplicates):

    insights = []

    rows, cols = df.shape
    insights.append(f"Dataset has {rows:,} rows and {cols} columns.")

    if numeric_cols:
        insights.append(f"{len(numeric_cols)} numeric column(s) detected: {', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}.")

    if categorical_cols:
        insights.append(f"{len(categorical_cols)} categorical column(s) detected: {', '.join(categorical_cols[:5])}{'...' if len(categorical_cols) > 5 else ''}.")

    if datetime_cols:
        insights.append(f"Date columns auto-detected: {', '.join(datetime_cols)}.")

    if duplicates > 0:
        pct = round((duplicates / rows) * 100, 1)
        insights.append(f"⚠ {duplicates:,} duplicate rows found ({pct}% of dataset) — consider removing.")
    else:
        insights.append("✔ No duplicate rows found in dataset.")

    # Missing value insights
    missing_cols = [(c, v["missing_before"]) for c, v in handling_report.items() if v["missing_before"] > 0]
    if missing_cols:
        worst = max(missing_cols, key=lambda x: x[1])
        insights.append(f"⚠ {len(missing_cols)} column(s) had missing values. '{worst[0]}' had the most ({worst[1]:,} missing).")
    else:
        insights.append("✔ Dataset has no missing values — clean data!")

    # Outlier insights
    for col, info in outlier_report.items():
        if info["outliers_count"] > 0:
            insights.append(f"⚠ Outliers detected in '{col}': {info['outliers_count']} values outside [{info['lower_bound']}, {info['upper_bound']}].")

    # Skewness insights
    if numeric_cols:
        for col in numeric_cols:
            try:
                skew = float(df[col].skew())
                if abs(skew) > 1:
                    direction = "right (positive)" if skew > 0 else "left (negative)"
                    insights.append(f"'{col}' is heavily skewed {direction} (skew={round(skew, 2)}) — may need log transformation.")
            except Exception:
                pass

    # High cardinality
    for col in categorical_cols:
        n_unique = df[col].nunique()
        if n_unique > rows * 0.8:
            insights.append(f"'{col}' has very high cardinality ({n_unique} unique values) — likely an ID column.")

    # Constant column
    for col in df.columns:
        if df[col].nunique() == 1:
            insights.append(f"⚠ '{col}' has only 1 unique value — this column adds no information.")

    return insights


# =====================================================
# MAIN EDA FUNCTION
# =====================================================
def perform_eda(df):

    df = df.copy()
    rows, columns = df.shape

    # ===== RAW INFO (before cleaning) =====
    buffer = StringIO()
    df.info(buf=buffer)
    info_string = buffer.getvalue()

    nunique_data = df.nunique().to_dict()

    # ===== DATE DETECTION =====
    df, detected_dates = try_parse_dates(df)

    # ===== MISSING HANDLING =====
    df, handling_report = handle_missing_values(df)

    # ===== COLUMN TYPES =====
    numeric_cols     = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    datetime_cols    = df.select_dtypes(include="datetime").columns.tolist()

    # ===== STATISTICAL SUMMARY =====
    stats = statistical_summary(df, numeric_cols)

    # ===== OUTLIER DETECTION =====
    outlier_report = detect_outliers(df, numeric_cols)

    # ===== VALUE COUNTS =====
    value_counts = {}
    for col in categorical_cols:
        value_counts[col] = (
            df[col]
            .astype(str)
            .value_counts()
            .head(50)           # limit top 50
            .to_dict()
        )

    # ===== HISTOGRAMS =====
    histograms = {}
    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) > 0:
            counts, bins = np.histogram(values, bins=20)
            histograms[col] = {
                "bins":   bins[:-1].tolist(),
                "counts": counts.tolist()
            }

    # ===== CORRELATION =====
    correlation = {}
    numeric_df = df.select_dtypes(include=np.number)
    if len(numeric_df.columns) >= 2:
        correlation = (
            numeric_df
            .corr()
            .fillna(0)
            .to_dict()
        )

    # ===== DUPLICATES =====
    duplicates = int(df.duplicated().sum())

    # ===== PREVIEW =====
    preview = df.head(10).to_dict(orient="records")

    # ===== INSIGHTS =====
    insights = generate_insights(
        df, numeric_cols, categorical_cols, datetime_cols,
        handling_report, outlier_report, duplicates
    )

    # ===== FINAL RESPONSE =====
    result = {

        "overview": {
            "rows":               rows,
            "columns":            columns,
            "numeric_columns":    numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns":   datetime_cols
        },

        "dataset_info": info_string,
        "nunique":       nunique_data,

        "missing_handling_process": handling_report,

        "data_quality": {
            "duplicates":    duplicates,
            "outliers":      outlier_report
        },

        "statistics": stats,

        "value_counts": value_counts,

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

import pandas as pd
import numpy as np
from io import StringIO


# =====================================================
# SAFE JSON CONVERSION (IMPROVED)
# =====================================================
def clean_json(obj):
    """Recursively clean object for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, bool):
        return bool(obj)
    elif pd.isna(obj):
        return None
    return obj


# =====================================================
# DATE FORMAT DETECTION
# =====================================================
DATE_FORMATS = [
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y",
    "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y",
    "%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y",
    "%d-%b-%Y", "%d-%B-%Y", "%d %b %y",
    "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
]


def detect_date_format(series):
    sample = series.dropna().head(50).astype(str)
    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(sample, format=fmt, errors="coerce")
            if parsed.notna().sum() >= len(sample) * 0.8:
                return fmt
        except Exception:
            continue
    return None


def try_parse_dates(df):
    detected_dates  = []
    date_format_map = {}
    for col in df.columns:
        if df[col].dtype != "object":
            continue
        fmt = detect_date_format(df[col])
        if fmt:
            try:
                parsed = pd.to_datetime(df[col], format=fmt, errors="coerce")
                if parsed.notna().sum() > len(df) * 0.6:
                    df[col]              = parsed
                    detected_dates.append(col)
                    date_format_map[col] = fmt
            except Exception:
                try:
                    parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                    if parsed.notna().sum() > len(df) * 0.6:
                        df[col]              = parsed
                        detected_dates.append(col)
                        date_format_map[col] = "auto-detected"
                except Exception:
                    pass
    return df, detected_dates, date_format_map


# =====================================================
# DETERMINE COLUMN CATEGORY (IMPROVED)
# =====================================================
def get_col_category(series):
    """
    Decide if a column should be treated as Numeric or Categorical.
    Handles mixed types, booleans, etc.
    """
    # Check for boolean
    if series.dtype == bool:
        return "Categorical"

    # Check for numeric types
    if pd.api.types.is_numeric_dtype(series):
        return "Numeric"

    # Check if object column is actually numeric
    if series.dtype == "object":
        converted = pd.to_numeric(series, errors="coerce")
        if converted.notna().sum() > len(series) * 0.7:
            return "Numeric"

    return "Categorical"


# =====================================================
# CAPTURE FULL "BEFORE" SNAPSHOT (IMPROVED)
# =====================================================
def capture_before_snapshot(df):
    snapshot = {}
    total_rows = len(df)

    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        col_category  = get_col_category(df[col])
        fill_value    = None
        fill_strategy = "No Action Needed"

        # ── Pre-compute fill value ──
        if col_category == "Numeric":
            num_series = pd.to_numeric(df[col], errors="coerce") \
                         if df[col].dtype == "object" else df[col]
            if missing_count > 0:
                mean_val = num_series.mean()
                if mean_val is not None and not np.isnan(float(mean_val)):
                    fill_value    = round(float(mean_val), 4)
                    fill_strategy = f"Fill {missing_count} missing with Mean = {fill_value}"
                else:
                    fill_strategy = "Mean is NaN — cannot fill"

        elif col_category == "Categorical":
            str_series = df[col].astype(str).str.strip() if df[col].dtype == "object" else df[col].astype(str)
            if missing_count > 0:
                mode_vals = str_series[str_series != 'nan'].mode()
                if len(mode_vals) > 0:
                    fill_value    = str(mode_vals[0])
                    fill_strategy = f"Fill {missing_count} missing with Mode = '{fill_value}'"
                else:
                    fill_strategy = "No mode found — cannot fill"

        # Value counts BEFORE cleaning
        try:
            if df[col].dtype == "object":
                vc_before = df[col].str.strip().value_counts(dropna=False).head(10).to_dict()
            else:
                vc_before = df[col].value_counts(dropna=False).head(10).to_dict()
        except:
            vc_before = {}

        vc_before = {str(k): int(v) for k, v in vc_before.items()}

        snapshot[col] = {
            "col_type":      col_category,
            "missing_count": missing_count,
            "missing_pct":   round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0,
            "fill_value":    str(fill_value) if fill_value is not None else None,
            "fill_strategy": fill_strategy,
            "total_rows":    total_rows,
            "vc_before":     vc_before,
        }

    return snapshot


# =====================================================
# HANDLE MISSING VALUES (IMPROVED)
# =====================================================
def handle_missing_values(df):
    handling_report = {}

    # ── Capture BEFORE state ──
    before_snapshot = capture_before_snapshot(df)

    for col in df.columns:
        missing_before = int(df[col].isnull().sum())
        method         = "No Missing"

        # Convert object → numeric where appropriate
        if df[col].dtype == "object":
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() > len(df) * 0.7:
                df[col] = converted

        # ══════════════════════════════════════════
        # NUMERIC → fill with MEAN
        # ══════════════════════════════════════════
        if pd.api.types.is_numeric_dtype(df[col]):
            if missing_before > 0:
                mean_val = df[col].mean()
                if not np.isnan(mean_val):
                    fill_val = round(float(mean_val), 4)
                    df[col].fillna(fill_val, inplace=True)
                    method = f"Filled with Mean ({fill_val})"
                else:
                    method = "Mean is NaN — Left Empty"

        # ══════════════════════════════════════════
        # CATEGORICAL (STRING) → strip + fill with MODE
        # ══════════════════════════════════════════
        elif df[col].dtype == "object":
            # Step 1: Remove leading/trailing spaces
            df[col] = df[col].str.strip()

            if missing_before > 0:
                # Step 2: Find most frequent value
                mode_series = df[col].mode(dropna=True)
                if len(mode_series) > 0:
                    mode_value = mode_series[0]
                    # Step 3: Fill missing with mode
                    df[col].fillna(mode_value, inplace=True)
                    method = f"Filled with Mode ('{mode_value}')"
                else:
                    method = "No Mode Found — Left Empty"

        missing_after = int(df[col].isnull().sum())

        # Value counts AFTER cleaning
        try:
            if df[col].dtype == "object":
                vc_after = df[col].value_counts(dropna=False).head(10).to_dict()
            else:
                vc_after = df[col].value_counts(dropna=False).head(10).to_dict()
        except:
            vc_after = {}

        vc_after = {str(k): int(v) for k, v in vc_after.items()}

        handling_report[col] = {
            "missing_before": missing_before,
            "missing_after":  missing_after,
            "method":         method,
            "col_type":       before_snapshot[col]["col_type"],
            "fill_value":     before_snapshot[col]["fill_value"],
            "fill_strategy":  before_snapshot[col]["fill_strategy"],
            "missing_pct":    before_snapshot[col]["missing_pct"],
            "vc_before":      before_snapshot[col]["vc_before"],
            "vc_after":       vc_after,
        }

    return df, handling_report, before_snapshot


# =====================================================
# OUTLIER DETECTION — IQR Method
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
        lower      = Q1 - 1.5 * IQR
        upper      = Q3 + 1.5 * IQR
        n_outliers = int(((series < lower) | (series > upper)).sum())
        outlier_report[col] = {
            "outliers_count": n_outliers,
            "lower_bound":    round(float(lower), 4),
            "upper_bound":    round(float(upper), 4),
            "Q1":             round(float(Q1),    4),
            "Q3":             round(float(Q3),    4),
            "IQR":            round(float(IQR),   4),
        }
    return outlier_report


# =====================================================
# STATISTICAL SUMMARY
# =====================================================
def statistical_summary(df, numeric_cols):
    if not numeric_cols:
        return {}

    summary = {}
    for col in numeric_cols:
        try:
            s = df[col]
            summary[col] = {
                "mean":     round(float(s.mean()), 4),
                "median":   round(float(s.median()), 4),
                "std":      round(float(s.std()), 4),
                "min":      round(float(s.min()), 4),
                "max":      round(float(s.max()), 4),
                "25%":      round(float(s.quantile(0.25)), 4),
                "75%":      round(float(s.quantile(0.75)), 4),
                "skewness": round(float(s.skew()), 4),
                "kurtosis": round(float(s.kurtosis()), 4),
            }
        except Exception as e:
            print(f"Error computing stats for {col}: {e}")
            pass
    return summary


# =====================================================
# SMART INSIGHTS GENERATOR (IMPROVED)
# =====================================================
def generate_insights(df, numeric_cols, categorical_cols, datetime_cols,
                       handling_report, outlier_report, duplicates, date_format_map):
    insights = []
    rows, cols = df.shape

    insights.append(f"📊 Dataset: {rows:,} rows × {cols} columns")

    if numeric_cols:
        num_str = ", ".join(numeric_cols[:5])
        if len(numeric_cols) > 5:
            num_str += f", +{len(numeric_cols)-5} more"
        insights.append(f"🔢 {len(numeric_cols)} numeric column(s): {num_str}")

    if categorical_cols:
        cat_str = ", ".join(categorical_cols[:5])
        if len(categorical_cols) > 5:
            cat_str += f", +{len(categorical_cols)-5} more"
        insights.append(f"📝 {len(categorical_cols)} categorical column(s): {cat_str}")

    if datetime_cols:
        insights.append(f"📅 {len(datetime_cols)} datetime column(s) detected")
    else:
        insights.append("✔ No date/time columns detected")

    if duplicates > 0:
        pct = round((duplicates / rows) * 100, 1) if rows > 0 else 0
        insights.append(f"⚠️ Found {duplicates:,} duplicate rows ({pct}% of dataset)")
    else:
        insights.append("✔ No duplicate rows found")

    missing_cols = [(c, v["missing_before"]) for c, v in handling_report.items() if v["missing_before"] > 0]
    if missing_cols:
        worst = max(missing_cols, key=lambda x: x[1])
        insights.append(f"⚠️ {len(missing_cols)} column(s) had missing values (max: {worst[0]} with {worst[1]:,})")
    else:
        insights.append("✔ Dataset is clean — no missing values!")

    if outlier_report:
        outlier_cols = [c for c, v in outlier_report.items() if v["outliers_count"] > 0]
        if outlier_cols:
            insights.append(f"⚠️ Outliers detected in {len(outlier_cols)} numeric column(s)")

    for col in numeric_cols:
        try:
            skew = float(df[col].skew())
            if abs(skew) > 1.5:
                direction = "right (positive skew)" if skew > 0 else "left (negative skew)"
                insights.append(f"↗️ '{col}' is heavily skewed {direction}")
        except:
            pass

    for col in categorical_cols:
        n_unique = df[col].nunique()
        if n_unique > rows * 0.8 and rows > 0:
            insights.append(f"🔑 '{col}' has very high cardinality ({n_unique} unique) — likely an ID column")

    for col in df.columns:
        if df[col].nunique() == 1:
            insights.append(f"⚠️ '{col}' has only 1 unique value — adds no information")

    return insights


# =====================================================
# MAIN EDA FUNCTION (IMPROVED)
# =====================================================
def perform_eda(df):
    """
    Perform complete EDA on a DataFrame
    Returns JSON-safe dictionary
    """

    # Validate input
    if df is None or len(df) == 0:
        return {"error": "Empty DataFrame"}

    df = df.copy()
    rows, columns = df.shape

    # ── Raw df.info() ──
    buffer = StringIO()
    df.info(buf=buffer)
    info_string = buffer.getvalue()

    nunique_data = df.nunique().to_dict()

    # Step 1 — Date Detection
    df, detected_dates, date_format_map = try_parse_dates(df)

    # Step 2 — Missing Value Handling
    df, handling_report, before_snapshot = handle_missing_values(df)

    # Step 3 — Column Types
    numeric_cols     = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    datetime_cols    = df.select_dtypes(include="datetime").columns.tolist()

    # Step 4 — Statistical Summary
    stats = statistical_summary(df, numeric_cols)

    # Step 5 — Outlier Detection
    outlier_report = detect_outliers(df, numeric_cols)

    # Step 6 — Value Counts
    value_counts = {}
    for col in categorical_cols:
        try:
            value_counts[col] = df[col].astype(str).value_counts().head(50).to_dict()
        except:
            value_counts[col] = {}

    # Step 7 — Histograms (for numeric columns)
    histograms = {}
    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) > 0:
            counts, bins = np.histogram(values, bins=20)
            histograms[col] = {
                "bins": bins[:-1].tolist(),
                "counts": counts.tolist()
            }

    # Step 8 — Correlation
    correlation = {}
    numeric_df  = df.select_dtypes(include=np.number)
    if len(numeric_df.columns) >= 2:
        correlation = numeric_df.corr().fillna(0).to_dict()

    # Step 9 — Duplicates
    duplicates = int(df.duplicated().sum())

    # Step 10 — Preview (first 10 rows)
    preview = df.head(10).to_dict(orient="records")

    # Step 11 — Insights
    insights = generate_insights(
        df, numeric_cols, categorical_cols, datetime_cols,
        handling_report, outlier_report, duplicates, date_format_map
    )

    # ── Final response ──
    result = {
        "overview": {
            "rows":                rows,
            "columns":             columns,
            "numeric_columns":     numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns":    datetime_cols,
            "date_formats":        date_format_map,
        },

        "dataset_info":             info_string,
        "nunique":                  nunique_data,
        "missing_handling_process": handling_report,

        "data_quality": {
            "duplicates": duplicates,
            "outliers":   outlier_report,
        },

        "statistics":   stats,
        "value_counts": value_counts,
        "preview":      preview,

        "visualization": {
            "histograms": histograms
        },

        "advanced_visualization": {
            "correlation": correlation
        },

        "insights": insights,
    }

    return clean_json(result)

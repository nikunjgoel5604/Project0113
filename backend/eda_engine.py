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
# DATE FORMAT DETECTION
# Supports all common formats:
#   ISO 8601  → YYYY-MM-DD (international standard)
#   DMY       → DD/MM/YYYY (India, UK, Australia)
#   MDY       → MM/DD/YYYY (USA)
#   Textual   → 19 Feb 2025, February 19 2025, etc.
# =====================================================
DATE_FORMATS = [
    # ── ISO 8601 — International Standard ──
    "%Y-%m-%d",           # 2025-02-19
    "%Y/%m/%d",           # 2025/02/19
    "%Y.%m.%d",           # 2025.02.19

    # ── DMY — India, UK, Australia ──
    "%d/%m/%Y",           # 19/02/2025
    "%d-%m-%Y",           # 19-02-2025
    "%d.%m.%Y",           # 19.02.2025
    "%d/%m/%y",           # 19/02/25
    "%d-%m-%y",           # 19-02-25

    # ── MDY — United States ──
    "%m/%d/%Y",           # 02/19/2025
    "%m-%d-%Y",           # 02-19-2025
    "%m/%d/%y",           # 02/19/25

    # ── Textual Formats ──
    "%d %b %Y",           # 19 Feb 2025
    "%d %B %Y",           # 19 February 2025
    "%B %d, %Y",          # February 19, 2025
    "%b %d, %Y",          # Feb 19, 2025
    "%d-%b-%Y",           # 19-Feb-2025
    "%d-%B-%Y",           # 19-February-2025
    "%d %b %y",           # 19 Feb 25

    # ── With Time ──
    "%Y-%m-%d %H:%M:%S",  # 2025-02-19 14:30:00
    "%d/%m/%Y %H:%M:%S",  # 19/02/2025 14:30:00
    "%m/%d/%Y %H:%M:%S",  # 02/19/2025 14:30:00
    "%Y-%m-%dT%H:%M:%S",  # 2025-02-19T14:30:00  (ISO with T)
]


def detect_date_format(series):
    """
    Try each known date format against a sample of the column.
    Returns the matching format string, or None if no match found.
    """
    sample = series.dropna().head(50).astype(str)

    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(sample, format=fmt, errors="coerce")
            # If 80%+ of the sample parses → this format matches
            if parsed.notna().sum() >= len(sample) * 0.8:
                return fmt
        except Exception:
            continue

    return None


def try_parse_dates(df):
    """
    Auto-detect and convert date columns.
    Returns updated df, list of detected date columns,
    and a map of {column: format_detected}.
    """
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
                # Fallback: pandas auto-inference
                try:
                    parsed = pd.to_datetime(
                        df[col], infer_datetime_format=True, errors="coerce"
                    )
                    if parsed.notna().sum() > len(df) * 0.6:
                        df[col]              = parsed
                        detected_dates.append(col)
                        date_format_map[col] = "auto-detected"
                except Exception:
                    pass

    return df, detected_dates, date_format_map


# =====================================================
# HANDLE MISSING VALUES
#
#  NUMERIC  columns → fillna with MEAN
#  STRING   columns → strip spaces first, fillna with MODE
# =====================================================
def handle_missing_values(df):
    handling_report = {}

    for col in df.columns:

        missing_before = int(df[col].isnull().sum())
        method         = "No Missing"

        # ── Try converting object column to numeric ──
        if df[col].dtype == "object":
            converted = pd.to_numeric(df[col], errors="coerce")
            # Only convert if majority are actually numeric
            if converted.notna().sum() > len(df) * 0.6:
                df[col] = converted

        # ════════════════════════════════════════════
        # CASE 1 — NUMERIC → Fill with MEAN
        # ════════════════════════════════════════════
        if pd.api.types.is_numeric_dtype(df[col]):

            if missing_before > 0:
                mean_val = df[col].mean()

                if not np.isnan(mean_val):
                    # Using the correct syntax as specified
                    df[col].fillna(df[col].mean(), inplace=True)
                    method = f"Filled with Mean ({round(mean_val, 4)})"
                else:
                    method = "Mean is NaN — Left Empty"

        # ════════════════════════════════════════════
        # CASE 2 — STRING → Strip spaces + Fill with MODE
        # ════════════════════════════════════════════
        elif df[col].dtype == "object":

            # Step 1: Remove unwanted leading/trailing spaces
            df[col] = df[col].str.strip()

            if missing_before > 0:
                # Step 2: Frequency check — find most frequent value
                mode_series = df[col].mode(dropna=True)

                if len(mode_series) > 0:
                    mode_value = mode_series[0]
                    # Step 3: Replace missing values with mode
                    df[col].fillna(mode_value, inplace=True)
                    method = f"Filled with Mode ('{mode_value}')"
                else:
                    method = "No Mode Found — Left Empty"

        missing_after = int(df[col].isnull().sum())

        handling_report[col] = {
            "missing_before": missing_before,
            "missing_after":  missing_after,
            "method":         method
        }

    return df, handling_report


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

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        n_outliers = int(((series < lower) | (series > upper)).sum())

        outlier_report[col] = {
            "outliers_count": n_outliers,
            "lower_bound":    round(float(lower), 4),
            "upper_bound":    round(float(upper), 4),
            "Q1":             round(float(Q1),    4),
            "Q3":             round(float(Q3),    4),
            "IQR":            round(float(IQR),   4)
        }

    return outlier_report


# =====================================================
# STATISTICAL SUMMARY
# =====================================================
def statistical_summary(df, numeric_cols):
    if not numeric_cols:
        return {}

    desc    = df[numeric_cols].describe().T
    summary = {}

    for col in numeric_cols:
        try:
            summary[col] = {
                "mean":     round(float(desc.loc[col, "mean"]),  4),
                "median":   round(float(df[col].median()),        4),
                "std":      round(float(desc.loc[col, "std"]),   4),
                "min":      round(float(desc.loc[col, "min"]),   4),
                "max":      round(float(desc.loc[col, "max"]),   4),
                "25%":      round(float(desc.loc[col, "25%"]),   4),
                "75%":      round(float(desc.loc[col, "75%"]),   4),
                "skewness": round(float(df[col].skew()),         4),
                "kurtosis": round(float(df[col].kurtosis()),     4),
            }
        except Exception:
            pass

    return summary


# =====================================================
# SMART INSIGHTS GENERATOR
# =====================================================
def generate_insights(df, numeric_cols, categorical_cols, datetime_cols,
                       handling_report, outlier_report, duplicates,
                       date_format_map):

    insights = []
    rows, cols = df.shape

    insights.append(f"Dataset has {rows:,} rows and {cols} columns.")

    if numeric_cols:
        insights.append(
            f"{len(numeric_cols)} numeric column(s) detected: "
            f"{', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}."
        )

    if categorical_cols:
        insights.append(
            f"{len(categorical_cols)} categorical column(s) detected: "
            f"{', '.join(categorical_cols[:5])}{'...' if len(categorical_cols) > 5 else ''}."
        )

    # ── Date format insights ──
    if datetime_cols:
        for col in datetime_cols:
            fmt = date_format_map.get(col, "unknown")
            # Make format human-readable
            fmt_readable = {
                "%Y-%m-%d":           "ISO 8601 (YYYY-MM-DD) — International Standard",
                "%d/%m/%Y":           "DMY (DD/MM/YYYY) — India / UK / Australia",
                "%m/%d/%Y":           "MDY (MM/DD/YYYY) — United States",
                "%d-%m-%Y":           "DMY with hyphens (DD-MM-YYYY)",
                "%d.%m.%Y":           "DMY with dots (DD.MM.YYYY)",
                "%Y/%m/%d":           "ISO variant (YYYY/MM/DD)",
                "%d %b %Y":           "Textual (DD Mon YYYY) — e.g. 19 Feb 2025",
                "%d %B %Y":           "Textual (DD Month YYYY) — e.g. 19 February 2025",
                "%B %d, %Y":          "Textual (Month DD, YYYY) — e.g. February 19, 2025",
                "%Y-%m-%d %H:%M:%S":  "ISO 8601 with Time (YYYY-MM-DD HH:MM:SS)",
                "auto-detected":      "Auto-detected by pandas",
            }.get(fmt, fmt)

            insights.append(
                f"Date column '{col}' detected — Format: {fmt_readable}."
            )
    else:
        insights.append("No date columns detected in dataset.")

    # ── Duplicates ──
    if duplicates > 0:
        pct = round((duplicates / rows) * 100, 1)
        insights.append(
            f"⚠ {duplicates:,} duplicate rows found ({pct}% of dataset) — consider removing."
        )
    else:
        insights.append("✔ No duplicate rows found.")

    # ── Missing value summary ──
    missing_cols = [
        (c, v["missing_before"])
        for c, v in handling_report.items()
        if v["missing_before"] > 0
    ]
    if missing_cols:
        worst = max(missing_cols, key=lambda x: x[1])
        insights.append(
            f"⚠ {len(missing_cols)} column(s) had missing values. "
            f"'{worst[0]}' had the most ({worst[1]:,} missing). All filled automatically."
        )
    else:
        insights.append("✔ Dataset has no missing values — clean data!")

    # ── Per-column missing fill details ──
    for col, info in handling_report.items():
        if info["missing_before"] > 0:
            insights.append(
                f"  → '{col}': {info['missing_before']} missing filled. {info['method']}."
            )

    # ── Outlier insights ──
    for col, info in outlier_report.items():
        if info["outliers_count"] > 0:
            insights.append(
                f"⚠ Outliers in '{col}': {info['outliers_count']} values outside "
                f"[{info['lower_bound']}, {info['upper_bound']}] (IQR method)."
            )

    # ── Skewness insights ──
    for col in numeric_cols:
        try:
            skew = float(df[col].skew())
            if abs(skew) > 1:
                direction = "right (positive)" if skew > 0 else "left (negative)"
                insights.append(
                    f"'{col}' is heavily skewed {direction} "
                    f"(skew={round(skew, 2)}) — consider log transformation."
                )
        except Exception:
            pass

    # ── High cardinality ──
    for col in categorical_cols:
        n_unique = df[col].nunique()
        if n_unique > rows * 0.8:
            insights.append(
                f"'{col}' has very high cardinality ({n_unique} unique values) — likely an ID column."
            )

    # ── Constant columns ──
    for col in df.columns:
        if df[col].nunique() == 1:
            insights.append(
                f"⚠ '{col}' has only 1 unique value — adds no predictive information."
            )

    return insights


# =====================================================
# MAIN EDA FUNCTION
# =====================================================
def perform_eda(df):

    df = df.copy()
    rows, columns = df.shape

    # ── Raw df.info() captured before cleaning ──
    buffer = StringIO()
    df.info(buf=buffer)
    info_string = buffer.getvalue()

    nunique_data = df.nunique().to_dict()

    # ── Step 1: Date Detection ──
    df, detected_dates, date_format_map = try_parse_dates(df)

    # ── Step 2: Missing Value Handling ──
    df, handling_report = handle_missing_values(df)

    # ── Step 3: Column Type Classification ──
    numeric_cols     = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    datetime_cols    = df.select_dtypes(include="datetime").columns.tolist()

    # ── Step 4: Statistical Summary ──
    stats = statistical_summary(df, numeric_cols)

    # ── Step 5: Outlier Detection ──
    outlier_report = detect_outliers(df, numeric_cols)

    # ── Step 6: Value Counts ──
    value_counts = {}
    for col in categorical_cols:
        value_counts[col] = (
            df[col]
            .astype(str)
            .value_counts()
            .head(50)
            .to_dict()
        )

    # ── Step 7: Histograms ──
    histograms = {}
    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) > 0:
            counts, bins = np.histogram(values, bins=20)
            histograms[col] = {
                "bins":   bins[:-1].tolist(),
                "counts": counts.tolist()
            }

    # ── Step 8: Correlation Matrix ──
    correlation = {}
    numeric_df  = df.select_dtypes(include=np.number)
    if len(numeric_df.columns) >= 2:
        correlation = (
            numeric_df
            .corr()
            .fillna(0)
            .to_dict()
        )

    # ── Step 9: Duplicates ──
    duplicates = int(df.duplicated().sum())

    # ── Step 10: Preview ──
    preview = df.head(10).to_dict(orient="records")

    # ── Step 11: Insights ──
    insights = generate_insights(
        df, numeric_cols, categorical_cols, datetime_cols,
        handling_report, outlier_report, duplicates,
        date_format_map
    )

    # ── Final Response Object ──
    result = {

        "overview": {
            "rows":                rows,
            "columns":             columns,
            "numeric_columns":     numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns":    datetime_cols,
            "date_formats":        date_format_map
        },

        "dataset_info":             info_string,
        "nunique":                  nunique_data,
        "missing_handling_process": handling_report,

        "data_quality": {
            "duplicates": duplicates,
            "outliers":   outlier_report
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

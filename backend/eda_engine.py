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
# DETERMINE COLUMN CATEGORY
# Returns: "Numeric" | "Categorical"
# =====================================================
def get_col_category(series):
    """
    Decide if a column should be treated as Numeric or Categorical.
    Even if dtype is object, check if values are mostly numeric.
    """
    if pd.api.types.is_numeric_dtype(series):
        return "Numeric"

    if series.dtype == "object":
        converted = pd.to_numeric(series, errors="coerce")
        if converted.notna().sum() > len(series) * 0.6:
            return "Numeric"

    return "Categorical"


# =====================================================
# CAPTURE FULL "BEFORE" SNAPSHOT
# Captures missing state + what fill value WILL be used
# for EVERY column — both Numeric and Categorical
# =====================================================
def capture_before_snapshot(df):
    snapshot = {}
    total_rows = len(df)

    for col in df.columns:

        missing_count = int(df[col].isnull().sum())
        col_category  = get_col_category(df[col])
        fill_value    = None
        fill_strategy = "No Action Needed"

        # ── Pre-compute fill value so we show it BEFORE cleaning ──
        if col_category == "Numeric":
            # Work on numeric version of the column
            num_series = pd.to_numeric(df[col], errors="coerce") \
                         if df[col].dtype == "object" else df[col]
            if missing_count > 0:
                mean_val = num_series.mean()
                if mean_val is not None and not np.isnan(float(mean_val)):
                    fill_value    = round(float(mean_val), 4)
                    fill_strategy = f"Will fill {missing_count} missing with Mean = {fill_value}"
                else:
                    fill_strategy = "Mean is NaN — cannot fill"

        elif col_category == "Categorical":
            str_series = df[col].str.strip() if df[col].dtype == "object" else df[col].astype(str)
            if missing_count > 0:
                mode_vals = str_series.mode(dropna=True)
                if len(mode_vals) > 0:
                    fill_value    = str(mode_vals[0])
                    fill_strategy = f"Will fill {missing_count} missing with Mode = '{fill_value}'"
                else:
                    fill_strategy = "No mode found — cannot fill"

        # Value counts BEFORE cleaning (top 10 for display)
        if df[col].dtype == "object":
            vc_before = df[col].str.strip().value_counts(dropna=False).head(10).to_dict()
        else:
            vc_before = df[col].value_counts(dropna=False).head(10).to_dict()

        # Convert keys to string for JSON safety
        vc_before = {str(k): int(v) for k, v in vc_before.items()}

        snapshot[col] = {
            "col_type":      col_category,
            "missing_count": missing_count,
            "missing_pct":   round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0,
            "fill_value":    str(fill_value) if fill_value is not None else None,
            "fill_strategy": fill_strategy,
            "total_rows":    total_rows,
            "vc_before":     vc_before,   # value distribution BEFORE
        }

    return snapshot


# =====================================================
# HANDLE MISSING VALUES
# NUMERIC  → fillna with MEAN
# STRING   → strip spaces, fillna with MODE
# Returns: cleaned df + detailed report + before snapshot
# =====================================================
def handle_missing_values(df):
    handling_report = {}

    # ── Capture BEFORE state first ──
    before_snapshot = capture_before_snapshot(df)

    for col in df.columns:

        missing_before = int(df[col].isnull().sum())
        method         = "No Missing"

        # Convert object → numeric where appropriate
        if df[col].dtype == "object":
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() > len(df) * 0.6:
                df[col] = converted

        # ══════════════════════════════════════════
        # NUMERIC → fill with MEAN
        # ══════════════════════════════════════════
        if pd.api.types.is_numeric_dtype(df[col]):
            if missing_before > 0:
                mean_val = df[col].mean()
                if not np.isnan(mean_val):
                    df[col].fillna(df[col].mean(), inplace=True)
                    method = f"Filled with Mean ({round(float(mean_val), 4)})"
                else:
                    method = "Mean is NaN — Left Empty"

        # ══════════════════════════════════════════
        # CATEGORICAL (STRING) → strip + fill with MODE
        # ══════════════════════════════════════════
        elif df[col].dtype == "object":
            # Step 1: Remove unwanted leading/trailing spaces
            df[col] = df[col].str.strip()

            if missing_before > 0:
                # Step 2: Find most frequent value (mode)
                mode_series = df[col].mode(dropna=True)
                if len(mode_series) > 0:
                    mode_value = mode_series[0]
                    # Step 3: Fill missing with mode
                    df[col].fillna(mode_value, inplace=True)
                    method = f"Filled with Mode ('{mode_value}')"
                else:
                    method = "No Mode Found — Left Empty"

        missing_after = int(df[col].isnull().sum())

        # Value counts AFTER cleaning (top 10 for display)
        if df[col].dtype == "object":
            vc_after = df[col].value_counts(dropna=False).head(10).to_dict()
        else:
            vc_after = df[col].value_counts(dropna=False).head(10).to_dict()
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
    desc    = df[numeric_cols].describe().T
    summary = {}
    for col in numeric_cols:
        try:
            summary[col] = {
                "mean":     round(float(desc.loc[col, "mean"]), 4),
                "median":   round(float(df[col].median()),      4),
                "std":      round(float(desc.loc[col, "std"]),  4),
                "min":      round(float(desc.loc[col, "min"]),  4),
                "max":      round(float(desc.loc[col, "max"]),  4),
                "25%":      round(float(desc.loc[col, "25%"]),  4),
                "75%":      round(float(desc.loc[col, "75%"]),  4),
                "skewness": round(float(df[col].skew()),        4),
                "kurtosis": round(float(df[col].kurtosis()),    4),
            }
        except Exception:
            pass
    return summary


# =====================================================
# BUILD BEFORE/AFTER COMPARISON TABLE
# Powers the toggle button in the frontend
# =====================================================
def build_before_after_table(df_original_rows, handling_report, before_snapshot):
    """
    Returns a list of dicts — one per column that had missing values.
    Each dict contains the full before and after picture.
    """
    rows = df_original_rows
    table = []

    for col, info in handling_report.items():
        snap = before_snapshot.get(col, {})

        # Only include columns that HAD missing values (cleaner output)
        # But still include all for the full report — filter in JS
        table.append({
            "column":          col,
            "col_type":        info.get("col_type", "—"),
            "total_rows":      rows,

            # ── BEFORE ──
            "missing_before":  info.get("missing_before", 0),
            "missing_pct":     snap.get("missing_pct", 0.0),
            "fill_strategy":   snap.get("fill_strategy", "No Action"),
            "fill_value":      snap.get("fill_value", None),
            "vc_before":       snap.get("vc_before", {}),

            # ── AFTER ──
            "method_applied":  info.get("method", "—"),
            "missing_after":   info.get("missing_after", 0),
            "vc_after":        info.get("vc_after", {}),

            # ── STATUS ──
            "status": (
                "✔ No Missing"  if info.get("missing_before", 0) == 0
                else "✔ Fixed"  if info.get("missing_after", 0)  == 0
                else "⚠ Partial"
            ),
        })

    return table


# =====================================================
# SMART INSIGHTS GENERATOR
# =====================================================
def generate_insights(df, numeric_cols, categorical_cols, datetime_cols,
                       handling_report, outlier_report, duplicates, date_format_map):
    insights = []
    rows, cols = df.shape

    insights.append(f"Dataset has {rows:,} rows and {cols} columns.")

    if numeric_cols:
        insights.append(
            f"{len(numeric_cols)} numeric column(s): "
            f"{', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}."
        )
    if categorical_cols:
        insights.append(
            f"{len(categorical_cols)} categorical column(s): "
            f"{', '.join(categorical_cols[:5])}{'...' if len(categorical_cols) > 5 else ''}."
        )

    if datetime_cols:
        fmt_map = {
            "%Y-%m-%d":          "ISO 8601 (YYYY-MM-DD) — International",
            "%d/%m/%Y":          "DMY (DD/MM/YYYY) — India/UK/Australia",
            "%m/%d/%Y":          "MDY (MM/DD/YYYY) — United States",
            "%d-%m-%Y":          "DMY with hyphens (DD-MM-YYYY)",
            "%d.%m.%Y":          "DMY with dots (DD.MM.YYYY)",
            "%d %b %Y":          "Textual — 19 Feb 2025",
            "%d %B %Y":          "Textual — 19 February 2025",
            "%B %d, %Y":         "Textual — February 19, 2025",
            "%Y-%m-%dT%H:%M:%S": "ISO 8601 with Time",
            "auto-detected":     "Auto-detected by pandas",
        }
        for col in datetime_cols:
            fmt = date_format_map.get(col, "unknown")
            insights.append(f"Date column '{col}' detected — Format: {fmt_map.get(fmt, fmt)}.")
    else:
        insights.append("No date columns detected.")

    if duplicates > 0:
        pct = round((duplicates / rows) * 100, 1)
        insights.append(f"⚠ {duplicates:,} duplicate rows found ({pct}% of dataset).")
    else:
        insights.append("✔ No duplicate rows found.")

    missing_cols = [(c, v["missing_before"]) for c, v in handling_report.items() if v["missing_before"] > 0]
    if missing_cols:
        worst = max(missing_cols, key=lambda x: x[1])
        insights.append(
            f"⚠ {len(missing_cols)} column(s) had missing values. "
            f"'{worst[0]}' had the most ({worst[1]:,} missing). All filled automatically."
        )
        for col, info in handling_report.items():
            if info["missing_before"] > 0:
                insights.append(
                    f"  → '{col}' [{info['col_type']}]: "
                    f"{info['missing_before']} missing. {info['method']}."
                )
    else:
        insights.append("✔ Dataset has no missing values — clean data!")

    for col, info in outlier_report.items():
        if info["outliers_count"] > 0:
            insights.append(
                f"⚠ Outliers in '{col}': {info['outliers_count']} values outside "
                f"[{info['lower_bound']}, {info['upper_bound']}] (IQR method)."
            )

    for col in numeric_cols:
        try:
            skew = float(df[col].skew())
            if abs(skew) > 1:
                direction = "right (positive)" if skew > 0 else "left (negative)"
                insights.append(f"'{col}' is heavily skewed {direction} (skew={round(skew, 2)}).")
        except Exception:
            pass

    for col in categorical_cols:
        n_unique = df[col].nunique()
        if n_unique > rows * 0.8:
            insights.append(f"'{col}' has very high cardinality ({n_unique} unique values) — likely an ID column.")

    for col in df.columns:
        if df[col].nunique() == 1:
            insights.append(f"⚠ '{col}' has only 1 unique value — adds no information.")

    return insights


# =====================================================
# MAIN EDA FUNCTION
# =====================================================
def perform_eda(df):

    df = df.copy()
    rows, columns = df.shape

    # ── Raw df.info() BEFORE any changes ──
    buffer = StringIO()
    df.info(buf=buffer)
    info_string = buffer.getvalue()

    nunique_data = df.nunique().to_dict()

    # Step 1 — Date Detection
    df, detected_dates, date_format_map = try_parse_dates(df)

    # Step 2 — Missing Value Handling (captures before + cleans + captures after)
    df, handling_report, before_snapshot = handle_missing_values(df)

    # Step 3 — Column Types (after cleaning)
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
        value_counts[col] = df[col].astype(str).value_counts().head(50).to_dict()

    # Step 7 — Histograms
    histograms = {}
    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) > 0:
            counts, bins = np.histogram(values, bins=20)
            histograms[col] = {"bins": bins[:-1].tolist(), "counts": counts.tolist()}

    # Step 8 — Correlation
    correlation = {}
    numeric_df  = df.select_dtypes(include=np.number)
    if len(numeric_df.columns) >= 2:
        correlation = numeric_df.corr().fillna(0).to_dict()

    # Step 9 — Duplicates
    duplicates = int(df.duplicated().sum())

    # Step 10 — Preview
    preview = df.head(10).to_dict(orient="records")

    # Step 11 — Insights
    insights = generate_insights(
        df, numeric_cols, categorical_cols, datetime_cols,
        handling_report, outlier_report, duplicates, date_format_map
    )

    # Step 12 — Before / After table for the toggle button
    before_after_table = build_before_after_table(rows, handling_report, before_snapshot)

    # ── Final response object ──
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

        # ── Powers the Before / After button ──
        "before_after_missing":     before_after_table,

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

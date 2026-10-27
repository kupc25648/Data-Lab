from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .preprocess import ColumnRoles, detect_column_roles


@dataclass
class DatasetProfile:
    rows: int
    columns: int
    roles: ColumnRoles
    missing_total: int
    duplicate_rows: int
    memory_mb: float
    warnings: list[str]


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    roles = detect_column_roles(df)
    missing_total = int(df.isna().sum().sum())
    dup = int(df.duplicated().sum())
    memory_mb = float(df.memory_usage(deep=True).sum() / (1024**2))
    warnings: list[str] = []
    total_cells = max(int(df.shape[0] * df.shape[1]), 1)
    if df.shape[0] < 30:
        warnings.append("Small sample size: model metrics and statistical tests may be unstable.")
    if missing_total / total_cells > 0.10:
        warnings.append("More than 10% of cells are missing. Review missingness before modeling.")
    if dup > 0:
        warnings.append(f"{dup} duplicated row(s) detected.")
    if not roles.numeric:
        warnings.append("No usable numeric columns detected after excluding ID-like fields.")
    high_card = [c for c in roles.categorical if df[c].nunique(dropna=True) > 50]
    if high_card:
        warnings.append("Some categorical columns have high cardinality and may be difficult to model directly.")
    return DatasetProfile(df.shape[0], df.shape[1], roles, missing_total, dup, memory_mb, warnings)


def overview_table(df: pd.DataFrame) -> pd.DataFrame:
    prof = profile_dataset(df)
    rows = [
        {"Metric": "Rows", "Value": prof.rows},
        {"Metric": "Columns", "Value": prof.columns},
        {"Metric": "Numeric columns", "Value": len(prof.roles.numeric)},
        {"Metric": "Categorical columns", "Value": len(prof.roles.categorical)},
        {"Metric": "Datetime columns", "Value": len(prof.roles.datetime)},
        {"Metric": "ID-like columns", "Value": len(prof.roles.id_like)},
        {"Metric": "Missing cells", "Value": prof.missing_total},
        {"Metric": "Duplicated rows", "Value": prof.duplicate_rows},
        {"Metric": "Memory MB", "Value": round(prof.memory_mb, 3)},
    ]
    return pd.DataFrame(rows)


def column_quality_table(df: pd.DataFrame) -> pd.DataFrame:
    roles = detect_column_roles(df)
    role_lookup = {}
    for name in roles.numeric: role_lookup[name] = "numeric"
    for name in roles.categorical: role_lookup[name] = "categorical"
    for name in roles.datetime: role_lookup[name] = "datetime"
    for name in roles.id_like: role_lookup[name] = "id-like"
    rows = []
    for col in df.columns:
        s = df[col]
        rows.append({
            "Column": col,
            "Role": role_lookup.get(col, "other"),
            "Dtype": str(s.dtype),
            "Missing": int(s.isna().sum()),
            "Missing %": round(float(s.isna().mean() * 100), 2),
            "Unique": int(s.nunique(dropna=True)),
            "Example": str(s.dropna().iloc[0]) if not s.dropna().empty else "",
        })
    return pd.DataFrame(rows)


def numeric_summary(df: pd.DataFrame, numeric_cols: list[str] | None = None) -> pd.DataFrame:
    if numeric_cols is None:
        numeric_cols = detect_column_roles(df).numeric
    rows = []
    for col in numeric_cols:
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            continue
        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1
        outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()) if iqr > 0 else 0
        rows.append({
            "Column": col,
            "Count": int(s.count()),
            "Mean": float(s.mean()),
            "Std": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
            "Min": float(s.min()),
            "Q1": float(q1),
            "Median": float(s.median()),
            "Q3": float(q3),
            "Max": float(s.max()),
            "Skewness": float(stats.skew(s)) if len(s) >= 3 else np.nan,
            "Kurtosis": float(stats.kurtosis(s)) if len(s) >= 4 else np.nan,
            "IQR outliers": outliers,
        })
    return pd.DataFrame(rows)


def categorical_summary(df: pd.DataFrame, categorical_cols: list[str] | None = None) -> pd.DataFrame:
    if categorical_cols is None:
        categorical_cols = detect_column_roles(df).categorical
    rows = []
    for col in categorical_cols:
        s = df[col].dropna().astype(str)
        top = s.value_counts().head(5)
        rows.append({
            "Column": col,
            "Count": int(s.count()),
            "Unique": int(s.nunique()),
            "Top values": ", ".join(f"{k}: {v}" for k, v in top.items()),
            "Rare categories (<2%)": int((s.value_counts(normalize=True) < 0.02).sum()) if len(s) else 0,
        })
    return pd.DataFrame(rows)


def target_health(df: pd.DataFrame, target_col: str) -> dict[str, Any]:
    s = df[target_col].dropna()
    info: dict[str, Any] = {"target": target_col, "missing": int(df[target_col].isna().sum()), "unique": int(s.nunique())}
    if pd.api.types.is_numeric_dtype(s):
        info.update({"type": "numeric", "mean": float(s.mean()), "std": float(s.std()), "skewness": float(stats.skew(s)) if len(s) >= 3 else np.nan})
    else:
        counts = s.astype(str).value_counts()
        ratio = counts.iloc[0] / max(counts.sum(), 1) if not counts.empty else np.nan
        info.update({"type": "categorical", "majority_class": str(counts.index[0]) if not counts.empty else "", "majority_ratio": float(ratio)})
    return info

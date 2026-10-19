from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def normality_test(df: pd.DataFrame, col: str) -> dict[str, Any]:
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(s) < 3:
        return {"Test": "Shapiro-Wilk", "Column": col, "N": len(s), "Statistic": np.nan, "p-value": np.nan, "Interpretation": "insufficient data"}
    if len(s) > 5000:
        s = s.sample(5000, random_state=42)
    stat, p = stats.shapiro(s)
    return {"Test": "Shapiro-Wilk", "Column": col, "N": len(s), "Statistic": float(stat), "p-value": float(p), "Interpretation": "likely non-normal" if p < 0.05 else "no strong evidence against normality"}


def compare_two_groups(df: pd.DataFrame, numeric_col: str, group_col: str, test: str = "Auto") -> dict[str, Any]:
    temp = df[[numeric_col, group_col]].dropna().copy()
    groups = list(temp[group_col].astype(str).unique())[:2]
    if len(groups) != 2:
        return {"Test": test, "Result": "Select a grouping column with exactly two groups."}
    a = pd.to_numeric(temp[temp[group_col].astype(str) == groups[0]][numeric_col], errors="coerce").dropna()
    b = pd.to_numeric(temp[temp[group_col].astype(str) == groups[1]][numeric_col], errors="coerce").dropna()
    if len(a) < 2 or len(b) < 2:
        return {"Test": test, "Result": "Insufficient data in one or both groups."}
    use = test
    if test == "Auto":
        use = "Welch t-test" if len(a) >= 20 and len(b) >= 20 else "Mann-Whitney U"
    if use == "Mann-Whitney U":
        stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    else:
        stat, p = stats.ttest_ind(a, b, equal_var=False)
        use = "Welch t-test"
    return {"Test": use, "Numeric": numeric_col, "Group": group_col, "Group A": groups[0], "Group B": groups[1], "N A": len(a), "N B": len(b), "Mean A": float(a.mean()), "Mean B": float(b.mean()), "Statistic": float(stat), "p-value": float(p), "Interpretation": "significant difference" if p < 0.05 else "no significant difference"}


def compare_many_groups(df: pd.DataFrame, numeric_col: str, group_col: str, test: str = "Auto") -> dict[str, Any]:
    temp = df[[numeric_col, group_col]].dropna().copy()
    data = []
    names = []
    for name, sub in temp.groupby(group_col):
        vals = pd.to_numeric(sub[numeric_col], errors="coerce").dropna()
        if len(vals) >= 2:
            data.append(vals)
            names.append(str(name))
    if len(data) < 2:
        return {"Test": test, "Result": "Need at least two groups with enough data."}
    use = test
    if test == "Auto":
        use = "ANOVA" if all(len(x) >= 20 for x in data) else "Kruskal-Wallis"
    if use == "ANOVA":
        stat, p = stats.f_oneway(*data)
    else:
        stat, p = stats.kruskal(*data)
        use = "Kruskal-Wallis"
    return {"Test": use, "Numeric": numeric_col, "Group": group_col, "Groups": ", ".join(names), "Statistic": float(stat), "p-value": float(p), "Interpretation": "at least one group differs" if p < 0.05 else "no significant group difference"}


def chi_square_test(df: pd.DataFrame, col_a: str, col_b: str) -> dict[str, Any]:
    temp = df[[col_a, col_b]].dropna().astype(str)
    if temp.empty:
        return {"Test": "Chi-square", "Result": "Insufficient data."}
    table = pd.crosstab(temp[col_a], temp[col_b])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {"Test": "Chi-square", "Result": "Both columns need at least two categories."}
    chi2, p, dof, expected = stats.chi2_contingency(table)
    return {"Test": "Chi-square independence", "Column A": col_a, "Column B": col_b, "Chi-square": float(chi2), "p-value": float(p), "df": int(dof), "Interpretation": "variables are associated" if p < 0.05 else "no significant association"}


def confidence_interval_mean(df: pd.DataFrame, col: str, confidence: float = 0.95) -> dict[str, Any]:
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(s) < 2:
        return {"Column": col, "Result": "Insufficient data."}
    mean = s.mean()
    se = stats.sem(s)
    h = se * stats.t.ppf((1 + confidence) / 2, len(s) - 1)
    return {"Column": col, "N": len(s), "Mean": float(mean), "Confidence": confidence, "Lower": float(mean - h), "Upper": float(mean + h)}

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

from .visualization import apply_theme


def correlation_matrix(df: pd.DataFrame, cols: list[str], method: str = "pearson") -> pd.DataFrame:
    if len(cols) < 2:
        return pd.DataFrame()
    return df[cols].corr(method=method, numeric_only=True)


def correlation_heatmap(corr: pd.DataFrame, title: str = "Correlation heatmap") -> go.Figure:
    if corr.empty:
        fig = go.Figure()
        fig.add_annotation(text="Select at least two numeric columns", x=0.5, y=0.5, showarrow=False)
        return apply_theme(fig, height=500, title=title)
    fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto")
    return apply_theme(fig, height=max(480, 32 * len(corr)), title=title)


def ranked_correlations(corr: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    rows = []
    seen = set()
    for a in corr.columns:
        for b in corr.index:
            if a == b:
                continue
            key = tuple(sorted([a, b]))
            if key in seen:
                continue
            seen.add(key)
            val = corr.loc[b, a]
            if pd.notna(val):
                rows.append({"Variable A": key[0], "Variable B": key[1], "Correlation": float(val), "Abs": abs(float(val))})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("Abs", ascending=False).drop(columns="Abs").head(top_n).reset_index(drop=True)


def correlation_significance(df: pd.DataFrame, x: str, y: str, method: str = "pearson") -> dict[str, float | str]:
    temp = df[[x, y]].dropna()
    if len(temp) < 3:
        return {"method": method, "n": len(temp), "r": np.nan, "p_value": np.nan}
    if method == "spearman":
        r, p = stats.spearmanr(temp[x], temp[y])
    else:
        r, p = stats.pearsonr(temp[x], temp[y])
    return {"method": method, "n": int(len(temp)), "r": float(r), "p_value": float(p)}


def vif_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    # Lightweight VIF without statsmodels: regress each col on all others using sklearn.
    from sklearn.linear_model import LinearRegression
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    rows = []
    use = df[cols].replace([np.inf, -np.inf], np.nan)
    for col in cols:
        others = [c for c in cols if c != col]
        if not others:
            continue
        temp = use[[col] + others].dropna()
        if len(temp) < max(10, len(others) + 2):
            rows.append({"Feature": col, "VIF": np.nan, "Interpretation": "insufficient data"})
            continue
        X = temp[others]
        y = temp[col]
        pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", LinearRegression())])
        pipe.fit(X, y)
        r2 = pipe.score(X, y)
        vif = np.inf if r2 >= 0.999999 else 1.0 / (1.0 - r2)
        label = "high multicollinearity" if vif >= 10 else ("moderate" if vif >= 5 else "low")
        rows.append({"Feature": col, "VIF": float(vif), "Interpretation": label})
    return pd.DataFrame(rows).sort_values("VIF", ascending=False, na_position="last")

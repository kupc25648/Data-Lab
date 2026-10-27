from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETTE = ["#60A5FA", "#A78BFA", "#34D399", "#FBBF24", "#FB7185", "#22D3EE", "#F97316", "#C084FC"]


def apply_theme(fig: go.Figure, height: int | None = None, title: str | None = None) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15,23,42,0)",
        plot_bgcolor="rgba(15,23,42,0.34)",
        font=dict(color="#E5E7EB", size=13),
        title_font=dict(color="#F8FAFC", size=19),
        margin=dict(t=68, b=52, l=58, r=32),
        legend=dict(bgcolor="rgba(15,23,42,0.35)", bordercolor="rgba(148,163,184,0.22)", borderwidth=1),
        colorway=PALETTE,
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.18)", zerolinecolor="rgba(148,163,184,0.32)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.18)", zerolinecolor="rgba(148,163,184,0.32)")
    if height:
        fig.update_layout(height=height)
    if title:
        fig.update_layout(title=title)
    return fig


def histogram(df: pd.DataFrame, col: str, color: str | None = None, nbins: int = 30) -> go.Figure:
    fig = px.histogram(df, x=col, color=color, nbins=nbins, marginal="box" if color is None else None, opacity=0.86)
    mean = pd.to_numeric(df[col], errors="coerce").mean()
    median = pd.to_numeric(df[col], errors="coerce").median()
    if pd.notna(mean):
        fig.add_vline(x=mean, line_color="#FBBF24", line_dash="solid", annotation_text="mean")
    if pd.notna(median):
        fig.add_vline(x=median, line_color="#A78BFA", line_dash="dash", annotation_text="median")
    return apply_theme(fig, height=480, title=f"Distribution of {col}")


def box_plot(df: pd.DataFrame, y: str, x: str | None = None, color: str | None = None) -> go.Figure:
    fig = px.box(df, x=x, y=y, color=color or x, points="outliers")
    return apply_theme(fig, height=480, title=f"Box plot of {y}" + (f" by {x}" if x else ""))


def violin_plot(df: pd.DataFrame, y: str, x: str | None = None, color: str | None = None) -> go.Figure:
    fig = px.violin(df, x=x, y=y, color=color or x, box=True, points="all")
    return apply_theme(fig, height=500, title=f"Violin plot of {y}" + (f" by {x}" if x else ""))


def categorical_bar(df: pd.DataFrame, col: str, top_n: int = 20) -> go.Figure:
    counts = df[col].dropna().astype(str).value_counts().head(top_n).reset_index()
    counts.columns = [col, "count"]
    counts["percent"] = counts["count"] / counts["count"].sum() * 100
    fig = px.bar(counts, x=col, y="count", text=counts["percent"].map(lambda x: f"{x:.1f}%"))
    fig.update_traces(textposition="outside")
    return apply_theme(fig, height=480, title=f"Frequency of {col}")


def scatter(df: pd.DataFrame, x: str, y: str, color: str | None = None, size: str | None = None, trendline: bool = True) -> go.Figure:
    fig = px.scatter(df, x=x, y=y, color=color, size=size, trendline="ols" if trendline else None, opacity=0.78)
    fig.update_traces(marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.55)")))
    return apply_theme(fig, height=520, title=f"{y} vs {x}")


def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None) -> go.Figure:
    plot_df = df[[x, y] + ([color] if color else [])].dropna().sort_values(x)
    fig = px.line(plot_df, x=x, y=y, color=color, markers=True)
    return apply_theme(fig, height=500, title=f"{y} over {x}")


def bar_agg(df: pd.DataFrame, x: str, y: str, agg: str = "mean", color: str | None = None) -> go.Figure:
    if color:
        g = df.groupby([x, color], dropna=False)[y].agg(agg).reset_index()
    else:
        g = df.groupby(x, dropna=False)[y].agg(agg).reset_index()
    fig = px.bar(g, x=x, y=y, color=color, text_auto=".2s")
    return apply_theme(fig, height=500, title=f"{agg.title()} {y} by {x}")


def missingness_bar(df: pd.DataFrame) -> go.Figure:
    miss = df.isna().sum().sort_values(ascending=False)
    miss = miss[miss > 0]
    if miss.empty:
        fig = go.Figure()
        fig.add_annotation(text="No missing values detected", x=0.5, y=0.5, showarrow=False, font=dict(size=18))
        return apply_theme(fig, height=360, title="Missing values")
    temp = miss.reset_index(); temp.columns = ["Column", "Missing"]
    temp["Missing %"] = temp["Missing"] / len(df) * 100
    fig = px.bar(temp, x="Column", y="Missing", text=temp["Missing %"].map(lambda x: f"{x:.1f}%"))
    fig.update_traces(textposition="outside")
    return apply_theme(fig, height=450, title="Missing values by column")


def target_balance(df: pd.DataFrame, target: str) -> go.Figure:
    if pd.api.types.is_numeric_dtype(df[target]):
        return histogram(df, target)
    return categorical_bar(df, target)


def pair_scatter_matrix(df: pd.DataFrame, cols: list[str], color: str | None = None, max_cols: int = 5) -> go.Figure:
    use_cols = cols[:max_cols]
    fig = px.scatter_matrix(df, dimensions=use_cols, color=color, opacity=0.65)
    fig.update_traces(diagonal_visible=False)
    return apply_theme(fig, height=760, title="Scatter matrix")

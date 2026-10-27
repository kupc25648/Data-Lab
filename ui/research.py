"""Slides 75-78: numeric regression only; no classification or generative models."""
from __future__ import annotations
from ui.i18n import t as tr, localize_tabs, localize_plot
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from backend.lessons import REGRESSION
from backend.regression import regression_fit, candidates_advanced, fitted_equation
from backend.visualization import apply_theme
from .common import lesson_header, learn, ensure_dataset, applied, save_table

def demo_explore(i):
    rng = np.random.default_rng(12)
    slope = st.slider(tr('Energy increase per area unit (slope)'), -5.0, 8.0, 2.0, 0.5, key=f'g_slope_{i}')
    noise = st.slider(tr('Measurement / unmodeled noise'), 0.0, 100.0, 25.0, 5.0, key=f'g_noise_{i}')
    x = np.linspace(30, 180, 35)
    y = 150 + slope * x + rng.normal(0, noise, len(x))
    model = LinearRegression().fit(x.reshape(-1, 1), y)
    pred = model.predict(x.reshape(-1, 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name='Observed'))
    fig.add_trace(go.Scatter(x=x, y=pred, mode='lines', name='Fitted line'))
    sample = 12
    fig.add_trace(go.Scatter(x=[x[sample], x[sample]], y=[y[sample], pred[sample]], mode='lines+markers', name='Example residual', line=dict(dash='dash')))
    st.plotly_chart(localize_plot(apply_theme(fig, title='Linear regression: fitted values and residual')), use_container_width=True, key='research_explore_linear_fit')
    st.write(tr(f'Fitted equation: **energy = {model.intercept_:.2f} + {model.coef_[0]:.2f} × area**'))
    requested = st.number_input(tr('Predict energy at floor area (m²)'), min_value=20.0, max_value=200.0, value=80.0, key=f'g_predict_{i}')
    st.metric(tr('Predicted energy (synthetic units)'), f'{model.predict([[requested]])[0]:.1f}')
    st.caption(tr('Prediction and fitted association are not causal explanations. Dashed segment illustrates an observed minus predicted residual.'))

def analyze(i, df):
    if not ensure_dataset(df):
        return
    d, roles = applied(df)
    if not roles.numeric:
        st.info(tr('No numerical outcome column. Select Numeric in the sidebar if scientific meaning supports it.'))
        return
    st.markdown(tr('**Guided regression — select a numeric target explicitly**'))
    target = st.selectbox(tr('Numerical target (y)'), roles.numeric, index=max(0, len(roles.numeric) - 1), key='g_target', format_func=lambda v: tr(str(v)))
    eligible = [c for c in d.columns if c != target and c not in roles.id_like + roles.datetime]
    default = roles.numeric[:1] if roles.numeric and roles.numeric[0] != target else [c for c in roles.numeric if c != target][:1]
    default = [c for c in default if c in eligible]
    features = st.multiselect(tr('Explanatory variables (X)'), eligible, default=default, key='g_features', format_func=lambda v: tr(str(v)))
    st.caption(tr('An architectural researcher must confirm predictors are available at prediction time and not derived from the target.'))
    advanced = st.toggle(tr('Advanced regression model comparison'), value=False, key='g_advanced')
    choices = None
    if advanced:
        modelnames = list(candidates_advanced(42))
        choices = st.multiselect(tr('Regression algorithms'), modelnames, default=modelnames[:3], key='g_models', format_func=lambda v: tr(str(v)))
    split_method = st.selectbox(tr('Train/test split design'), ['Random', 'Chronological', 'Grouped'], key='g_split', format_func=lambda v: tr(str(v)))
    order_col = None
    group_col = None
    if split_method == 'Chronological':
        options = roles.datetime + roles.numeric
        order_col = st.selectbox(tr('Order variable (time or sequence)'), options, key='g_order', format_func=lambda v: tr(str(v))) if options else None
    if split_method == 'Grouped':
        options = [c for c in d if c != target]
        group_col = st.selectbox(tr('Independent group ID (building, project, participant)'), options, key='g_group', format_func=lambda v: tr(str(v)))
    c1, c2, c3 = st.columns(3)
    size = c1.slider(tr('Test fraction'), 0.15, 0.35, 0.2, step=0.05, key='g_test_size')
    folds = c2.slider(tr('Training CV folds'), 3, 6, 5, key='g_cv_folds')
    seed = c3.number_input(tr('Random seed'), min_value=0, max_value=9999, value=42, step=1, key='g_seed')
    if st.button(tr('Run regression and evaluate held-out predictions'), type='primary', key='g_run'):
        try:
            run = regression_fit(d, target, features, advanced, choices, int(seed), float(size), folds, split_method, order_col, group_col)
            st.session_state.last_regression = run
            st.session_state.export_bundle = None
            st.session_state.regression_signature = (st.session_state.dataset_id, tuple(sorted(st.session_state.role_overrides.items())))
            save_table('cv_regression', run.cv_metrics)
            save_table('test_regression', run.final_metrics)
        except (ValueError, TypeError) as exc:
            st.error(tr(f'Cannot run regression: {exc}'))
    run = st.session_state.last_regression
    if run is None:
        return
    if st.session_state.regression_signature != (st.session_state.dataset_id, tuple(sorted(st.session_state.role_overrides.items()))):
        st.warning(tr('Stored regression belongs to previous data/role settings; rerun the model.'))
        return
    if run.target != target or run.features != features:
        st.warning(tr('Displayed results are from an earlier target/predictor selection. Click Run regression to update.'))
    st.success(tr(f'Selected using training folds: {run.best_model} · Final holdout: {run.test_n} observations'))
    st.dataframe(run.cv_metrics, hide_index=True)
    st.markdown(tr('**Final held-out test metrics (evaluated only after model selection)**'))
    st.dataframe(run.final_metrics, hide_index=True)
    equation = fitted_equation(run)
    if equation:
        st.write('**Fitted equation (original input units):** ' + equation)
    figs = st.tabs(localize_tabs(['Observed vs predicted', 'Residuals', 'Predictions & interpretation']))
    with figs[0]:
        fig = px.scatter(run.predictions, x='observed', y='predicted', title='Observed vs predicted — held-out test')
        lo = float(min(run.predictions[['observed', 'predicted']].min()))
        hi = float(max(run.predictions[['observed', 'predicted']].max()))
        fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode='lines', name='Perfect prediction', line=dict(dash='dash')))
        st.plotly_chart(localize_plot(apply_theme(fig)), use_container_width=True, key='research_analyze_observed_predicted')
    with figs[1]:
        fig = px.scatter(run.predictions, x='predicted', y='residual', title='Residuals vs predicted')
        fig.add_hline(y=0, line_dash='dash')
        st.plotly_chart(localize_plot(apply_theme(fig)), use_container_width=True, key='research_analyze_residuals')
    with figs[2]:
        st.dataframe(run.predictions.head(60), hide_index=True)
        st.caption(tr(f'Split={run.split_method}; seed={run.seed}; train n={run.train_n}; test n={run.test_n}. Residual = observed − predicted.'))
    for note in run.notes:
        st.warning(note)
    st.info(tr('Predictive accuracy does not prove causation; ensure measurements, groups, leakage, temporal structure and sampling match your research question.'))

def render(df):
    topic = st.selectbox(tr('Lecture topic'), [x.title for x in REGRESSION], key='g_topic', format_func=lambda v: tr(str(v)))
    i = next((j for j, v in enumerate(REGRESSION) if v.title == topic))
    lesson = REGRESSION[i]
    lesson_header(lesson)
    a, b, c = st.tabs(localize_tabs(['Learn', 'Explore', 'Analyze']))
    with a:
        learn(lesson)
    with b:
        demo_explore(i)
    with c:
        analyze(i, df)

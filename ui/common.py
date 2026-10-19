from __future__ import annotations
from ui.i18n import t as tr, localize_tabs, localized_lesson, render_reading
import streamlit as st
import pandas as pd
from backend.preprocess import detect_column_roles, make_analysis_view, data_warnings

def lesson_header(lesson):
    st.caption(tr(f'LECTURE SLIDES {lesson.slides}  ·  TABULAR DATA SCIENCE'))
    st.subheader(tr(lesson.title))

def learn(lesson):
    _, summary, points, limitation = localized_lesson(lesson)
    st.markdown(summary)
    for point in points:
        st.markdown('• ' + point)
    st.info(f'**{tr("Interpretation / limitation:")}** {limitation}')
    render_reading(lesson.title)
    with st.expander(tr('Show equivalent Python operation')):
        st.code(lesson.python, language='python')
        st.caption(tr('Illustrative code fragments; adapt column names to your dataset.'))

def ensure_dataset(df):
    if df is None:
        st.info(tr('Load a CSV/Excel file or choose a synthetic demo dataset in the sidebar to analyze your own table. You can use Learn and Explore without data.'))
        return False
    return True

def applied(df):
    if df is None:
        return (None, None)
    roles = detect_column_roles(df, st.session_state.role_overrides)
    view = make_analysis_view(df, st.session_state.role_overrides)
    return (view, roles)

def see_data_warnings(df):
    for warning in data_warnings(df):
        st.warning(tr(warning))

def show_metric_values(metrics: list[tuple[str, str]]):
    cols = st.columns(len(metrics))
    for c, (k, v) in zip(cols, metrics):
        c.metric(tr(k), v)

def save_table(name, frame):
    st.session_state.saved_tables[name] = frame

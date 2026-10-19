"""Slides 13-29 and 45-46; tabular representations only."""
from __future__ import annotations
from ui.i18n import t as tr, localize_tabs, localize_plot
import streamlit as st
import pandas as pd
import plotly.express as px
from backend.lessons import REPRESENTATION
from backend.preprocess import quality_table, one_hot_preview, frequency_table, apply_cleaning
from backend.visualization import histogram
from .common import lesson_header, learn, ensure_dataset, applied, see_data_warnings

def _toy():
    return pd.DataFrame({'room_id': ['R1', 'R2', 'R3', 'R4'], 'area_m2': [18.5, 25.3, 13.1, 32.0], 'room_type': ['Living', 'Office', 'Office', 'Living'], 'occupants': [3, 2, 1, 4]})

def explore(topic):
    toy = _toy()
    if topic in [0, 1, 5]:
        st.markdown(tr('**Example: rooms as observations, measured properties as variables**'))
        col = st.selectbox(tr('Highlight a column (variable)'), list(toy.columns), key=f'r_rep_col_{topic}', format_func=lambda v: tr(str(v)))
        row = st.slider(tr('Highlight a row (observation)'), 0, len(toy) - 1, 0, key=f'r_rep_row_{topic}')
        style = pd.DataFrame('', index=toy.index, columns=toy.columns)
        style.loc[row, :] = 'background-color: #23466d'
        style.loc[:, col] = 'background-color: #375d83'
        st.dataframe(toy.style.apply(lambda _: style, axis=None), hide_index=True)
        st.caption(tr(f'Observation {row + 1}: {toy.iloc[row].to_dict()}. Selected variable: {col}.'))
        st.dataframe(toy[[col]], hide_index=True)
    elif topic == 2:
        col = st.selectbox(tr('Categorical example'), ['room_type'], key='r_cat_demo', format_func=lambda v: tr(str(v)))
        st.markdown(tr('Original categories → one-hot indicator columns'))
        st.dataframe(one_hot_preview(toy[col]), hide_index=True)
        st.caption(tr('One-hot encoding avoids imposing an artificial rank on nominal room types.'))
    elif topic == 3:
        mode = st.radio(tr('Select a numerical type'), ['Continuous area (m²)', 'Discrete occupants'], horizontal=True, key='r_num_mode', format_func=lambda v: tr(str(v)))
        col = 'area_m2' if mode.startswith('Continuous') else 'occupants'
        st.plotly_chart(localize_plot(px.histogram(toy, x=col, nbins=6, title=f'Distribution of {col}')), use_container_width=True, key='representation_explore_numerical_type')
        st.dataframe(toy[[col]].describe(), use_container_width=True)
    elif topic == 4:
        sample = toy.copy()
        sample.loc[1, 'room_type'] = '  Office  '
        sample.loc[2, 'area_m2'] = None
        sample = pd.concat([sample, sample.iloc[[0]]], ignore_index=True)
        st.dataframe(sample, hide_index=True)
        st.write(tr('Missing cells:'), int(sample.isna().sum().sum()), tr('· Exact duplicates:'), int(sample.duplicated().sum()))
        st.caption(tr('Cleaning should be reviewed: repeated measurements are not necessarily mistakes.'))

def analyze(topic, df):
    if not ensure_dataset(df):
        return
    d, roles = applied(df)
    if topic in [0, 1, 5]:
        st.metric(tr('Observations (rows)'), len(d))
        st.metric(tr('Variables (columns)'), len(d.columns))
        st.dataframe(d.head(35), hide_index=True)
        st.dataframe(quality_table(d, roles), hide_index=True)
    elif topic == 2:
        if not roles.categorical:
            st.info(tr('No categorical columns. You can designate a column as Categorical in the sidebar.'))
            return
        col = st.selectbox(tr('Category variable'), roles.categorical, key='r_cat_own', format_func=lambda v: tr(str(v)))
        st.dataframe(frequency_table(d[col]), hide_index=True)
        st.write(tr('**Encoding preview (original values alongside indicator columns)**'))
        st.dataframe(one_hot_preview(d[col], 12), hide_index=True)
    elif topic == 3:
        if not roles.numeric:
            st.info(tr('No numeric columns detected.'))
            return
        col = st.selectbox(tr('Numerical variable'), roles.numeric, key='r_num_own', format_func=lambda v: tr(str(v)))
        kind = st.radio(tr('Interpretation'), ['Continuous measurement', 'Discrete count'], horizontal=True, key='r_num_kind', format_func=lambda v: tr(str(v)))
        st.caption(tr(f'User interpretation: {kind}. The Python dtype alone cannot establish this scientific meaning.'))
        st.plotly_chart(localize_plot(histogram(d, col)), use_container_width=True, key='representation_analyze_numerical')
    elif topic == 4:
        see_data_warnings(d)
        st.write(tr('**Column quality**'))
        st.dataframe(quality_table(d, roles), hide_index=True)
        st.write(tr('**Prepare a working copy (explicit and reversible)**'))
        operation = st.selectbox(tr('Operation'), ['Trim text', 'Replace missing values', 'Drop exact duplicate rows', 'Drop completely empty rows/columns'], key='r_clean_action', format_func=lambda v: tr(str(v)))
        column = None
        value = None
        if operation == 'Trim text':
            opts = [c for c in d if pd.api.types.is_object_dtype(d[c]) or pd.api.types.is_string_dtype(d[c])]
            if not opts:
                st.info(tr('No text columns available.'))
                return
            column = st.selectbox(tr('Text column'), opts, key='r_clean_col_text', format_func=lambda v: tr(str(v)))
        elif operation == 'Replace missing values':
            opts = [c for c in d if d[c].isna().any()]
            if not opts:
                st.info(tr('No missing values in this working table.'))
                return
            column = st.selectbox(tr('Column with missing values'), opts, key='r_clean_col_miss', format_func=lambda v: tr(str(v)))
            value = st.selectbox(tr('Fill method'), ['Median', 'Mode'], key='r_clean_fill', format_func=lambda v: tr(str(v)))
        c1, c2, c3 = st.columns(3)
        if c1.button(tr('Preview transformation'), key='r_clean_preview'):
            try:
                proposed, desc = apply_cleaning(d, operation, column, value)
                st.session_state.pending_clean = (proposed, desc)
            except ValueError as exc:
                st.error(str(exc))
                st.session_state.pending_clean = None
        pending = st.session_state.get('pending_clean')
        if pending:
            proposed, description = pending
            st.caption('Proposed: ' + description)
            st.dataframe(proposed.head(15), hide_index=True)
            if c2.button(tr('Approve & apply'), key='r_clean_commit'):
                st.session_state.history.append(st.session_state.working.copy(deep=True))
                st.session_state.working = proposed.copy(deep=True)
                st.session_state.change_log.append({'Action': operation, 'Details': description})
                st.session_state.pending_clean = None
                st.session_state.last_regression = None
                st.session_state.saved_tables = {}
                st.session_state.auto_result = None
                st.session_state.export_bundle = None
                st.rerun()
        if c3.button(tr('Undo last change'), disabled=not st.session_state.history, key='r_clean_undo'):
            st.session_state.working = st.session_state.history.pop()
            if st.session_state.change_log:
                st.session_state.change_log.pop()
            st.session_state.last_regression = None
            st.session_state.saved_tables = {}
            st.session_state.pending_clean = None
            st.session_state.auto_result = None
            st.session_state.export_bundle = None
            st.rerun()
        if st.session_state.change_log:
            st.dataframe(pd.DataFrame(st.session_state.change_log), hide_index=True)
        with st.expander(tr('Original uploaded data (unchanged)')):
            st.dataframe(st.session_state.raw.head(50), hide_index=True)

def render(df):
    topic = st.selectbox(tr('Lecture topic'), [v.title for v in REPRESENTATION], key='r_topic', format_func=lambda v: tr(str(v)))
    i = next((j for j, l in enumerate(REPRESENTATION) if l.title == topic))
    lesson = REPRESENTATION[i]
    lesson_header(lesson)
    a, b, c = st.tabs(localize_tabs(['Learn', 'Explore', 'Analyze']))
    with a:
        learn(lesson)
    with b:
        explore(i)
    with c:
        analyze(i, df)

"""Slides 48-73: interactive exploratory statistical concepts and research data."""
from __future__ import annotations
from ui.i18n import t as tr, localize_tabs, localize_plot
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from backend.lessons import UNDERSTANDING
from backend.auto_analysis import numeric_summary, correlation_pairs, suggest_charts, auto_profile
from backend.preprocess import frequency_table, quality_table
from backend.interpolation import interpolate_ordered
from backend.visualization import histogram, scatter, box_plot, categorical_bar
from backend.visualization import apply_theme
from .common import lesson_header, learn, ensure_dataset, applied, save_table, see_data_warnings

def demo_explore(topic: int):
    rng = np.random.default_rng(123)
    if topic in (0, 1):
        n = st.slider(tr('Number of observations'), 5, 30, 12, key=f'u_demo_n_{topic}')
        extreme = st.slider(tr('Extreme observation'), 0, 100, 20, key=f'u_demo_outlier_{topic}')
        values = np.array([16, 18, 20, 21, 22, 23, 18, 19, 20, 21, 22, 20, 21, 20, 19, 18, 22, 17, 23, 20, 21, 19, 18, 20, 22, 20, 20, 23, 19, 21][:n], dtype=float)
        values[-1] = extreme
        st.metric(tr('Mean'), f'{np.mean(values):.2f}')
        st.metric(tr('Median'), f'{np.median(values):.2f}')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, n + 1)), y=values, mode='markers+lines', name='Observations'))
        fig.add_hline(y=values.mean(), line_dash='dash', annotation_text='Mean')
        st.plotly_chart(localize_plot(apply_theme(fig, title='Same observations, adjustable extreme value')), use_container_width=True, key='understanding_explore_mean')
        st.caption(tr('As the extreme value changes, the mean can shift more than the median.'))
    elif topic == 2:
        center = st.slider(tr('Shared mean'), 10, 50, 25, key='u_sd_mean')
        spread = st.slider(tr('Standard deviation scale'), 0.5, 9.0, 2.0, 0.5, key='u_sd_scale')
        z = np.linspace(-1.8, 1.8, 31)
        a = center + z * 0.8
        b = center + z * spread
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=a, name='Lower spread', opacity=0.65))
        fig.add_trace(go.Histogram(x=b, name='Adjustable spread', opacity=0.65))
        fig.update_layout(barmode='overlay')
        st.plotly_chart(localize_plot(apply_theme(fig, title='Equal mean, different spread')), use_container_width=True, key='understanding_explore_spread')
        st.write(tr(f'Lower SD = {a.std(ddof=1):.2f}; adjusted SD = {b.std(ddof=1):.2f} (same mean ≈ {center}).'))
    elif topic == 3:
        slope = st.slider(tr('Association direction / slope'), -3.0, 3.0, 1.5, 0.1, key='u_corr_slope')
        noise = st.slider(tr('Noise level'), 0.1, 5.0, 1.0, 0.1, key='u_corr_noise')
        x = np.linspace(-3, 3, 85)
        y = slope * x + rng.normal(0, noise, len(x))
        r = np.corrcoef(x, y)[0, 1]
        st.metric(tr('Pearson correlation'), f'{r:.3f}')
        st.plotly_chart(localize_plot(apply_theme(px.scatter(x=x, y=y, labels={'x': 'X', 'y': 'Y'}, title='Changing slope and noise changes r'))), use_container_width=True, key='understanding_explore_correlation')
        st.warning(tr('A strong correlation is not proof that X causes Y; hidden variables or common trends may explain it.'))
    elif topic in (4, 5, 6, 7, 8):
        toy = pd.DataFrame({'floor_area_m2': np.arange(40, 180, 8), 'energy_kwh': np.arange(40, 180, 8) * 4 + rng.normal(0, 35, 18), 'building_type': np.resize(['Office', 'School', 'Residential'], 18)})
        if topic == 5:
            st.plotly_chart(localize_plot(apply_theme(px.scatter(toy, x='floor_area_m2', y='energy_kwh', color='building_type', trendline='ols', title='Floor area vs energy (synthetic)'))), use_container_width=True, key='understanding_explore_scatter')
        elif topic == 6:
            agg = st.radio(tr('Bar represents'), ['Count', 'Mean energy'], horizontal=True, key='u_bar_agg', format_func=lambda v: tr(str(v)))
            fig = px.histogram(toy, x='building_type') if agg == 'Count' else px.bar(toy.groupby('building_type', as_index=False)['energy_kwh'].mean(), x='building_type', y='energy_kwh')
            st.plotly_chart(localize_plot(apply_theme(fig, title=f'Bar chart: {agg}')), use_container_width=True, key='understanding_explore_bar')
        elif topic == 7:
            q = st.radio(tr('Research question'), ['Distribution', 'Numerical relationship', 'Category counts'], horizontal=True, key='u_choose_q', format_func=lambda v: tr(str(v)))
            st.caption(tr({'Distribution': 'Histogram: one numerical variable.', 'Numerical relationship': 'Scatter plot: two numerical variables.', 'Category counts': 'Bar chart: frequency of categories.'}[q]))
            fig = px.histogram(toy, x='energy_kwh') if q == 'Distribution' else px.scatter(toy, x='floor_area_m2', y='energy_kwh') if q == 'Numerical relationship' else px.histogram(toy, x='building_type')
            st.plotly_chart(localize_plot(apply_theme(fig)), use_container_width=True, key='understanding_explore_chart_selector')
        else:
            st.plotly_chart(localize_plot(apply_theme(px.histogram(toy, x='energy_kwh', title='Distribution of energy'))), use_container_width=True, key='understanding_explore_statistics')
            st.dataframe(toy[['floor_area_m2', 'energy_kwh']].describe(), use_container_width=True)
    elif topic == 9:
        missing = st.slider(tr('Missing internal time index'), 1, 8, 4, key='u_interp_miss')
        t = np.arange(0, 11)
        y = 12 + 1.8 * t + 0.3 * np.sin(t)
        y[missing] = np.nan
        tmp = pd.DataFrame({'time': t, 'reading': y})
        filled, changes = interpolate_ordered(tmp, 'time', 'reading')
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=y, mode='lines+markers', name='Known observations'))
        fig.add_trace(go.Scatter(x=filled['time'], y=filled['reading'], mode='lines+markers', name='Interpolated series'))
        st.plotly_chart(localize_plot(apply_theme(fig, title='Estimating an internal missing reading')), use_container_width=True, key='understanding_explore_interpolation')
        st.dataframe(changes, hide_index=True)
    elif topic == 10:
        toy = pd.DataFrame({'room': ['A', 'A', 'B', 'C'], 'temp_c': [26, None, 27, 24], 'notes': ['hot', 'cool', 'warm', 'warm']})
        st.dataframe(toy, hide_index=True)
        st.write(tr('Data quality:'), int(toy.isna().sum().sum()), tr('missing cell(s), mixed numeric and categorical columns.'))
    elif topic == 11:
        answers = pd.Series(['Satisfied', 'Neutral', 'Satisfied', 'Unsatisfied', None, 'Satisfied', 'Neutral'], name='comfort')
        st.dataframe(frequency_table(answers), hide_index=True)
        st.caption(tr('Percent denominator includes missing responses, shown explicitly.'))

def localized_finding(finding, profile):
    if st.session_state.get('ui_language', 'en') != 'th':
        return finding
    if finding.startswith('Quality check: '):
        return 'ตรวจคุณภาพข้อมูล: ' + tr(finding.split(': ', 1)[1])
    if finding.startswith('Computed descriptive summaries for '):
        return f"คำนวณสถิติเชิงพรรณนาสำหรับ {len(profile['numeric'])} ตัวแปรเชิงตัวเลข"
    if finding.startswith('Largest observed |Pearson r|') and (not profile['pairs'].empty):
        p = profile['pairs'].iloc[0]
        return f"คู่ความสัมพันธ์ที่มากที่สุด: {p['Variable A']} เทียบกับ {p['Variable B']} (r={p['r']:.2f}, n={int(p['N'])}) เป็นผลสำรวจเบื้องต้น ไม่ยืนยันเหตุและผล"
    if 'pairs were examined' in finding:
        return f"ตรวจสอบทั้งหมด {len(profile['pairs'])} คู่ ต้องระวังการทดสอบหลายครั้งและค่า p ที่ยังไม่ปรับ"
    if finding.startswith('No major issues detected'):
        return 'ยังไม่พบปัญหาสำคัญจากการตรวจเบื้องต้น โปรดตรวจความหมายตัวแปรและหน่วยวัดด้วยตนเอง'
    return tr(finding)

def _plot_suggestion(df, sug):
    if sug['Chart'] == 'Histogram':
        return histogram(df, sug['X'])
    if sug['Chart'] == 'Scatter':
        return scatter(df, sug['X'], sug['Y'], trendline=False)
    if sug['Chart'] == 'Bar counts':
        return categorical_bar(df, sug['X'])
    return box_plot(df, sug['Y'], sug['X'])

def analyze(topic: int, df):
    if not ensure_dataset(df):
        return
    d, roles = applied(df)
    if topic in (0, 1, 2, 8):
        if not roles.numeric:
            st.info(tr('No numerical data detected.'))
            return
        data = numeric_summary(d, roles.numeric)
        st.dataframe(data, hide_index=True, use_container_width=True)
        save_table('descriptive', data)
        c = st.selectbox(tr('Inspect numerical variable'), roles.numeric, key=f'u_desc_{topic}', format_func=lambda v: tr(str(v)))
        st.plotly_chart(localize_plot(histogram(d, c)), use_container_width=True, key='understanding_analyze_distribution')
        st.caption(tr('Sample SD uses n−1. Check whether the reported scale and mean are meaningful.'))
    elif topic in (3, 5):
        if len(roles.numeric) < 2:
            st.info(tr('Two numerical variables are needed.'))
            return
        options = roles.numeric[:12]
        cols = st.multiselect(tr('Numerical variables to screen (max 12)'), options, default=options[:min(len(options), 6)], key=f'u_corr_cols_{topic}', format_func=lambda v: tr(str(v)))
        method = st.radio(tr('Correlation method'), ['pearson', 'spearman'], horizontal=True, key=f'u_corr_method_{topic}', format_func=lambda v: tr(str(v)))
        if len(cols) < 2:
            st.info(tr('Choose at least two variables.'))
            return
        pairs = correlation_pairs(d, cols, method)
        st.dataframe(pairs, hide_index=True)
        save_table('correlation', pairs)
        if not pairs.empty:
            pair_names = [f"{r['Variable A']} / {r['Variable B']}" for _, r in pairs.iterrows()]
            chosen = st.selectbox(tr('Inspect pair'), pair_names, key=f'u_corr_pair_{topic}', format_func=lambda v: tr(str(v)))
            i = pair_names.index(chosen)
            row = pairs.iloc[i]
            st.plotly_chart(localize_plot(scatter(d, row['Variable A'], row['Variable B'], trendline=True)), use_container_width=True, key='understanding_analyze_pairwise')
            st.caption(tr(f"{row['Method']} r={row['r']:.3f}, paired N={int(row['N'])}. Descriptive association, not causation."))
            if len(pairs) > 1:
                st.warning(tr(f'Screened {len(pairs)} pairs. Unadjusted p-values are not confirmatory evidence after searching many relationships.'))
    elif topic in (4, 7):
        suggestions = suggest_charts(roles)
        if not suggestions:
            st.info(tr('No suitable chart can be recommended from current field roles.'))
            return
        st.dataframe(pd.DataFrame(suggestions), hide_index=True)
        i = st.selectbox(tr('Chart to visualize'), range(len(suggestions)), format_func=lambda j: f"{suggestions[j]['Chart']} — {suggestions[j]['X']} {suggestions[j]['Y']}", key=f'u_chart_idx_{topic}')
        st.plotly_chart(localize_plot(_plot_suggestion(d, suggestions[i])), use_container_width=True, key='understanding_analyze_chart')
        st.caption(tr(suggestions[i]['Reason']))
    elif topic == 6:
        if not roles.categorical:
            st.info(tr('Need at least one categorical variable.'))
            return
        category = st.selectbox(tr('Category'), roles.categorical, key='u_barcat', format_func=lambda v: tr(str(v)))
        mode = st.radio(tr('Aggregation'), ['Count', 'Percent', 'Mean', 'Sum'], horizontal=True, key='u_baragg', format_func=lambda v: tr(str(v)))
        if mode in ('Count', 'Percent'):
            freq = frequency_table(d[category])
            key = 'Count' if mode == 'Count' else 'Percent'
            fig = px.bar(freq, x='Category', y=key, text=key, title=f'{mode} by {category}')
            st.caption(tr(f'Denominator: all {len(d)} observations, including missing categories.'))
            st.dataframe(freq, hide_index=True)
        else:
            if not roles.numeric:
                st.info(tr('Need a numerical variable for the aggregation.'))
                return
            numeric = st.selectbox(tr('Numerical variable'), roles.numeric, key='u_bar_numeric', format_func=lambda v: tr(str(v)))
            grp = d.groupby(category, dropna=False)[numeric].agg(mode.lower()).reset_index()
            fig = px.bar(grp, x=category, y=numeric, title=f'{mode} {numeric} by {category}')
        st.plotly_chart(localize_plot(apply_theme(fig)), use_container_width=True, key='understanding_analyze_group_bar')
    elif topic == 9:
        if len(d.columns) < 2:
            st.info(tr('Choose a table with two columns or more.'))
            return
        x_candidates = roles.datetime + roles.numeric
        if not x_candidates or not roles.numeric:
            st.info(tr('Provide an ordered numeric/time X variable and numeric Y variable.'))
            return
        x = st.selectbox(tr('Ordered X (time, sequence number, position)'), x_candidates, key='u_interp_x', format_func=lambda v: tr(str(v)))
        y_options = [c for c in roles.numeric if c != x]
        if not y_options:
            st.info(tr('Need a distinct numerical Y.'))
            return
        y = st.selectbox(tr('Numerical measurement with missing values'), y_options, key='u_interp_y', format_func=lambda v: tr(str(v)))
        if not st.checkbox(tr('I confirm X is meaningfully ordered, uniquely positioned, and interpolation is scientifically appropriate.'), key='u_interp_confirm'):
            st.info(tr('Confirm the meaning of X before interpolation. No data will be changed automatically.'))
            return
        try:
            filled, changes = interpolate_ordered(d, x, y)
            st.metric(tr('Interior gaps filled'), len(changes))
            chart = pd.concat([d[[x, y]].assign(Series='Original'), filled[[x, y]].assign(Series='Interpolated')], ignore_index=True)
            fig = px.line(chart, x=x, y=y, color='Series', markers=True, title='Before vs after interpolation')
            st.plotly_chart(localize_plot(apply_theme(fig)), use_container_width=True, key='understanding_analyze_interpolation')
            st.dataframe(changes, hide_index=True)
            if not changes.empty and st.button(tr('Apply interpolation to working dataset'), key='u_interp_commit'):
                st.session_state.history.append(st.session_state.working.copy(deep=True))
                st.session_state.working = filled
                st.session_state.change_log.append({'Action': 'Linear interpolation', 'Details': f'{y} along {x}: {len(changes)} internal missing values filled; no extrapolation.'})
                st.session_state.saved_tables = {}
                st.session_state.last_regression = None
                st.session_state.auto_result = None
                st.session_state.export_bundle = None
                st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    elif topic == 10:
        see_data_warnings(d)
        st.dataframe(quality_table(d, roles), hide_index=True)
        st.caption(tr('Make reversible, explicit cleaning changes in Part 1 → Organizing Tabular Data Properly.'))
    elif topic == 11:
        if not roles.categorical:
            st.info(tr('No categorical/survey response field detected.'))
            return
        answer = st.selectbox(tr('Survey response variable'), roles.categorical, key='u_survey_answer', format_func=lambda v: tr(str(v)))
        freq = frequency_table(d[answer])
        st.dataframe(freq, hide_index=True)
        save_table('survey_frequency', freq)
        st.plotly_chart(localize_plot(apply_theme(px.bar(freq, x='Category', y='Percent', title='Survey response frequency (including missing)'))), use_container_width=True, key='understanding_analyze_survey')
        groups = [c for c in roles.categorical if c != answer]
        if groups:
            group = st.selectbox(tr('Optional group comparison'), [None] + groups, key='u_survey_group', format_func=lambda v: tr(str(v)))
            if group:
                cross = pd.crosstab(d[group].fillna('(Missing)'), d[answer].fillna('(Missing)'), dropna=False)
                if not cross.empty:
                    pct = cross.div(cross.sum(axis=1), axis=0).mul(100).round(1)
                    st.write(tr('Row percentages (denominator is each grouping row)'))
                    st.dataframe(pct)
                    save_table('survey_group_percent', pct.reset_index())
        st.caption(tr('For ordinal/Likert responses, categories may have a meaningful rank; that does not by itself justify treating differences as equal.'))

def render(df):
    topic = st.selectbox(tr('Lecture topic'), [x.title for x in UNDERSTANDING], key='u_topic', format_func=lambda v: tr(str(v)))
    i = next((j for j, v in enumerate(UNDERSTANDING) if v.title == topic))
    lesson = UNDERSTANDING[i]
    lesson_header(lesson)
    a, b, c = st.tabs(localize_tabs(['Learn', 'Explore', 'Analyze']))
    with a:
        learn(lesson)
    with b:
        demo_explore(i)
    with c:
        analyze(i, df)
    st.divider()
    with st.expander(tr('Automatic dataset analysis (read-only, limited to first 12 numerical columns)')):
        if df is None:
            st.info(tr('Load data to generate the automatic overview.'))
        else:
            d, r = applied(df)
            if st.button(tr('Generate automatic analysis'), key='u_auto_run'):
                st.session_state.auto_result = auto_profile(d, r)
            profile = st.session_state.get('auto_result')
            if profile:
                for finding in profile['findings']:
                    st.write('• ' + localized_finding(finding, profile))
                st.write(tr('**Recommended charts**'))
                st.dataframe(pd.DataFrame([{k: tr(str(v)) if k in ('Chart','Reason') else v for k,v in item.items()} for item in profile['charts']]), hide_index=True)
                if not profile['numeric'].empty:
                    st.dataframe(profile['numeric'], hide_index=True)
                if not profile['pairs'].empty:
                    st.dataframe(profile['pairs'], hide_index=True)
                st.caption(tr('Automatic rules cannot determine scientific relevance or causal explanations.'))

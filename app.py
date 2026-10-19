"""Interactive Data Lab — tabular architectural research, no LLM."""
from __future__ import annotations
from ui.i18n import t as tr, localize_tabs
import hashlib
import streamlit as st
import pandas as pd
from backend.preprocess import read_uploaded_bytes, detect_column_roles, make_analysis_view, quality_table, MAX_UPLOAD_BYTES
from backend.demo_data import DEMOS
from backend.reporting import csv_bytes, zip_tables, assemble_tables, make_docx
from ui import representation, understanding, research
st.set_page_config(page_title='Interactive Data Lab | Architecture', page_icon='◆', layout='wide')
APP_CSS = '\n<style>\n:root{--page:#070B16;--panel:#0F172A;--text:#F8FAFC;--muted:#CBD5E1;--line:rgba(148,163,184,.22)}\n.stApp{background:radial-gradient(circle at 9% 0%,rgba(96,165,250,.17),transparent 32%),radial-gradient(circle at 89% 9%,rgba(167,139,250,.12),transparent 25%),linear-gradient(180deg,#070B16,#0F172A);color:var(--text)}\n.block-container{padding-top:1.5rem;max-width:1490px;padding-bottom:4rem}\n[data-testid="stSidebar"]{background:rgba(15,23,42,.9);border-right:1px solid var(--line)}\n.stMetric{background:#14203B;border:1px solid var(--line);padding:10px 15px;border-radius:14px}\nheader[data-testid="stHeader"]{background:transparent}\n.hero{padding:1.3rem 1.55rem 1.1rem;background:linear-gradient(135deg,#131c32,#172542);border:1px solid var(--line);border-radius:22px;margin:0 0 1rem}\n.kicker{font-size:.78rem;font-weight:800;letter-spacing:.09em;color:#96BFFF;text-transform:uppercase}\n.hero h1{font-size:2.25rem;margin:5px 0 9px;color:white}\n.hero p{margin:0;color:#D1DBE9}\n</style>\n'
st.markdown(APP_CSS, unsafe_allow_html=True)

def init():
    defaults = {'raw': None, 'working': None, 'file_name': '', 'dataset_id': None, 'history': [], 'change_log': [], 'role_overrides': {}, 'saved_tables': {}, 'last_regression': None, 'regression_signature': None, 'pending_clean': None, 'auto_result': None, 'export_bundle': None, 'ui_language':'en'}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def load(df: pd.DataFrame, label: str, fingerprint: str):
    if st.session_state.dataset_id == fingerprint:
        return
    st.session_state.raw = df.copy(deep=True)
    st.session_state.working = df.copy(deep=True)
    st.session_state.dataset_id = fingerprint
    st.session_state.file_name = label
    st.session_state.role_overrides = {}
    st.session_state.history = []
    st.session_state.change_log = []
    st.session_state.saved_tables = {}
    st.session_state.last_regression = None
    st.session_state.regression_signature = None
    st.session_state.pending_clean = None
    st.session_state.auto_result = None
    st.session_state.export_bundle = None

def sidebar():
    with st.sidebar:
        st.markdown('### ◆ Interactive Data Lab')
        st.radio('Language / ภาษา', ['English', 'ไทย'], index=0 if st.session_state.get('ui_language','en')=='en' else 1, key='language_toggle', horizontal=True, on_change=lambda:st.session_state.update(ui_language='th' if st.session_state.language_toggle=='ไทย' else 'en'))
        st.caption(tr('Tabular data only · No LLM · Local computation'))
        uploaded = st.file_uploader(tr('Upload CSV / Excel'), type=['csv', 'xlsx', 'xls'], key='upload')
        if uploaded is not None:
            try:
                raw = uploaded.getvalue()
                if len(raw) > MAX_UPLOAD_BYTES:
                    raise ValueError('Upload maximum: 15 MB')
                fid = 'upload-' + hashlib.sha256(raw + uploaded.name.encode()).hexdigest()
                if st.session_state.dataset_id != fid:
                    load(read_uploaded_bytes(raw, uploaded.name), uploaded.name, fid)
            except Exception as exc:
                st.error(tr(f'Upload failed: {exc}'))
        st.divider()
        st.caption(tr('Or load a synthetic architecture teaching dataset:'))
        demo = st.selectbox(tr('Demonstration dataset'), ['No demo'] + list(DEMOS), key='demo_selection', format_func=lambda v: tr(str(v)))
        if demo != 'No demo' and st.button(tr('Load demo dataset'), key='load_demo'):
            load(DEMOS[demo](), demo, 'demo-' + demo)
            st.rerun()
        if st.session_state.working is not None:
            d = st.session_state.working
            st.success(tr(f'{st.session_state.file_name}\n\n{len(d)} observations · {len(d.columns)} variables'))
            if st.button(tr('Reset to untouched original'), key='reset_data'):
                st.session_state.working = st.session_state.raw.copy(deep=True)
                st.session_state.history = []
                st.session_state.change_log = []
                st.session_state.saved_tables = {}
                st.session_state.last_regression = None
                st.session_state.regression_signature = None
                st.session_state.pending_clean = None
                st.session_state.auto_result = None
                st.session_state.export_bundle = None
                st.rerun()
            with st.expander(tr('Variable role overrides')):
                col = st.selectbox(tr('Variable'), list(d.columns), key='role_column', format_func=lambda v: tr(str(v)))
                current = st.session_state.role_overrides.get(col, 'Auto')
                roles = ['Auto', 'Numeric', 'Categorical', 'Datetime', 'Boolean', 'Identifier']
                role = st.selectbox(tr('Scientific role'), roles, index=roles.index(current) if current in roles else 0, key='role_new', format_func=lambda v: tr(str(v)))
                st.caption(tr('Changing a role may convert strings to missing values in the analysis view. It does not change your raw/working table.'))
                if st.button(tr('Apply role override'), key='role_commit'):
                    if role == 'Auto':
                        st.session_state.role_overrides.pop(col, None)
                    else:
                        st.session_state.role_overrides[col] = role
                    st.session_state.last_regression = None
                    st.session_state.saved_tables = {}
                    st.session_state.auto_result = None
                    st.session_state.export_bundle = None
                    st.rerun()
                if st.session_state.role_overrides:
                    st.json(st.session_state.role_overrides)
        st.divider()
        st.caption(tr('Inspired by Research Methods in Architecture, slides 12–29, 45–78. Ends at numeric regression.'))
        st.caption(tr('All demo data are synthetic. Do not use their numerical findings as empirical research results.'))

def export_tab():
    st.subheader(tr('Research Report & Export'))
    st.write(tr('Download your working data, tabulated results and a transparent methodology summary. The original file is never overwritten.'))
    raw = st.session_state.raw
    work = st.session_state.working
    if work is None:
        st.info(tr('Choose a synthetic demo or upload a CSV/Excel dataset before exporting.'))
        return
    if st.button(tr('Prepare reproducible exports'), type='primary', key='prepare_exports'):
        d = make_analysis_view(work, st.session_state.role_overrides)
        roles = detect_column_roles(work, st.session_state.role_overrides)
        run = st.session_state.last_regression
        if run is not None and st.session_state.regression_signature != (st.session_state.dataset_id, tuple(sorted(st.session_state.role_overrides.items()))):
            run = None
        with st.spinner(tr('Preparing research tables and Word report...')):
            tables = assemble_tables(d, roles, run, st.session_state.change_log)
            tables.update(st.session_state.saved_tables)
            docx = make_docx(d, st.session_state.file_name, raw.shape, st.session_state.change_log, roles, run, lang=st.session_state.get('ui_language','en'))
            st.session_state.export_bundle = {'csv': csv_bytes(work), 'zip': zip_tables(tables), 'docx': docx, 'table_names': list(tables), 'table_rows': [len(v) for v in tables.values()]}
    bundle = st.session_state.export_bundle
    if not bundle:
        st.info(tr('Click “Prepare reproducible exports” after confirming the analysis and cleaning decisions. Files will only be generated on demand.'))
        return
    c1, c2, c3 = st.columns(3)
    c1.download_button(tr('Download working CSV'), bundle['csv'], file_name='interactive_data_working.csv', mime='text/csv', use_container_width=True)
    c2.download_button(tr('Download tables ZIP'), bundle['zip'], file_name='interactive_data_tables.zip', mime='application/zip', use_container_width=True)
    c3.download_button(tr('Download research DOCX'), bundle['docx'], file_name='interactive_data_research_summary.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document', use_container_width=True)
    st.write(tr('**Available result tables**'))
    st.dataframe(pd.DataFrame({'Table': bundle['table_names'], 'Rows': bundle['table_rows']}), hide_index=True)
    st.write(tr('**Transformation audit**'))
    if st.session_state.change_log:
        st.dataframe(pd.DataFrame(st.session_state.change_log), hide_index=True)
    else:
        st.caption(tr('No transformations were approved; working data are unchanged.'))
    st.caption(tr('Report is generated locally, with deterministic statistical descriptions. Figures use Matplotlib and do not need Kaleido.'))

def main():
    init()
    sidebar()
    st.markdown(f'<div class="hero"><div class="kicker">{tr("Architectural research · Interactive lecture companion")}</div><h1>Interactive Data Lab</h1><p>{tr("Represent tabular data → understand patterns → learn regression → report results. Transparent analysis without an LLM.")}</p></div>', unsafe_allow_html=True)
    tabs = st.tabs(localize_tabs(['1  Data Representation', '2  Understanding Data', '3  From Data to Research', '4  Report & Export']))
    with tabs[0]:
        representation.render(st.session_state.working)
    with tabs[1]:
        understanding.render(st.session_state.working)
    with tabs[2]:
        research.render(st.session_state.working)
    with tabs[3]:
        export_tab()
if __name__ == '__main__':
    main()

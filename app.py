"""Interactive Data Lab — tabular architectural research, no LLM."""
from __future__ import annotations
from ui.i18n import t as tr, localize_tabs
import hashlib
import streamlit as st
import pandas as pd
from backend.preprocess import (read_uploaded_bytes, excel_sheet_names, detect_column_roles,
    make_analysis_view, quality_table, MAX_UPLOAD_BYTES, CSV_ENCODINGS, CSV_DELIMITERS)
from backend.demo_data import DEMOS
from backend.reporting import csv_bytes, zip_tables, assemble_tables, make_docx
from ui import representation, understanding, research
st.set_page_config(page_title='Interactive Data Lab | Architecture', page_icon='◆', layout='wide')
APP_CSS = '\n<style>\n:root{--page:#070B16;--panel:#0F172A;--text:#F8FAFC;--muted:#CBD5E1;--line:rgba(148,163,184,.22)}\n.stApp{background:radial-gradient(circle at 9% 0%,rgba(96,165,250,.17),transparent 32%),radial-gradient(circle at 89% 9%,rgba(167,139,250,.12),transparent 25%),linear-gradient(180deg,#070B16,#0F172A);color:var(--text)}\n.block-container{padding-top:1.5rem;max-width:1490px;padding-bottom:4rem}\n[data-testid="stSidebar"]{background:rgba(15,23,42,.9);border-right:1px solid var(--line)}\n.stMetric{background:#14203B;border:1px solid var(--line);padding:10px 15px;border-radius:14px}\nheader[data-testid="stHeader"]{background:transparent}\n.hero{padding:1.3rem 1.55rem 1.1rem;background:linear-gradient(135deg,#131c32,#172542);border:1px solid var(--line);border-radius:22px;margin:0 0 1rem}\n.kicker{font-size:.78rem;font-weight:800;letter-spacing:.09em;color:#96BFFF;text-transform:uppercase}\n.hero h1{font-size:2.25rem;margin:5px 0 9px;color:white}\n.hero p{margin:0;color:#D1DBE9}\n</style>\n'
st.markdown(APP_CSS, unsafe_allow_html=True)

@st.cache_data(show_spinner=False, max_entries=3)
def cached_upload(raw: bytes, filename: str, sheet: str | int, header_row: int,
                  encoding: str, delimiter: str) -> pd.DataFrame:
    """Decode for a preview; reuse exactly the same table on confirmation."""
    return read_uploaded_bytes(raw, filename, sheet_name=sheet,
                               header_row=header_row, csv_encoding=encoding,
                               csv_delimiter=delimiter)


@st.cache_data(show_spinner=False, max_entries=3)
def cached_sheets(raw: bytes, filename: str) -> list[str]:
    return excel_sheet_names(raw, filename)


def init():
    defaults = {
        'raw': None, 'working': None, 'file_name': '', 'dataset_id': None,
        'dataset_source': '', 'dataset_description': '', 'history': [],
        'change_log': [], 'role_overrides': {}, 'saved_tables': {},
        'last_regression': None, 'regression_signature': None,
        'pending_clean': None, 'auto_result': None, 'export_bundle': None,
        'ui_language': 'en'
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def load(df: pd.DataFrame, label: str, fingerprint: str,
         source: str = 'upload', description: str = '') -> None:
    """Only called by explicit confirmation buttons, never file selection."""
    st.session_state.raw = df.copy(deep=True)
    st.session_state.working = df.copy(deep=True)
    st.session_state.dataset_id = fingerprint
    st.session_state.file_name = label
    st.session_state.dataset_source = source
    st.session_state.dataset_description = description
    # A new confirmation replaces the old working set and clears stale results.
    st.session_state.role_overrides = {}
    st.session_state.history = []
    st.session_state.change_log = []
    st.session_state.saved_tables = {}
    st.session_state.last_regression = None
    st.session_state.regression_signature = None
    st.session_state.pending_clean = None
    st.session_state.auto_result = None
    st.session_state.export_bundle = None


def fingerprint_upload(raw: bytes, filename: str, sheet: str | int,
                       header_row: int, encoding: str, delimiter: str) -> str:
    options = f'{filename}\n{sheet}\n{header_row}\n{encoding}\n{delimiter}'.encode('utf-8')
    return 'upload-' + hashlib.sha256(raw + options).hexdigest()


def sidebar():
    with st.sidebar:
        st.markdown('### ◆ Interactive Data Lab')
        st.radio('Language / ภาษา', ['English', 'ไทย'],
                 index=0 if st.session_state.get('ui_language', 'en') == 'en' else 1,
                 key='language_toggle', horizontal=True,
                 on_change=lambda: st.session_state.update(
                     ui_language='th' if st.session_state.language_toggle == 'ไทย' else 'en'))
        st.caption(tr('Tabular data only · No LLM · Local computation'))

        st.markdown('#### ' + tr('1. Upload your dataset'))
        uploaded = st.file_uploader(tr('Select CSV / Excel file'),
                                    type=['csv', 'xlsx', 'xls'], key='upload')
        if uploaded is None:
            st.caption(tr('Choose a file, check its preview, then confirm to analyze it.'))
        else:
            try:
                raw = uploaded.getvalue()
                if not raw:
                    raise ValueError(tr('The uploaded file is empty.'))
                if len(raw) > MAX_UPLOAD_BYTES:
                    raise ValueError(tr('The file exceeds the 100 MB limit.'))
                filename = uploaded.name
                # A newly selected file gets fresh import defaults. Otherwise
                # an old header-row/worksheet setting can make it look broken.
                selected_token = hashlib.sha256(raw + filename.encode('utf-8')).hexdigest()
                if st.session_state.get('_upload_selection_token') != selected_token:
                    for setting in ('import_sheet', 'import_header', 'import_encoding', 'import_delimiter'):
                        st.session_state.pop(setting, None)
                    st.session_state._upload_selection_token = selected_token
                suffix = filename.lower().rsplit('.', 1)[-1]
                st.caption(tr('Selected file (not automatically loaded):') + f' {filename} '
                           f'({len(raw) / 1024 / 1024:.2f} MB)')
                with st.expander(tr('Import settings — worksheet, heading row, CSV format')):
                    if suffix in ('xlsx', 'xls'):
                        sheets = cached_sheets(raw, filename)
                        sheet = st.selectbox(tr('Worksheet'), sheets, key='import_sheet')
                        encoding = 'Auto'
                        delimiter = 'Auto'
                    else:
                        sheet = 0
                        encoding = st.selectbox(tr('CSV text encoding'),
                                                list(CSV_ENCODINGS), key='import_encoding')
                        delimiter = st.selectbox(tr('CSV column separator'),
                                                 list(CSV_DELIMITERS), key='import_delimiter')
                    header_row = int(st.number_input(tr('Heading row (1 = first row)'),
                                         min_value=1, max_value=1000, value=1,
                                         step=1, key='import_header'))
                preview_df = cached_upload(raw, filename, sheet, header_row,
                                            encoding, delimiter)
                st.caption(tr('Preview of selected dataset:'))
                st.dataframe(preview_df.head(8), hide_index=True, use_container_width=True)
                st.caption(f'{len(preview_df):,} × {len(preview_df.columns):,} '
                           + tr('rows × columns'))
                if len(preview_df.columns) == 1:
                    st.warning(tr('Only one column was detected. If you expected more, check the CSV column separator.'))
                if any(str(col).startswith('Unnamed:') for col in preview_df.columns):
                    st.warning(tr('Unnamed columns found. Check the heading row.'))
                fid = fingerprint_upload(raw, filename, sheet, header_row,
                                         encoding, delimiter)
                if fid == st.session_state.dataset_id:
                    st.success(tr('This uploaded dataset is currently active.'))
                else:
                    st.info(tr('Selected file is a preview only. Confirm below to use it for every analysis.'))
                if st.button(tr('Confirm & Use Uploaded Dataset'),
                             key='confirm_uploaded_dataset', type='primary',
                             use_container_width=True):
                    description = (f'{filename} · '
                                   + (f'{tr("worksheet")}: {sheet} · ' if suffix in ('xlsx', 'xls') else '')
                                   + f'{tr("heading row")}: {header_row}')
                    load(preview_df, filename, fid, source='upload', description=description)
                    st.rerun()
            except Exception as exc:
                st.error(tr('Cannot preview the selected file:') + f' {exc}')
                st.caption(tr('Adjust the import settings or try a different CSV encoding. Your active dataset is unchanged.'))

        st.divider()
        st.markdown('#### ' + tr('2. Or use a demonstration dataset'))
        demo = st.selectbox(tr('Demonstration dataset'), ['No demo'] + list(DEMOS),
                            key='demo_selection', format_func=lambda v: tr(str(v)))
        if demo != 'No demo':
            demo_df = DEMOS[demo]()
            st.caption(tr('Demo preview — confirm before loading:'))
            st.dataframe(demo_df.head(5), hide_index=True, use_container_width=True)
            st.caption(f'{len(demo_df):,} × {len(demo_df.columns):,} '
                       + tr('rows × columns'))
            if st.session_state.dataset_id == 'demo-' + demo:
                st.success(tr('This demo dataset is currently active.'))
            else:
                st.info(tr('Selected demo is a preview only.'))
            if st.button(tr('Confirm & Use Demo Dataset'), key='confirm_demo_dataset',
                         use_container_width=True):
                load(demo_df, demo, 'demo-' + demo, source='demo', description=demo)
                st.rerun()

        st.divider()
        st.markdown('#### ' + tr('3. Active dataset'))
        if st.session_state.working is None:
            st.warning(tr('No active dataset yet. Confirm an uploaded file or a demo above.'))
        else:
            d = st.session_state.working
            st.success(tr('Currently analyzing:') + f' **{st.session_state.file_name}**')
            st.caption(st.session_state.dataset_description)
            st.caption(f'{len(d):,} ' + tr('observations') + f' · {len(d.columns):,} '
                       + tr('variables'))
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
                col = st.selectbox(tr('Variable'), list(d.columns), key='role_column',
                                   format_func=lambda v: tr(str(v)))
                current = st.session_state.role_overrides.get(col, 'Auto')
                roles = ['Auto', 'Numeric', 'Categorical', 'Datetime', 'Boolean', 'Identifier']
                role = st.selectbox(tr('Scientific role'), roles,
                                    index=roles.index(current) if current in roles else 0,
                                    key='role_new', format_func=lambda v: tr(str(v)))
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
    if st.session_state.working is None:
        st.info(tr('Start by selecting and confirming a CSV/Excel file or a demo dataset in the sidebar.'))
    else:
        st.success(tr('Currently analyzing:') + f' **{st.session_state.file_name}** '
                   f'({len(st.session_state.working):,} ' + tr('observations') + ')')
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

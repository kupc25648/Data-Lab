# Interactive Data Lab — Tabular Data for Architectural Research

Bilingual (English / ไทย) Streamlit teaching and applied research platform aligned to *Research Methods in Architecture*, slides **13–29, 45–78**, restricted to **CSV/Excel tables and numeric regression**.

## Start

```bash
cd Interactive_Data_Lab
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

On macOS you may also run `START_MAC.command` after installing the dependencies.

Use the **Language / ภาษา** switch in the sidebar to choose English or Thai. All 22 lesson descriptions, topic selectors, instructional controls, limitations, and contextual glossary terms are localized. User-provided dataset column names remain unchanged; scientific measurement labels in tables remain in English for reproducibility. Downloaded Word research summaries follow the selected UI language.

Each **Learn** section includes a *Key terms & further reading* expander with brief definitions and direct Wikipedia / GeeksforGeeks articles; links require an internet connection only when clicked. The app itself does not retrieve or send data to these websites.

Open the local URL that Streamlit prints (typically http://localhost:8501). No OpenAI key, cloud account, or external model is required.

## Use

1. Upload a CSV/XLSX/XLS file (15 MB maximum), or load one of four included synthetic demo datasets.
2. Work through **Data Representation → Understanding Data → From Data to Research**. Every topic has **Learn**, **Explore** (no upload required), and **Analyze**.
3. Raw data are retained; approved changes affect only the working copy and can be undone. Inspect scientific roles in the sidebar; type overrides only affect analysis views.
4. In Understanding Data, run **automatic analysis** to generate bounded summaries, potential relationships, and chart recommendations. Correlations are exploratory, not causal.
5. For regression, **you** select a numeric target and predictors. Choose an appropriate random, grouped, or chronological split. Linear regression is the teaching default. Optional advanced regression selects candidates using **training-only CV**, with a separate test set for final metrics.
6. Export the working CSV, result tables ZIP, and a DOCX report including methodology, training/test sizes, selected tables, an illustrative figure, and an audit log.

## Architecture

- `app.py`: four-tab Streamlit shell and session-state data lifecycle.
- `ui/`: lecture-aligned interfaces (representation, understanding, research).
- `backend/lessons.py`: slide-mapped lesson definitions and example snippets.
- `backend/preprocess.py`: safe read-only ingestion, roles, frequencies, approved reversible cleaning.
- `backend/auto_analysis.py`: descriptive statistics, bounded correlation scan, chart suggestions.
- `backend/interpolation.py`: internal-only interpolation with saved value provenance.
- `backend/regression.py`: leakage-aware numeric regression model selection and test reporting.
- `backend/reporting.py`: CSV/ZIP and DOCX with tables/figures.
- `backend/*_legacy.py`: uploaded V2 reference functions retained for continuity (not used by main UI).
- `backend/visualization.py`, `backend/statistics.py`, `backend/correlation.py`, `backend/profiling.py`: reusable V2 analytical helpers.
- `tests/`: test coverage for ingestion, preparation, interpolation, auto analysis, regression, export.

## Methodological boundaries

- Input: tabular CSV/Excel **only**. No image or graph analysis, no classification, generative AI, embeddings, multimodal models, or LLM APIs.
- Automatic analysis never decides what a variable means scientifically; review variable units and study design.
- Imported CSV with malformed rows raises an error rather than silently skipping records.
- `Role override=Numeric` converts nonnumeric text to missing **in the analysis view only**; review before statistical use.
- Correlation screening reports **unadjusted p values** and warns about searching multiple relationships; do not infer causation.
- Interpolation requires unique, meaningful X coordinates and user confirmation. It fills internal gaps only, never extrapolates.
- Regression needs >=25 known-target observations. Pipelines fit imputation/encoding on training partitions inside CV. Advanced model selection compares **CV MAE**, not test scores.
- Repeated measures must use grouped splitting where meaningful; time series should use chronological splitting. These cannot replace full scientific validation.
- All bundled demos are synthetically generated, and their results are not empirical findings.

## Tests

```bash
python -m pytest -q
```

If Streamlit is installed, use `streamlit.testing.v1.AppTest` for a UI smoke test. A separate `tests/test_ui.py` includes a basic Streamlit smoke test where installed. See `TEST_RESULTS.md` for verified and unverified parts.


## Bilingual verification

```bash
python tests/smoke_bilingual.py
```

The bilingual smoke test uses an offline Streamlit stand-in and verifies all 22 lesson paths in both languages, appropriate reading links, and Thai DOCX output. It is not a replacement for a real-browser acceptance test.

## Streamlit Plotly duplicate ID fix (19 October 2026)

If you previously encountered `StreamlitDuplicateElementId` in `ui/understanding.py`, this build fixes it by giving every Plotly chart its own stable `key=`. This is a UI-only fix; analysis methods and dataset files have not changed.

To update an existing installation without replacing the full project, copy the following three files from the updated ZIP into the same paths in your existing `Interactive_Data_Lab` directory, overwriting them:

- `ui/representation.py`
- `ui/understanding.py`
- `ui/research.py`

Restart Streamlit (`Ctrl+C`, then `streamlit run app.py`) and refresh your browser. To run the non-browser regression check: `python tests/smoke_plotly_keys.py`.

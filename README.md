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

1. **Select** a CSV/XLSX/XLS file (100 MB maximum) in the sidebar, inspect the table preview, then press **Confirm & Use Uploaded Dataset**. For a built-in demo, select its name, inspect its preview and press **Confirm & Use Demo Dataset**. Merely selecting a source never changes the active dataset.
2. Check **3. Active dataset** in the sidebar or the **Currently analyzing:** banner at the top of the page. Only the confirmed file/demo is used for **Data Representation → Understanding Data → From Data to Research**. Every topic has **Learn**, **Explore** (no upload required), and **Analyze**.
3. Raw data are retained; approved changes affect only the working copy and can be undone. Inspect scientific roles in the sidebar; type overrides only affect analysis views.
4. In Understanding Data, run **automatic analysis** to generate bounded summaries, potential relationships, and chart recommendations. Correlations are exploratory, not causal.
5. For regression, **you** select a numeric target and predictors. Choose an appropriate random, grouped, or chronological split. Linear regression is the teaching default. Optional advanced regression selects candidates using **training-only CV**, with a separate test set for final metrics.
6. Export the working CSV, result tables ZIP, and a DOCX report including methodology, training/test sizes, selected tables, an illustrative figure, and an audit log.


## Uploading your own data — confirm before use

- **CSV:** select the `.csv` file. Check the first eight rows in the preview, and click **Confirm & Use Uploaded Dataset**. When the file is confirmed, the banner shows its filename and the active observation count.
- **Excel:** select `.xlsx` or `.xls`, optionally open **Import settings** to select the worksheet and the row containing column names. Confirm after verifying the preview.
- **Demo:** select a demo from the second section of the sidebar, inspect its preview, and click **Confirm & Use Demo Dataset**. The demo does not replace your uploaded dataset without that click.
- **If CSV preview is wrong:** open **Import settings**, choose the correct CSV text encoding (UTF-8, Thai CP874, CP1252, UTF-16, etc.), column separator (comma, semicolon, tab, or pipe), and header row. The app does not skip bad rows silently.
- **If the file is very large:** the upload limit is 100 MB and large workbooks may require considerable memory. A rejected file is not made active.
- **To start again with the same active dataset:** choose **Reset to untouched original**, which discards approved working-copy transformations but keeps the raw upload unchanged.

Any change to the selected file or demo only changes the *preview* until its own confirmation button is pressed. Once confirmed, the new table replaces both `raw` and `working`, and cached analysis results and manual role settings from the previous table are cleared.

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

## Confirmed upload workflow update — 27 October 2026

- Explicit **Confirm & Use Uploaded Dataset** and **Confirm & Use Demo Dataset** buttons; a preview is not the active dataset.
- The previously confirmed dataset stays active if you explore a different source but do not confirm it.
- CSV import now has selectable encoding, delimiter, and heading row; Excel supports worksheet selection and heading row. Import choices reset when choosing a different file.
- Raised hard app limit from 15 MB to 100 MB and aligned the Streamlit upload limit.
- Current source and active filename are visible in the sidebar and above the teaching tabs.
- `python tests/smoke_upload_confirmation.py` exercises transitions between pending upload, confirmed upload, and confirmed demo, including Thai CP874 CSV and multi-sheet Excel.

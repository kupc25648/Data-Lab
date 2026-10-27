# Verification note — Interactive Data Lab

Initial project checked on 18 October 2026; bilingual update checked on 19 October 2026:

- Python byte-compilation: passed.
- Pytest: **11 backend tests passed**; **1 Streamlit integration test skipped** because Streamlit is not installed in this execution environment.
- Offline simulated UI execution: **22/22 lecture topic routes passed** using a lightweight stand-in for Streamlit. This validates the Python control paths but is **not** an actual interactive-browser test.
- Research DOCX export: generated, rendered to three pages, and visually checked for legible tables and figures.
- Regression tests include training-only CV, final holdout metrics, grouped/chronological splits, reproducible runs and insufficient-data safeguards.
- Interpolation tests include internal gaps, no extrapolation, and original-data preservation.

**Environment limitation:** Package installation was blocked by unavailable external network/DNS, so the real Streamlit UI could not be launched in the container. Install `requirements.txt` locally and run the app for a final interactive verification. This is delivered as a functional source project, not a hosted deployment.


## Bilingual update — 19 October 2026
- Renamed application (page title, sidebar, hero, report heading and filenames) to **Interactive Data Lab**; no visible version number.
- English/Thai language switch, full lesson descriptions for 22 topics, common controls, research cautions, auto-analysis narrative, plot headings and contextual key-term glossary.
- Curated Wikipedia / GeeksforGeeks reading URLs appear only as optional links; no background network activity.
- Research DOCX can be generated in English or Thai and the Thai sample was rendered to 3 pages for visual inspection.
- 11 backend pytest checks passed; English and Thai offline 22-route smoke tests passed.
- A real Streamlit browser run remains unverified due to missing Streamlit package in this execution environment.

## Plotly element ID bug fix — 19 October 2026

User reported `streamlit.errors.StreamlitDuplicateElementId` in `ui/understanding.py:126` on the `plotly_chart` call. Root cause: when different tabs or routes generate charts with identical parameters, Streamlit may derive the same automatic element ID. The app rendered both the **Explore** and **Analyze** tab bodies during each run.

**Resolution:** All 19 Plotly chart calls in `ui/representation.py`, `ui/understanding.py`, and `ui/research.py` now have explicit unique, stable keys. This makes widget identity independent of figure contents.

**Regression checks:**
- `python tests/smoke_plotly_keys.py`: 19 unique stable key declarations, plus 44 simulated page renders across English and Thai. **Passed**.
- `python -m pytest -q tests/test_backend.py tests/test_ui.py`: **11 passed, 1 skipped** (Streamlit not installed in this environment).
- `python -m compileall -q app.py ui backend tests`: **Passed**.

**Testing limitation:** The smoke tests use a stand-in Streamlit API; a real running Streamlit browser session is still unverified in this environment.

## CSV/Excel confirmation and activation update — 27 October 2026

- Backend/import pytest: **18 passed**, **1 integration test skipped** because Streamlit is not installed.
- New upload-state smoke test: **passed** for preview without activation, explicit upload confirmation, explicit demo confirmation, switching sources only on confirmation, correct Excel worksheet/header, and Thai CP874 CSV.
- Bilingual route simulation: **44 routes passed** (22 topics × 2 languages).
- Plotly explicit-key check: **19 chart declarations passed**.
- **Limitation:** real Streamlit execution and a test with the user's own CSV are not available here; Streamlit package installation failed due to DNS/network restrictions.

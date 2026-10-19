# Interactive Data Lab — Lecture-Aligned Tabular Data Analysis

**Development specification · 18 October 2026**  
**Basis:** `ResearchMethodComp(2).pdf` (98 slides) and the nine uploaded V2 Python files.  
**Status:** approved product scope; specification only, no V3 code changes yet.

## 1. Product objective

Build a no-LLM, Streamlit-based learning and applied research platform in which architecture students upload tabular data (CSV/Excel), learn the concepts from the lecture, explore methods interactively, run appropriate automatic analyses, and export reproducible findings. Mirror the lecture's conceptual progression rather than presenting an unrelated collection of tools:

1. **Data (Representation)** — lecture slides 12–29 and 45–46, limited to tabular data.
2. **Understanding Data (Data Processing)** — lecture slides 47–73.
3. **From Data to Research** — lecture slides 75–78, ending with numeric prediction through regression.
4. **Report & Export** — practical output across sections; not a separate lecture chapter.

**Out of scope for the main workflow:** image processing, graph processing, classification, generative AI, embedding methods, multimodal AI, external LLM/API use, causal discovery, general-purpose AutoML, user authentication and cloud-hosted data storage. Lecture slides 30–44 and 79 onward do not become app modules. Advanced V2 methods may be preserved in a separate, collapsed toolbox, but never presented as part of the main lecture sequence.

## 2. Navigation and pedagogy

Use a persistent dataset sidebar (Upload, dataset information, reset, data version) and four top-level Streamlit tabs: **1. Data Representation**, **2. Understanding Data**, **3. From Data to Research**, **4. Report & Export**.

Every instructional topic uses a consistent **Learn → Explore → Analyze** organization:

- **Learn:** plain-language explanation, mathematical notation or formula where useful, architectural example, methodology caveats, and slide-number cross-reference.
- **Explore:** small, interactive, built-in synthetic example that works even without an uploaded dataset; charts and numbers update when controls change.
- **Analyze:** apply the technique to the uploaded tabular dataset; provide suitable automatic defaults while preserving user choice, dataset validity warnings, and methods visibility.
- Optional **Show Python** expandable area: the equivalent pandas/scipy/scikit-learn operation with specified inputs, preprocessing, random seed, and results. Python code must match what the app actually runs.

Avoid reusing a single giant form for all analysis. Make automatic actions explain *why* a variable/chart/method was selected. Calculated results and interpretation must be clearly separated. Analysis can be automatic; research purpose and causal claims cannot be inferred from data alone.

## 3. Traceability matrix: lecture → V3 requirements

### Part 1: Data (Representation)

| Slide(s) | Lecture topic | Current V2 support | V3 acceptance requirement |
|---|---|---|---|
| 13–16 | Why representation matters | No explicit lesson | Explain the transformation from building observations to quantitative variables, with an architecture mini-example |
| 17–20 | Tabular data: spreadsheet thinking | Overview table / raw preview | Visually label row = observation; column = variable, show a small building/room dataset and selected row/column |
| 21–24 | Categorical data | Type detection, categorical summaries, internal one-hot encoder for ML | Distinguish nominal categories, frequencies; interactive before/after one-hot table, avoiding false numerical ordering |
| 25–27 | Numerical data | Numeric type detection | Show continuous vs discrete examples, distribution and meaningful operations; allow correction of a misidentified field |
| 28–29 | Organizing tables | Preprocess and column quality | Detect missing cells, duplicate observations, bad column names, potential inconsistent units/format; review and approve each change |
| 45–46 | Why tabular, transition to processing | Implied | Brief lesson connecting prepared rows/columns with mean, standard deviation and correlation; no image/graph modules |

### Part 2: Understanding Data (Data Processing)

| Slide(s) | Lecture topic | Current V2 support | V3 acceptance requirement |
|---|---|---|---|
| 48–51 | Why statistics matter | Numeric/categorical summaries | Explain when summary statistics help and how summaries can hide individual patterns |
| 52 | Mean | `numeric_summary` | Show formula, interactive points, mean marker, change from adding an outlier; explain mean vs median |
| 53 | Standard deviation | `numeric_summary` | Visual comparison of same mean with different spread; show sample SD convention (`ddof=1`) and units |
| 54–57 | Correlation, scatter, interpretation | Pearson/Spearman, pair rankings, significance, heatmap | Interpret direction/magnitude and sample size, interactive example; emphasize correlation is not causation, nonlinearity and outliers |
| 58–61 | Visualization purpose | Plotly charts | Show purpose: pattern, outlier, trend, communication; avoid misleading aggregations |
| 62–65 | Scatter plot | Plotly scatter and OLS trendline | Interactive x/y choice; identify observations and show optional trendline; explain chart selection |
| 66 | Bar chart | Category count/aggregated values | Distinguish count, percent, mean, and sum; respect denominators and label aggregation |
| 67 | Choose the right chart | Manual Visualization Lab | Auto recommendations by question/data role (distribution→histogram; numerical relationship→scatter; category counts→bar; grouped numeric comparison→bar or box) with explanation |
| 68–70 | Colab: running stats and plots | Streamlit substitutes already exist | Replace Colab tool demonstrations with matching Streamlit Learn/Explore/Analyze and optional equivalent Python code, not a standalone Colab tutorial |
| 71 | Linear interpolation | Not implemented | Interactive ordered x–y series; estimate internal missing points with before/after chart; avoid extrapolation; log inserted values; disable when order is not meaningful |
| 72 | Real research data | Import/clean/profiling | Separate raw vs cleaned dataframe, cleaning summary/change log, column-role overrides, reversible operations; preserve uploaded file |
| 73 | Survey data | Categorical frequencies | Counts and percentages, missing/unknown responses, compare responses by a chosen categorical group; make Likert coding and denominator explicit |

### Part 3: From Data to Research — regression only

| Slide(s) | Lecture topic | Current V2 support | V3 acceptance requirement |
|---|---|---|---|
| 75 | What is prediction? | `run_model_comparison` | Identify features X and numeric target y; distinguish observed/predicted values from explanation or causality |
| 76 | Regression definition | Linear Regression is available | Interactive simple linear regression (scatter, fitted line, equation, residual arrows), optional input for predicted y |
| 77 | Learn relationships | Coefficients / model predictions | Explain association vs fitted regression, training/test separation, error; no target chosen implicitly |
| 78 | Architectural use cases | Generic dataset/demo support | Offer sample tasks such as floor area→cost or outdoor temperature→energy use, and user data support |

Main teaching path should start with **simple linear regression**, move to multiple linear regression if suitable, and only then optionally expose Ridge, Random Forest, Gradient Boosting, KNN, and SVR as advanced regression comparisons. No classification in the main V3 workflow.

## 4. Automatic analysis behavior

### At import (automatic, read-only)

- Validate file type/size and parse CSV/Excel; present errors instead of silently discarding records.
- Show number of observations/variables and tentative data roles: categorical, numeric, datetime, identifiers; allow user overrides.
- Summarize missingness, duplicate rows, distinct values, potential parse issues, and numeric distributions. Flag questionable values without deleting them.
- Preserve raw uploaded data and store cleaned/working version separately; actions taken to alter data are user-confirmed and recorded.

### Understanding Data (automatic, bounded)

- Produce descriptive statistics for valid numerical fields (n, mean, median, standard deviation, min/max, quartiles, missingness).
- Suggest a small selection of plots appropriate to variable types rather than rendering every possible pair.
- Correlation review: exclude identifier-like fields, distinguish Pearson/Spearman assumptions, display pairwise n, warn on missingness/multiple comparisons; charts support interpretation rather than causal conclusions.
- Provide survey frequency tables for categorical fields, with clear percentages and denominator.
- Offer interpolation only with a meaningful ordered index/time or x coordinate; do not auto-impute all missing values.

### From Data to Research (guided, not fully automatic)

- Require learner to select a numeric prediction target y and eligible features X, and confirm variable roles and units.
- Default first analysis: simple or multiple ordinary least squares, using train/validation/test as appropriate.
- If advanced comparison is enabled, compare through training-only cross-validation and evaluate the chosen model once on an untouched test set; preprocessing fits only to training splits.
- Report n train/test, random state or temporal split, metrics (R², MAE, RMSE), actual vs predicted scatter, residuals, and limitations.
- Do not train or rank models on clearly inappropriate samples; show clear warnings for constant targets, near-empty fields, insufficient samples, target leakage, grouped/time-dependent rows, and out-of-range predictions.

### Interpretation

- No external LLM or AI API. Generate cautious, deterministic descriptions based on explicitly defined rules and numerical outputs.
- Template results e.g. “Among **n** paired observations, variable A and B have a Pearson coefficient **r**. This describes association, not causation.”
- Do not state that a difference or relationship is scientifically meaningful solely because of a threshold; include n, assumptions and the original scale.

## 5. Implementation plan mapped to uploaded V2 files

| Existing file | Retain / change |
|---|---|
| `app(20261018-100256).py` | Reorganize eight tool-oriented tabs into four lecture-aligned tabs and Learn/Explore/Analyze subviews; preserve V2 look and feel; namespace widget keys. |
| `preprocess(2).py` | Keep loader/column roles; add raw-vs-cleaned workflows, manual role correction, validated and reversible cleaning, audit log, ordered interpolation. |
| `profiling(1).py` | Reuse overview and numeric/categorical summaries; supplement per-variable explanation and survey counts/percentages. |
| `visualization(1).py` | Reuse Plotly figures; add automatic chart recommendation and interactive concept visuals with consistent labeling. |
| `correlation(1).py` | Reuse coefficients and heatmaps; add pairwise n, checks for constant inputs, ranked-pair caveats and reproducible result tables. |
| `modeling(1).py` | Restrict main flow to regression; teach simple OLS first; fix evaluation to avoid choosing best model using the test set; surface residuals and split metadata. |
| `statistics(1).py` | Keep available as optional advanced tools; not in lecture-aligned primary navigation. |
| `export(1).py` | Extend DOCX to carry methods, selected charts, dataset lineage, transformation log, definitions and limitations; keep CSV / ZIP. |
| `__init__.py` | Preserve package module. |

**New suggested modules:**

- `backend/lessons.py` — slide-aligned prose, examples, formulas and references; declarative topic metadata.
- `backend/auto_analysis.py` — rules for field selection, recommendation, bounded batch summaries and insight records.
- `backend/interpolation.py` — ordered interpolation logic and provenance.
- `backend/reporting.py` — assemble exported methods, analysis provenance, and selected figures (extend `export.py` or use a separate file).
- `ui/representation.py`, `ui/understanding.py`, `ui/regression.py` — UI separation for maintainability.

## 6. Implementation phases and “done” tests

### Phase A — Reorganization and reliable data ingestion

- Four-part navigation implemented; all slide-aligned topic headings present; no image/graph/classification/generative modules.
- CSV and XLSX load in the app from normal local paths, not from hard-coded `/mnt/data` demo locations.
- Raw and processed datasets displayed separately; no irreversible automatic transformation.
- App starts, detects field roles and renders all sections with empty dataset and typical dataset.

### Phase B — Teach/explore activities

- Interactive mean/median/SD/outlier demonstration; numeric vs categorical and one-hot demos; chart recommendation; correlation demo; interpolation with before/after; survey summaries.
- Each demo functions without upload and has corresponding Analyze behavior where applicable.
- Formula/legend units, column selection and educational guidance match lecture topics.

### Phase C — Automatic EDA and regression

- One-click bounded EDA with meaningful selection rationale and reproducible tables.
- Regression requires numeric target; fits pipeline correctly across splits and gives reproducible metrics and plots.
- Leak-safe selection for advanced models; warnings for too-small/mis-specified datasets.

### Phase D — Reports, quality assurance, distribution

- Single downloadable DOCX report with dataset provenance, descriptive tables, selected charts, cleaned-data methods and regression results when run; CSV/ZIP exports retained.
- Test with: tidy energy dataset, messy construction cost data, mixed categorical survey, ordered time-series with missing entries, dataset with zero usable numeric columns, tiny datasets, and high-cardinality categorical fields.
- Manual exploratory QA for UI, chart labeling, unexpected Streamlit reruns, empty/degenerate input, data leakage and report consistency.

## 7. Existing implementation caveats to address

1. CSV parser uses permissive `on_bad_lines='skip'`; skipped records must be reported, not silently omitted for research use.
2. String-to-numeric/date conversions are heuristic; require user confirmation when ambiguous, particularly percentage/units and locale-specific numbers.
3. Currently uploaded file is re-cleaned on loading and replaced in session; preserve raw data and persist transformations separately.
4. The V2 regression model comparison selects the best model based on holdout test scores; move model selection inside cross-validation on training data.
5. V2 “Auto” task detection may classify low-cardinality numeric fields as classification; numeric target suitability should be explicitly confirmed in V3.
6. Group-comparison auto-test selection uses sample-count shortcuts; if retained in advanced tools, add assumption checks and methodology warnings.
7. Demo CSV names referenced by `app.py` were not included with uploaded files; include new self-contained synthetic teaching examples.
8. The uploaded filenames have suffixes such as `(1)` / `(2)` and the app imports `backend.*`; normalize the project package tree when building, without altering the uploaded originals.

## 8. Explicit exclusions and future options

For this version do not build anything to ingest or analyze architectural images, CAD geometry, graph structure, natural-language prompts, embeddings, generative models, or classification targets. Avoid expanding the scope into research hypothesis automation or causal inference. Optional advanced regression and testing code from V2 can remain present but hidden from the lecture-first UI until it is validated.

## 9. Definition of successful V3

A learner can open Streamlit, understand the representation of rows and variables, upload an architectural tabular dataset, safely check data quality, learn and interactively explore each method from the lecture, run defensible automatic descriptive analysis, select an outcome for transparent regression, and export figures/methods/results without writing code or supplying an API key. All primary navigation faithfully follows the slide-defined topics and stops at regression.

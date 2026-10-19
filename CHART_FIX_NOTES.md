# Plotly Chart ID Fix — Interactive Data Lab

This patch addresses the following Streamlit exception:

```
streamlit.errors.StreamlitDuplicateElementId
  ... ui/understanding.py, line 126
  st.plotly_chart(localize_plot(histogram(d, c)), use_container_width=True)
```

All 19 `st.plotly_chart(...)` calls across the three teaching modules now have unique stable `key=` arguments so matching figures in different tabs cannot collide.

## Install the full updated project

Unzip `Interactive_Data_Lab_Chart_Fix.zip`, replace your old `Interactive_Data_Lab` folder, and run `streamlit run app.py` inside it. Save any local edits before replacing files.

## Minimal update

Unzip the smaller `Interactive_Data_Lab_Only_3_Files.zip` **inside your existing** `Interactive_Data_Lab` folder, allowing it to overwrite the three `ui/*.py` files. Restart Streamlit (`Ctrl+C`, then `streamlit run app.py`).

## Verification

- 19/19 Plotly chart declarations have explicit, unique keys.
- 44 simulated routes across EN/TH and all tabs passed duplicate-key checks.
- 11 backend tests passed; 1 browser/UI test remains skipped because Streamlit is not installed in the QA runtime.

No regression logic or bilingual content was changed by the fix.

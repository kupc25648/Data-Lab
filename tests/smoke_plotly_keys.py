"""Guard against StreamlitDuplicateElementId for Plotly charts.

Static check covers all code branches. The fake-Streamlit smoke simulation
additionally checks all normal lesson routes in both languages, with all
Streamlit tabs executed just as the app does in a normal rerun.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = [ROOT / "ui" / x for x in ("representation.py", "understanding.py", "research.py")]

seen_keys: dict[str, str] = {}
for path in MODULES:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (isinstance(f, ast.Attribute) and f.attr == "plotly_chart" and isinstance(f.value, ast.Name) and f.value.id == "st"):
            continue
        explicit_keys = [kw.value for kw in node.keywords if kw.arg == "key"]
        assert len(explicit_keys) == 1, f"Missing or multiple key= in {path.name}:{node.lineno}"
        keynode = explicit_keys[0]
        assert isinstance(keynode, ast.Constant) and isinstance(keynode.value, str), f"Nonstable key in {path.name}:{node.lineno}"
        key = keynode.value
        assert key and key not in seen_keys, f"Duplicate chart key={key!r}, locations {seen_keys.get(key)} and {path.name}:{node.lineno}"
        seen_keys[key] = f"{path.name}:{node.lineno}"
assert len(seen_keys) == 19, f"Expected 19 Plotly chart locations, found {len(seen_keys)}"
print(f"PASS: {len(seen_keys)} chart declarations have unique, stable keys")

# Run every lesson with a duplicate-key checker. All tab bodies are executed.
import smoke_simulated_ui as smoke
from backend.lessons import REPRESENTATION, UNDERSTANDING, REGRESSION

fake = smoke.fake
ran = 0
for locale in ("en", "th"):
    fake.session_state.ui_language = locale
    for selector, lessons in (("r_topic", REPRESENTATION), ("u_topic", UNDERSTANDING), ("g_topic", REGRESSION)):
        for index in range(len(lessons)):
            fake.topic_index[selector] = index
            rendered: set[str] = set()

            def checked_chart(*args, **kwargs):
                key = kwargs.get("key")
                assert isinstance(key, str) and key, f"Chart missing explicit key on {locale}/{selector}/{index}"
                assert key not in rendered, f"Duplicate rendered chart key {key} on {locale}/{selector}/{index}"
                rendered.add(key)

            fake.plotly_chart = checked_chart
            smoke.app.main()
            ran += 1
print(f"PASS: {ran} simulated page renders (all tab bodies, both languages), no duplicate chart keys")

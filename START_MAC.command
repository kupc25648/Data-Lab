#!/bin/zsh
cd "$(dirname "$0")" || exit 1
# Prefer the project environment if it exists, otherwise the active Python.
if [[ -x .venv/bin/python ]]; then
  PYTHON=.venv/bin/python
else
  PYTHON=python3
fi
if ! "$PYTHON" -c 'import streamlit' >/dev/null 2>&1; then
  echo 'Streamlit is not installed in this Python environment. Run:'
  echo '  python3 -m venv .venv'
  echo '  source .venv/bin/activate'
  echo '  pip install -r requirements.txt'
  echo 'Then launch START_MAC.command again.'
  read -k 1 '?Press any key to close...'
  exit 1
fi
"$PYTHON" -m streamlit run app.py

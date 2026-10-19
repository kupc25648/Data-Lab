#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if ! python3 -c 'import streamlit' >/dev/null 2>&1; then
  echo 'Streamlit is not installed. Set up the project with:'
  echo '  python3 -m venv .venv'
  echo '  source .venv/bin/activate'
  echo '  pip install -r requirements.txt'
  echo 'Then double-click START_MAC.command or run: streamlit run app.py'
  read -k 1 '?Press any key to close...'
  exit 1
fi
python3 -m streamlit run app.py

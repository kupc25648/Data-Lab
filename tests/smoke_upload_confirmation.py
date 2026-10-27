"""Offline state-transition test for the actual sidebar's two Confirm buttons.

Uses a minimal Streamlit stand-in. Run a real Streamlit AppTest on a machine
with the package installed; this test verifies that selection != activation.
"""
from __future__ import annotations
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('lesson_smoke', ROOT / 'tests/smoke_simulated_ui.py')
mod = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(mod)
fake = mod.fake
app = mod.app

class Upload:
    def __init__(self, name, contents):
        self.name = name
        self.contents = contents
    def getvalue(self): return self.contents

fake.session_state.clear()
app.init()
selected_upload = None
selected_demo = 'No demo'
clicked = set()
header_row = 1
sheet_name = None
encoding = 'Auto'
delimiter = 'Auto'


def upload_widget(*a, **kw): return selected_upload

def selectbox(label, options, index=0, key=None, **kw):
    if key == 'demo_selection': return selected_demo
    if key == 'import_sheet' and sheet_name in options: return sheet_name
    if key == 'import_encoding': return encoding
    if key == 'import_delimiter': return delimiter
    return list(options)[index]

def number_input(label, *a, **kw):
    return header_row if kw.get('key') == 'import_header' else kw.get('value',0)

def button(label, *a, **kw): return kw.get('key') in clicked

def rerun(): pass

fake.file_uploader = upload_widget
fake.selectbox = selectbox
fake.number_input = number_input
fake.button = button
fake.rerun = rerun

# No implicit dataset after entering the site.
app.sidebar()
assert fake.session_state.working is None

# Selecting a CSV does not activate it until the button is pressed.
selected_upload = Upload('my_original.csv', b'area,cost\n22,100\n35,160\n')
app.sidebar()
assert fake.session_state.working is None
clicked = {'confirm_uploaded_dataset'}
app.sidebar()
assert fake.session_state.dataset_source == 'upload'
assert fake.session_state.working['area'].tolist() == [22,35]
old_id = fake.session_state.dataset_id
clicked = set()

# Merely selecting a demo does not displace uploaded data.
selected_demo = 'Energy performance (synthetic)'
app.sidebar()
assert fake.session_state.dataset_id == old_id
clicked = {'confirm_demo_dataset'}
app.sidebar()
assert fake.session_state.dataset_source == 'demo'
assert len(fake.session_state.working) > 100
clicked = set()

# With selected demo still on screen, original upload remains a candidate.
selected_upload = Upload('changed.csv', b'area,cost\n80,1000\n90,2000\n')
app.sidebar()
assert fake.session_state.dataset_source == 'demo'
clicked = {'confirm_uploaded_dataset'}
app.sidebar()
assert fake.session_state.dataset_source == 'upload'
assert fake.session_state.working['area'].tolist() == [80,90]
clicked = set()
app.sidebar()
assert fake.session_state.working['area'].tolist() == [80,90]

# Confirm the correct worksheet and a non-first-row header in Excel.
excel=io.BytesIO()
with pd.ExcelWriter(excel,engine='openpyxl') as writer:
    pd.DataFrame({'wrong':[1]}).to_excel(writer,sheet_name='Intro',index=False)
    pd.DataFrame([['Notes',None],['Ignore',None],['พื้นที่','ราคา'],[12,120],[15,160]])\
      .to_excel(writer,sheet_name='Buildings',index=False,header=False)
selected_upload=Upload('my_buildings.xlsx',excel.getvalue())
sheet_name='Buildings'
header_row=3
clicked={'confirm_uploaded_dataset'}
app.sidebar()
assert list(fake.session_state.working.columns) == ['พื้นที่','ราคา']
assert fake.session_state.working['ราคา'].tolist()==[120,160]
assert fake.session_state.dataset_source == 'upload'
clicked=set()

# Thai CP874 semicolon CSV is supported with an explicit encoding choice.
selected_upload=Upload('thai.csv','อาคาร;พื้นที่\nก;55\nข;80\n'.encode('cp874'))
header_row=1
encoding='Thai CP874'
delimiter='Semicolon (;)'
clicked={'confirm_uploaded_dataset'}
app.sidebar()
assert fake.session_state.working['พื้นที่'].tolist()==[55,80]
assert fake.session_state.working['อาคาร'].tolist()==['ก','ข']
print('PASS: pending upload, explicit upload confirmation, demo confirmation, no implicit switching, multitab Excel headers, CP874 CSV')

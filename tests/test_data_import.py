"""CSV/Excel import regression tests. No Streamlit required."""
from io import BytesIO
import pandas as pd
import pytest
from backend.preprocess import (read_uploaded_bytes, excel_sheet_names,
                                MAX_UPLOAD_BYTES)


def test_csv_semicolon_auto():
    actual = read_uploaded_bytes(b'area;cost\n20;100\n35;200\n', 'project.csv')
    assert list(actual) == ['area', 'cost']
    assert actual['cost'].tolist() == [100, 200]


def test_csv_tsv_and_header_row():
    raw = b'This is an introductory title\nBuilding\tArea\nA\t100\nB\t150\n'
    actual = read_uploaded_bytes(raw, 'experiment.csv', header_row=2, csv_delimiter='Tab')
    assert list(actual) == ['Building', 'Area']
    assert actual.Area.tolist() == [100,150]


def test_thai_csv_cp874_encoding():
    raw = 'อาคาร;พื้นที่\nก;12\nข;25\n'.encode('cp874')
    actual = read_uploaded_bytes(raw,'thai.csv',csv_encoding='Thai CP874',
                                 csv_delimiter='Semicolon (;)')
    assert actual['อาคาร'].tolist() == ['ก','ข']


def test_utf16_csv_from_excel():
    raw = 'Name,Area\nA,22\nB,45\n'.encode('utf-16')
    actual = read_uploaded_bytes(raw,'excel_export.csv')
    assert actual['Area'].tolist() == [22,45]


def test_excel_sheet_selection_and_headers():
    output=BytesIO()
    with pd.ExcelWriter(output,engine='openpyxl') as writer:
        pd.DataFrame({'wrong':[1]}).to_excel(writer,sheet_name='Intro',index=False)
        pd.DataFrame([['Report',None],['Project','Cost'],['A',200],['B',300]])\
          .to_excel(writer,sheet_name='Data',header=False,index=False)
    raw=output.getvalue()
    assert excel_sheet_names(raw,'report.xlsx') == ['Intro','Data']
    actual=read_uploaded_bytes(raw,'report.xlsx',sheet_name='Data',header_row=2)
    assert actual['Cost'].tolist()==[200,300]


def test_malformed_csv_is_not_silently_skipped():
    with pytest.raises(Exception):
        read_uploaded_bytes(b'X,Y\n1,2\n3,4,5\n', 'broken.csv')


def test_size_limit_raised_and_empty_rejected():
    assert MAX_UPLOAD_BYTES >= 50*1024*1024
    with pytest.raises(ValueError):
        read_uploaded_bytes(b'','empty.csv')

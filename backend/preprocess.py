"""Lossless file ingestion, controlled data preparation, and role classification.

A loaded dataset is NEVER mutated by these functions. Every change returns a
new dataframe and an audit record, and the UI maintains undo history.
"""
from __future__ import annotations
from io import BytesIO, StringIO
import csv
from dataclasses import dataclass
import pandas as pd
import numpy as np

# The original app rejected user CSV files larger than 15 MB while the
# Streamlit file uploader appeared to accept them. Keep one explicit limit.
MAX_UPLOAD_BYTES = 100 * 1024 * 1024

@dataclass
class ColumnRoles:
    numeric: list[str]
    categorical: list[str]
    datetime: list[str]
    boolean: list[str]
    id_like: list[str]


CSV_ENCODINGS = {
    'Auto': None,
    'UTF-8': 'utf-8',
    'UTF-8 with BOM': 'utf-8-sig',
    'UTF-16': 'utf-16',
    'Thai CP874': 'cp874',
    'Western CP1252': 'cp1252',
    'Latin-1': 'latin-1',
}
CSV_DELIMITERS = {'Auto': None, 'Comma (,)': ',', 'Semicolon (;)': ';',
                  'Tab': '\t', 'Pipe (|)': '|'}


def _decode_csv(raw: bytes, encoding: str) -> str:
    if encoding not in CSV_ENCODINGS:
        raise ValueError('Unsupported CSV encoding selection.')
    if encoding != 'Auto':
        return raw.decode(CSV_ENCODINGS[encoding])
    # Detect actual BOM before trying permissive single-byte encodings.
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        pass
    # Thai legacy exports often use CP874; CP1252 exports are common too.
    # This heuristic is only a convenience. The user can explicitly override.
    try:
        thai = raw.decode('cp874')
        thai_letters = sum('\u0e01' <= c <= '\u0e5b' for c in thai[:20000])
        if thai_letters >= 3 and thai_letters / max(len(thai[:20000]), 1) >= 0.005:
            return thai
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode('cp1252')
    except UnicodeDecodeError:
        return raw.decode('latin-1')


def excel_sheet_names(raw: bytes, filename: str) -> list[str]:
    if not filename.lower().endswith(('.xlsx', '.xls')):
        return []
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError('Upload exceeds the 100 MB limit.')
    with pd.ExcelFile(BytesIO(raw)) as workbook:
        return list(workbook.sheet_names)


def read_uploaded_bytes(raw: bytes, filename: str, sheet_name=0,
                        header_row: int = 1, csv_encoding: str = 'Auto',
                        csv_delimiter: str = 'Auto') -> pd.DataFrame:
    """Read a user-selected table *without* changing the original bytes.

    ``header_row`` is a 1-based row of the uploaded CSV or worksheet.
    The caller must explicitly confirm activation of this DataFrame.
    """
    if not raw:
        raise ValueError('The uploaded file is empty.')
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError('Files must be 100 MB or smaller for this teaching app.')
    if not (1 <= int(header_row) <= 1000):
        raise ValueError('The column-heading row must be between 1 and 1000.')
    low = filename.lower()
    if low.endswith('.csv'):
        text = _decode_csv(raw, csv_encoding)
        if csv_delimiter not in CSV_DELIMITERS:
            raise ValueError('Unsupported CSV separator selection.')
        separator = CSV_DELIMITERS[csv_delimiter]
        if separator is None:
            # Sniff several lines starting at the selected heading row, instead
            # of the document title/preamble, which can use unrelated commas.
            lines = text.splitlines()
            sample = '\n'.join(lines[int(header_row)-1:int(header_row)+30])[:16000]
            try:
                separator = csv.Sniffer().sniff(sample, delimiters=',;\t|').delimiter
            except csv.Error:
                separator = ','
        # Never silently discard malformed records.
        result = pd.read_csv(StringIO(text), sep=separator, on_bad_lines='error',
                             low_memory=False, header=int(header_row)-1,
                             skip_blank_lines=False)
    elif low.endswith(('.xlsx', '.xls')):
        result = pd.read_excel(BytesIO(raw), sheet_name=sheet_name,
                               header=int(header_row)-1)
    else:
        raise ValueError('Only CSV, XLSX, and XLS files are supported.')
    if result.empty or result.shape[1] == 0:
        raise ValueError('Dataset is empty. Check the selected sheet and heading row.')
    if not result.columns.is_unique:
        raise ValueError('Duplicate column names detected. Rename columns in the source table.')
    return result


def is_id_like(s: pd.Series, name: str) -> bool:
    name = str(name).strip().lower()
    if name in ('id','uuid','code','key','index','serial','row_id') or name.endswith(('_id','_code','_key')):
        return True
    if name.startswith(('id_','uuid_')):
        return True
    if pd.api.types.is_object_dtype(s) and len(s.dropna()) > 15:
        return s.nunique(dropna=True) / max(s.notna().sum(), 1) >= 0.98
    return False


def detect_column_roles(df: pd.DataFrame, overrides: dict[str,str] | None = None) -> ColumnRoles:
    overrides = overrides or {}
    r = ColumnRoles([], [], [], [], [])
    for col in df.columns:
        s = df[col]
        role = overrides.get(col)
        if role is None or role == 'Auto':
            if is_id_like(s, col): role = 'Identifier'
            elif pd.api.types.is_datetime64_any_dtype(s): role = 'Datetime'
            elif pd.api.types.is_bool_dtype(s): role = 'Boolean'
            elif pd.api.types.is_numeric_dtype(s): role = 'Numeric'
            else: role = 'Categorical'
        role = role.lower()
        if role == 'numeric': r.numeric.append(col)
        elif role == 'datetime': r.datetime.append(col)
        elif role == 'boolean': r.boolean.append(col)
        elif role == 'identifier': r.id_like.append(col)
        else: r.categorical.append(col)
    return r


def make_analysis_view(df: pd.DataFrame, overrides: dict[str,str] | None = None) -> pd.DataFrame:
    """For user-approved role overrides only; conversion does not modify raw/working frames."""
    out = df.copy(deep=True)
    for col, role in (overrides or {}).items():
        if col not in out: continue
        if role == 'Numeric':
            out[col] = pd.to_numeric(out[col], errors='coerce')
        elif role == 'Datetime':
            out[col] = pd.to_datetime(out[col], errors='coerce')
        elif role == 'Categorical':
            out[col] = out[col].astype('string')
    return out


def quality_table(df: pd.DataFrame, roles: ColumnRoles | None = None) -> pd.DataFrame:
    roles = roles or detect_column_roles(df)
    role_map={c:'Numeric' for c in roles.numeric}
    role_map.update({c:'Categorical' for c in roles.categorical})
    role_map.update({c:'Datetime' for c in roles.datetime})
    role_map.update({c:'Boolean' for c in roles.boolean})
    role_map.update({c:'Identifier' for c in roles.id_like})
    return pd.DataFrame([{'Column':str(c),'Role':role_map.get(c,'Other'),'Stored dtype':str(df[c].dtype),
                          'Non-missing':int(df[c].notna().sum()),'Missing':int(df[c].isna().sum()),
                          'Missing %':round(df[c].isna().mean()*100,1),'Distinct':int(df[c].nunique(dropna=True))}
                         for c in df.columns])


def data_warnings(df: pd.DataFrame) -> list[str]:
    warnings=[]
    if len(df)<30: warnings.append(f'Small dataset (n={len(df)}): statistical and predictive results may be unstable.')
    if df.isna().to_numpy().mean()>0.10: warnings.append('More than 10% of all cells are missing.')
    if df.duplicated().any(): warnings.append(f'{int(df.duplicated().sum())} exact duplicate rows detected (may be legitimate repeated observations).')
    suspect=[c for c in df if str(c).strip()=='' or str(c).lower().startswith('unnamed')]
    if suspect: warnings.append(f'Possible unnamed columns: {", ".join(map(str, suspect[:4]))}.')
    return warnings


def apply_cleaning(df:pd.DataFrame, operation:str, column:str|None=None, value=None) -> tuple[pd.DataFrame,str]:
    out=df.copy(deep=True)
    if operation=='Trim text':
        if column is None: raise ValueError('Choose a text column.')
        if not (pd.api.types.is_string_dtype(out[column]) or out[column].dtype=='object'):
            raise ValueError('Trimming requires a text column.')
        out[column]=out[column].map(lambda x:x.strip() if isinstance(x,str) else x)
        description=f'Trimmed leading/trailing spaces in {column}'
    elif operation=='Replace missing values':
        if column is None: raise ValueError('Choose a column.')
        count=int(out[column].isna().sum())
        if value=='Median':
            v=pd.to_numeric(out[column],errors='coerce').median()
            if pd.isna(v): raise ValueError('No numeric median available.')
        elif value=='Mode':
            modes=out[column].mode(dropna=True)
            if modes.empty: raise ValueError('No non-missing values available.')
            v=modes.iloc[0]
        else: raise ValueError('Select Median or Mode.')
        out[column]=out[column].fillna(v)
        description=f'Filled {count} missing value(s) in {column} using {value.lower()} ({v})'
    elif operation=='Drop exact duplicate rows':
        count=int(out.duplicated().sum());out=out.drop_duplicates().reset_index(drop=True)
        description=f'Removed {count} exact duplicate row(s)'
    elif operation=='Drop completely empty rows/columns':
        original=out.shape
        out=out.dropna(how='all').dropna(axis=1,how='all').reset_index(drop=True)
        description=f'Removed all-empty rows/columns: {original} → {out.shape}'
    else: raise ValueError(f'Unknown cleaning operation: {operation}')
    return out, description


def frequency_table(s:pd.Series, include_missing:bool=True) -> pd.DataFrame:
    values=s.astype('string').fillna('(Missing)') if include_missing else s.dropna().astype('string')
    freq=values.value_counts(dropna=False)
    denom=len(values)
    return pd.DataFrame({'Category':freq.index.astype(str),'Count':freq.to_numpy(),
                         'Percent':np.round(freq.to_numpy()/max(denom,1)*100,2),
                         'Denominator':denom})


def one_hot_preview(s:pd.Series,n:int=8)->pd.DataFrame:
    values=s.head(n).astype('string')
    encoded=pd.get_dummies(values, prefix=str(s.name), dummy_na=False,dtype=int)
    return pd.concat([values.rename(str(s.name)),encoded],axis=1)

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls")
NULL_TOKENS = {"", "nan", "none", "null", "n/a", "na", "-", "--", "missing", "invalid", "<na>"}


@dataclass
class ColumnRoles:
    numeric: list[str]
    categorical: list[str]
    datetime: list[str]
    boolean: list[str]
    id_like: list[str]


def make_unique_columns(columns: list[Any]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for col in columns:
        name = str(col).replace("\n", " ").replace("\r", " ").strip()
        if not name or name.lower().startswith("unnamed:"):
            name = "column"
        if name not in seen:
            seen[name] = 0
            out.append(name)
        else:
            seen[name] += 1
            out.append(f"{name}_{seen[name]}")
    return out


def _read_csv_bytes(raw: bytes) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    last_error: Exception | None = None
    for enc in encodings:
        try:
            text = raw.decode(enc)
        except Exception as exc:
            last_error = exc
            continue
        sample = text[:5000]
        seps = []
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
            seps.append(dialect.delimiter)
        except Exception:
            pass
        seps += [",", ";", "\t", "|"]
        for sep in dict.fromkeys(seps):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python", on_bad_lines="skip")
                if df is not None and df.shape[1] >= 1:
                    return df
            except Exception as exc:
                last_error = exc
    raise ValueError(f"Could not parse CSV. Last error: {last_error}")


def read_uploaded_file(uploaded_file: Any) -> pd.DataFrame:
    name = str(uploaded_file.name).lower()
    if name.endswith(".csv"):
        raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        df = _read_csv_bytes(raw)
    elif name.endswith((".xlsx", ".xls")):
        raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        df = pd.read_excel(io.BytesIO(raw))
    else:
        raise ValueError("Please upload CSV or Excel files only.")
    return clean_dataframe(df)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = make_unique_columns(list(out.columns))
    out = out.dropna(axis=0, how="all").dropna(axis=1, how="all")
    for col in out.select_dtypes(include=["object"]).columns:
        s = out[col].astype(str).str.strip()
        out[col] = s.mask(s.str.lower().isin(NULL_TOKENS), pd.NA)
    out = coerce_types(out)
    return out.reset_index(drop=True)


def _numeric_from_text(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip()
    cleaned = cleaned.str.replace(r"[\$,฿€£¥]", "", regex=True)
    cleaned = cleaned.str.replace("%", "", regex=False)
    cleaned = cleaned.str.replace(r"\s+", "", regex=True)
    comma_count = cleaned.str.contains(",", regex=False).sum()
    dot_count = cleaned.str.contains(".", regex=False).sum()
    if comma_count > 0 and dot_count < max(1, int(len(cleaned) * 0.2)):
        cleaned = cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    else:
        cleaned = cleaned.str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace(r"[^\d\.\-+eE]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    bool_map = {"true": True, "false": False, "yes": True, "no": False, "y": True, "n": False, "1": True, "0": False}
    for col in out.columns:
        if out[col].dtype != "object":
            continue
        non_na = out[col].dropna()
        if non_na.empty:
            continue
        lowered = non_na.astype(str).str.strip().str.lower()
        if lowered.isin(bool_map).mean() >= 0.85 and len(non_na) >= 3:
            converted = out[col].astype("object").copy()
            converted.loc[non_na.index] = lowered.map(bool_map)
            out[col] = converted
            continue
        num = _numeric_from_text(out[col])
        if num.notna().sum() / max(len(non_na), 1) >= 0.75:
            out[col] = num
            continue
        dt = pd.to_datetime(out[col], errors="coerce", format="mixed")
        if dt.notna().sum() / max(len(non_na), 1) >= 0.75:
            out[col] = dt
    return out


def is_id_like(series: pd.Series, name: str) -> bool:
    low = name.lower()
    tokens = ["id", "uuid", "code", "key", "no", "number", "serial", "ref", "index"]
    if low in tokens or low.endswith("_id") or any(t == low for t in tokens):
        return True
    non_na = series.dropna()
    if len(non_na) < 8:
        return False
    unique_ratio = non_na.nunique(dropna=True) / max(len(non_na), 1)
    # High uniqueness alone is not enough for numeric research/business variables
    # such as area, cost, duration, strength, or energy use. Treat uniqueness as
    # ID-like only for object columns or explicitly ID-named numeric columns.
    if series.dtype == "object" and unique_ratio >= 0.98:
        return True
    if pd.api.types.is_numeric_dtype(series) and unique_ratio > 0.9 and non_na.reset_index(drop=True).is_monotonic_increasing:
        if any(token in low for token in ["id", "code", "serial", "ref", "index"]):
            return True
    return False


def detect_column_roles(df: pd.DataFrame) -> ColumnRoles:
    numeric_raw = list(df.select_dtypes(include=[np.number]).columns)
    datetime_cols = list(df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns)
    bool_cols = list(df.select_dtypes(include=["bool"]).columns)
    id_like = [c for c in df.columns if is_id_like(df[c], str(c))]
    numeric = [c for c in numeric_raw if c not in id_like and df[c].dropna().nunique() > 1]
    categorical = [c for c in df.columns if c not in numeric + datetime_cols and c not in id_like and df[c].dropna().nunique() > 1]
    return ColumnRoles(numeric=numeric, categorical=categorical, datetime=datetime_cols, boolean=bool_cols, id_like=id_like)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

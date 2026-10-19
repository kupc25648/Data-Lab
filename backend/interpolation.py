"""No extrapolation: fill only internal gaps with meaningful ordered x coordinate."""
from __future__ import annotations
import pandas as pd
import numpy as np


def interpolate_ordered(df:pd.DataFrame,x:str,y:str)->tuple[pd.DataFrame,pd.DataFrame]:
    if x==y: raise ValueError('X and Y must be different columns.')
    series=df[[x,y]].copy()
    xx=series[x]
    if pd.api.types.is_datetime64_any_dtype(xx):
        numeric_x=xx.astype('int64').astype(float)
        numeric_x[xx.isna()]=np.nan
    else:
        numeric_x=pd.to_numeric(xx,errors='coerce').astype(float)
    yy=pd.to_numeric(series[y],errors='coerce')
    if numeric_x.isna().any(): raise ValueError('X has invalid or missing positions; clean X first.')
    if numeric_x.duplicated().any(): raise ValueError('X contains duplicates; interpolation needs unique positions.')
    if numeric_x.nunique()<3: raise ValueError('At least three ordered positions are required.')
    idx=np.argsort(numeric_x.to_numpy())
    xs=numeric_x.iloc[idx].to_numpy(dtype=float)
    ys=yy.iloc[idx].to_numpy(dtype=float)
    known=np.isfinite(ys)
    if known.sum()<2: raise ValueError('At least two known Y values are required.')
    internal=np.isnan(ys)&(xs>xs[known].min())&(xs<xs[known].max())
    fills=np.interp(xs[internal],xs[known],ys[known])
    out=df.copy(deep=True)
    out.loc[series.index[idx[internal]],y]=fills
    change=pd.DataFrame({'Row index':series.index[idx[internal]],'X':series[x].iloc[idx[internal]].to_numpy(),
                         'Column':y,'Old value':np.nan,'Interpolated value':fills})
    return out,change

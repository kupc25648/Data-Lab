"""Bounded, read-only automatic EDA and deterministic interpretations."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from .preprocess import ColumnRoles, detect_column_roles, frequency_table, data_warnings


def numeric_summary(df:pd.DataFrame,cols:list[str]|None=None)->pd.DataFrame:
    cols=cols if cols is not None else detect_column_roles(df).numeric
    rows=[]
    for c in cols:
        s=pd.to_numeric(df[c],errors='coerce').replace([np.inf,-np.inf],np.nan).dropna()
        if not len(s):continue
        q1,q3=s.quantile([.25,.75]);iqr=q3-q1
        rows.append({'Variable':c,'N':len(s),'Missing':len(df)-len(s),'Mean':s.mean(),
          'Median':s.median(),'Sample SD':s.std(ddof=1),'Min':s.min(),'Q1':q1,'Q3':q3,
          'Max':s.max(),'IQR outliers':int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum()) if iqr>0 else 0})
    return pd.DataFrame(rows)


def correlation_pairs(df:pd.DataFrame,cols:list[str],method:str='pearson',max_columns:int=12)->pd.DataFrame:
    cols=cols[:max_columns]
    rows=[]
    for i,a in enumerate(cols):
        for b in cols[i+1:]:
            xy=df[[a,b]].apply(pd.to_numeric,errors='coerce').replace([np.inf,-np.inf],np.nan).dropna()
            if len(xy)<4 or xy[a].nunique()<2 or xy[b].nunique()<2:continue
            try:
                res=pearsonr(xy[a],xy[b]) if method=='pearson' else spearmanr(xy[a],xy[b])
                rows.append({'Variable A':a,'Variable B':b,'N':len(xy),'Method':method.title(),
                  'r':float(res.statistic),'p (unadjusted)':float(res.pvalue)})
            except ValueError:continue
    result=pd.DataFrame(rows)
    if not result.empty:
        result=result.assign(_abs=result['r'].abs()).sort_values('_abs',ascending=False).drop(columns='_abs').reset_index(drop=True)
    return result


def suggest_charts(roles:ColumnRoles,max_suggestions:int=5)->list[dict[str,str]]:
    suggestions=[]
    for col in roles.numeric[:2]:
        suggestions.append({'Chart':'Histogram','X':col,'Y':'','Reason':'A numerical variable has a distribution; inspect spread and outliers.'})
    if len(roles.numeric)>=2:
        suggestions.append({'Chart':'Scatter','X':roles.numeric[0],'Y':roles.numeric[1],
                            'Reason':'Two numerical variables can be compared for a relationship.'})
    for col in roles.categorical[:1]:
        suggestions.append({'Chart':'Bar counts','X':col,'Y':'','Reason':'Counts compare frequencies of categories.'})
        if roles.numeric:
            suggestions.append({'Chart':'Box by category','X':col,'Y':roles.numeric[0],
                                'Reason':'A numerical response can be compared across categories.'})
    return suggestions[:max_suggestions]


def auto_profile(df:pd.DataFrame,roles:ColumnRoles|None=None,limit:int=12)->dict:
    roles=roles or detect_column_roles(df)
    numeric_cols=roles.numeric[:limit]
    desc=numeric_summary(df,numeric_cols)
    pairs=correlation_pairs(df,numeric_cols,max_columns=min(12,limit))
    categories={c:frequency_table(df[c]).head(15) for c in roles.categorical[:3]}
    findings=[]
    for issue in data_warnings(df): findings.append('Quality check: '+issue)
    if not desc.empty:
        findings.append(f'Computed descriptive summaries for {len(desc)} of {len(roles.numeric)} numerical variables.')
    if not pairs.empty:
        p=pairs.iloc[0]
        findings.append(f'Largest observed |Pearson r| in scanned pairs: {p["Variable A"]} versus {p["Variable B"]}, r={p["r"]:.2f}, paired n={int(p["N"])}. This is exploratory association, not causation.')
        if len(pairs)>1: findings.append(f'{len(pairs)} pairs were examined; unadjusted p-values should not be treated as confirmatory significance without multiple-testing control.')
    if not findings: findings.append('No major issues detected in the bounded automatic checks; review variable meanings and units manually.')
    return {'numeric':desc,'pairs':pairs,'categorical':categories,
            'charts':suggest_charts(roles), 'findings':findings,'warnings':data_warnings(df)}

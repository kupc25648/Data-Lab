from io import BytesIO
from zipfile import ZipFile
import numpy as np
import pandas as pd
import pytest
from docx import Document
from backend.demo_data import energy_demo,cost_demo,survey_demo,sensor_demo
from backend.preprocess import (read_uploaded_bytes,detect_column_roles,apply_cleaning,
  frequency_table,one_hot_preview,make_analysis_view,quality_table)
from backend.auto_analysis import numeric_summary,correlation_pairs,auto_profile,suggest_charts
from backend.interpolation import interpolate_ordered
from backend.regression import regression_fit,fitted_equation
from backend.reporting import make_docx,zip_tables,assemble_tables


def test_all_demo_datasets_profile():
    for maker in (energy_demo,cost_demo,survey_demo,sensor_demo):
        df=maker()
        assert len(df)>=80
        assert len(quality_table(df))==df.shape[1]
        result=auto_profile(df)
        assert result['findings']


def test_csv_error_preserves_records():
    raw=b'A,B\n1,2\n3,4\n'
    assert len(read_uploaded_bytes(raw,'okay.csv'))==2
    with pytest.raises(Exception):read_uploaded_bytes(b'A,B\n1,2\n3,4,5\n','bad.csv')
    with pytest.raises(ValueError):read_uploaded_bytes(raw,'unaccepted.json')


def test_excel_ingestion():
    x=pd.DataFrame({'area':[40,60],'orientation':['East','West']})
    stream=BytesIO();x.to_excel(stream,index=False)
    actual=read_uploaded_bytes(stream.getvalue(),'data.xlsx')
    pd.testing.assert_frame_equal(x,actual)


def test_role_override_and_encoding():
    d=pd.DataFrame({'code':['1','2','3'],'type':['Office','School','Office']})
    view=make_analysis_view(d,{'code':'Numeric'})
    assert pd.api.types.is_numeric_dtype(view['code'])
    assert not pd.api.types.is_numeric_dtype(d['code'])
    enc=one_hot_preview(d['type']);assert 'type_School' in enc
    assert int(frequency_table(d['type'])['Count'].sum())==3


def test_reversible_cleaning_outputs_are_copies():
    orig=pd.DataFrame({'name':[' A ',' A ',None],'value':[10.,10.,np.nan]})
    trim,_=apply_cleaning(orig,'Trim text','name')
    assert orig.iloc[0,0]==' A ' and trim.iloc[0,0]=='A'
    full,_=apply_cleaning(trim,'Replace missing values','value','Median')
    assert full['value'].isna().sum()==0
    assert orig['value'].isna().sum()==1
    dedup,_=apply_cleaning(trim,'Drop exact duplicate rows')
    assert len(dedup)==2


def test_numeric_stats_pairwise_and_n():
    x=pd.DataFrame({'a':[1,2,3,np.nan,5], 'b':[2,4,6,8,10], 'c':['x']*5})
    summ=numeric_summary(x,['a','b']);assert summ.loc[0,'N']==4
    pairs=correlation_pairs(x,['a','b'])
    assert len(pairs)==1 and int(pairs.iloc[0]['N'])==4
    assert pytest.approx(pairs.iloc[0]['r'],abs=1e-10)==1.0
    assert len(suggest_charts(detect_column_roles(x)))>=2


def test_interpolation_internal_only_and_no_mutation():
    x=pd.DataFrame({'t':[0,1,2,3,4,5],'v':[np.nan,2,np.nan,6,np.nan,np.nan]})
    out,changes=interpolate_ordered(x,'t','v')
    assert out.loc[2,'v']==4 and len(changes)==1
    assert pd.isna(out.loc[0,'v']) and pd.isna(out.loc[5,'v'])
    assert pd.isna(x.loc[2,'v'])
    with pytest.raises(ValueError):interpolate_ordered(pd.DataFrame({'t':[0,1,1,3],'v':[2,None,4,5]}),'t','v')


def test_regression_linear_reproducible():
    df=energy_demo()
    r=regression_fit(df,'monthly_electricity_kwh',['floor_area_m2'],seed=11)
    r2=regression_fit(df,'monthly_electricity_kwh',['floor_area_m2'],seed=11)
    assert r.train_n+r.test_n==len(df)
    pd.testing.assert_frame_equal(r.predictions,r2.predictions)
    assert r.best_model=='Linear regression'
    assert 'floor_area_m2' in fitted_equation(r)
    assert 'CV MAE' in r.cv_metrics and 'Test MAE' in r.final_metrics


def test_regression_multi_algorithm_selection_training_only():
    df=energy_demo()
    r=regression_fit(df,'monthly_electricity_kwh',['floor_area_m2','building_type'],
                      advanced=True,selected=['Linear regression','Ridge'],seed=9)
    assert set(r.cv_metrics['Model'])=={'Linear regression','Ridge'}
    assert r.best_model==r.cv_metrics.sort_values('CV MAE').iloc[0]['Model']
    assert len(r.predictions)==r.test_n


def test_regression_group_time_and_invalid_cases():
    df=energy_demo()
    group=regression_fit(df,'monthly_electricity_kwh',['floor_area_m2'],split_method='Grouped',group_col='building_type') if False else None
    # Building type has only 3 groups, intentionally reject as insufficient.
    with pytest.raises(ValueError):regression_fit(df,'monthly_electricity_kwh',['floor_area_m2'],split_method='Grouped',group_col='building_type')
    df=df.copy();df['group']=[f'P{i%16:02}' for i in range(len(df))]
    rg=regression_fit(df,'monthly_electricity_kwh',['floor_area_m2'],split_method='Grouped',group_col='group',advanced=True,selected=['Linear regression'])
    assert rg.test_n>0
    df['sequence']=np.arange(len(df))
    rt=regression_fit(df,'monthly_electricity_kwh',['floor_area_m2'],split_method='Chronological',order_col='sequence')
    assert rt.test_n>0
    with pytest.raises(ValueError):regression_fit(df.head(10),'monthly_electricity_kwh',['floor_area_m2'])
    with pytest.raises(ValueError):regression_fit(df,'building_type',['floor_area_m2'])


def test_export_zip_and_docx():
    df=cost_demo()
    run=regression_fit(df,'construction_cost_thb',['area_m2','storeys'])
    tables=assemble_tables(df,run=run)
    zipped=zip_tables(tables)
    with ZipFile(BytesIO(zipped)) as z:
        assert 'regression_holdout.csv' in z.namelist()
    blob=make_docx(df,'synthetic cost',df.shape,[{'Action':'Example','Details':'test'}],run=run)
    doc=Document(BytesIO(blob));alltext='\n'.join(p.text for p in doc.paragraphs)
    assert 'training subset only' in alltext
    assert 'synthetic cost' in alltext
    assert len(doc.inline_shapes)>0

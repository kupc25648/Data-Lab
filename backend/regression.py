"""Leakage-aware regression only. Select on training CV, report untouched test once."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor,RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression,Ridge
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from sklearn.model_selection import KFold,GroupKFold,TimeSeriesSplit,GroupShuffleSplit,train_test_split,cross_validate
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.svm import SVR

@dataclass
class RegressionRun:
    target:str
    features:list[str]
    best_model:str
    final_metrics:pd.DataFrame
    cv_metrics:pd.DataFrame
    predictions:pd.DataFrame
    model:Pipeline
    train_n:int
    test_n:int
    seed:int
    test_fraction:float
    split_method:str
    notes:list[str]
    candidates:list[str]


def candidates_advanced(seed:int)->dict:
    return {'Linear regression':LinearRegression(), 'Ridge':Ridge(alpha=1.0),
        'Random Forest':RandomForestRegressor(n_estimators=120,random_state=seed,n_jobs=-1,min_samples_leaf=2),
        'Gradient Boosting':GradientBoostingRegressor(random_state=seed),
        'KNN':KNeighborsRegressor(n_neighbors=5), 'SVR':SVR(C=10,epsilon=0.1)}


def _pre(X:pd.DataFrame)->ColumnTransformer:
    num=X.select_dtypes(include=['number','bool']).columns.tolist()
    cat=[c for c in X if c not in num]
    trs=[]
    if num:
        trs.append(('num',Pipeline([('imputer',SimpleImputer(strategy='median')),
           ('scale',StandardScaler())]),num))
    if cat:
        trs.append(('cat',Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),
           ('onehot',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),cat))
    return ColumnTransformer(trs,remainder='drop',verbose_feature_names_out=False)


def regression_fit(df:pd.DataFrame,target:str,features:list[str],advanced:bool=False,
                   selected:list[str]|None=None,seed:int=42,test_fraction:float=.2,
                   cv_folds:int=5,split_method:str='Random',order_col:str|None=None,
                   group_col:str|None=None)->RegressionRun:
    if target not in df:raise ValueError('Choose an existing numeric target.')
    if not pd.api.types.is_numeric_dtype(df[target]):raise ValueError('Regression needs a numeric target. Select or convert its role first.')
    if not features or target in features or len(set(features))!=len(features):
        raise ValueError('Choose one or more distinct predictor columns, excluding target.')
    if any(c not in df for c in features):raise ValueError('Unknown predictor column.')
    if split_method not in ('Random','Chronological','Grouped'):raise ValueError('Unknown split method.')
    cols=list(dict.fromkeys([target]+features+([order_col] if split_method=='Chronological' and order_col else [])+([group_col] if split_method=='Grouped' and group_col else [])))
    if split_method=='Chronological' and (not order_col or order_col==target):raise ValueError('Choose an ordering column for chronological evaluation.')
    if split_method=='Grouped' and (not group_col or group_col==target):raise ValueError('Choose a grouping column for grouped evaluation.')
    frame=df[cols].replace([np.inf,-np.inf],np.nan).dropna(subset=[target]).copy()
    if len(frame)<25:raise ValueError('At least 25 observations with a known target are required for this learning workflow.')
    if frame[target].nunique()<3:raise ValueError('Regression target has fewer than three distinct values.')
    if len(frame[target].dropna())<len(df)*.5:raise ValueError('More than 50% of target values are missing.')
    for c in features:
        if frame[c].notna().sum()<3 or frame[c].nunique(dropna=True)<2:raise ValueError(f'Predictor {c} has too few nonmissing/distinct values.')
    notes=[]
    if any(frame[c].isna().mean()>.4 for c in features):
        notes.append('Some predictors have over 40% missing observations; median/mode training-only imputation may be unreliable.')
    if len(frame)<60:notes.append('Small dataset: test metrics can vary substantially between splits.')
    for c in features:
        if frame[c].nunique(dropna=True)/len(frame)>.95 and not pd.api.types.is_numeric_dtype(frame[c]):
            raise ValueError(f'{c} has nearly unique categories, possibly an ID; remove or recode before training.')
    if split_method=='Chronological':
        frame=frame.dropna(subset=[order_col]).sort_values(order_col,kind='stable')
        n_test=max(5,int(np.ceil(test_fraction*len(frame))))
        if len(frame)-n_test < 20:raise ValueError('Chronological training segment is too small.')
        train=frame.iloc[:-n_test];test=frame.iloc[-n_test:]
        notes.append('Chronological split respects row order; forward-time generalization still requires careful review.')
    elif split_method=='Grouped':
        frame=frame.dropna(subset=[group_col])
        if frame[group_col].nunique()<4:raise ValueError('Grouped split needs at least four independent groups.')
        gss=GroupShuffleSplit(n_splits=1,test_size=test_fraction,random_state=seed)
        i,j=next(gss.split(frame,groups=frame[group_col]))
        train=frame.iloc[i];test=frame.iloc[j]
        notes.append('Groups do not overlap between train and test; within-group observations may be dependent.')
    else:
        train,test=train_test_split(frame,test_size=test_fraction,random_state=seed)
        notes.append('Random split assumes independent exchangeable observations; use chronological/grouped splitting where appropriate.')
    Xtr=train[features].copy();ytr=train[target].astype(float)
    Xte=test[features].copy();yte=test[target].astype(float)
    candidates=candidates_advanced(seed) if advanced else {'Linear regression':LinearRegression()}
    if selected and advanced:candidates={k:v for k,v in candidates.items() if k in selected}
    if not candidates:raise ValueError('Select at least one regression model.')
    pre=_pre(Xtr)
    if split_method=='Chronological':
        k=min(cv_folds, max(2,len(train)//12))
        cv=TimeSeriesSplit(n_splits=k)
        groups=None
    elif split_method=='Grouped':
        g=train[group_col].to_numpy()
        k=min(cv_folds,pd.Series(g).nunique())
        if k<2:raise ValueError('Insufficient distinct training groups for cross-validation.')
        cv=GroupKFold(n_splits=k)
        groups=g
    else:
        k=min(cv_folds,max(2,len(train)//8))
        cv=KFold(n_splits=k,shuffle=True,random_state=seed)
        groups=None
    results=[]
    for name,model in candidates.items():
        pipeline=Pipeline([('preprocess',clone(pre)),('model',clone(model))])
        try:
            scores=cross_validate(pipeline,Xtr,ytr,cv=cv,groups=groups,scoring={
                'mae':'neg_mean_absolute_error','rmse':'neg_root_mean_squared_error','r2':'r2'},error_score='raise')
            results.append({'Model':name,'CV MAE':-np.mean(scores['test_mae']),
                            'CV RMSE':-np.mean(scores['test_rmse']),
                            'CV R²':np.mean(scores['test_r2']),'Folds':k})
        except Exception as exc:notes.append(f'{name} unavailable: {type(exc).__name__}: {exc}')
    if not results:raise ValueError('No model could complete cross-validation; check dataset quality and features.')
    cvdf=pd.DataFrame(results).sort_values('CV MAE').reset_index(drop=True)
    best=str(cvdf.iloc[0]['Model'])
    final=Pipeline([('preprocess',clone(pre)),('model',clone(candidates[best]))])
    final.fit(Xtr,ytr)
    pred=final.predict(Xte)
    metrics=pd.DataFrame([{'Model':best,'Test R²':r2_score(yte,pred),'Test RMSE':np.sqrt(mean_squared_error(yte,pred)),
                           'Test MAE':mean_absolute_error(yte,pred),'Train N':len(train),'Test N':len(test)}])
    pred_frame=pd.DataFrame({'source_index':test.index,'observed':yte.to_numpy(),
                             'predicted':pred,'residual':yte.to_numpy()-pred})
    return RegressionRun(target,features,best,metrics,cvdf,pred_frame,final,len(train),len(test),seed,
                         test_fraction,split_method,notes,list(candidates))


def fitted_equation(run:RegressionRun)->str|None:
    """Simple one-feature numeric OLS equation, in original predictor units."""
    if run.best_model!='Linear regression' or len(run.features)!=1:return None
    x=run.features[0]
    pre=run.model.named_steps['preprocess']
    if x not in pre.transformers_[0][2] or pre.transformers_[0][0]!='num':return None
    model=run.model.named_steps['model']
    scale=pre.named_transformers_['num'].named_steps['scale']
    num_names=pre.transformers_[0][2]
    idx=list(num_names).index(x)
    b=float(model.coef_[idx]/scale.scale_[idx])
    a=float(model.intercept_ - np.sum(model.coef_[:len(num_names)]*scale.mean_/scale.scale_))
    return f'{run.target} = {a:.4g} + ({b:.4g} × {x})'

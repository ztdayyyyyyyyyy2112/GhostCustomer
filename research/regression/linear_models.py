"""BE-07: simple/multiple OLS with explicit future outcomes and temporal holdout."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

META={'visitorid','snapshot_date','feature_max_event_time','outcome_end','next_engagement'}

def coefficients(fit):
    ci=fit.conf_int()
    return [{'term':k,'coefficient':float(v),'ci_low':float(ci.loc[k,0]),'ci_high':float(ci.loc[k,1]),
             'p_value':float(fit.pvalues[k])} for k,v in fit.params.items()]

def analyze(frame,predictors,train_end,test_start,observed_through):
    if not predictors or len(predictors)!=len(set(predictors)) or set(predictors)&META:
        raise ValueError('Explicit unique pre-T predictor allowlist required')
    if any(k.startswith(('future_','target_','label_','post_')) for k in predictors):
        raise ValueError('Future/target fields are forbidden as predictors')
    if not META|set(predictors)<=set(frame):raise ValueError('Missing documented input columns')
    d=frame.copy()
    if d.visitorid.isna().any() or d.visitorid.astype(str).str.strip().eq('').any():raise ValueError('Missing visitor ID')
    d.visitorid=d.visitorid.astype(str)
    for k in ['snapshot_date','feature_max_event_time','outcome_end']:
        d[k]=pd.to_datetime(d[k],utc=True,errors='raise')
        if d[k].isna().any():raise ValueError('Missing temporal provenance')
    if d.duplicated(['visitorid','snapshot_date']).any():raise ValueError('Duplicate snapshot')
    if (d.feature_max_event_time>d.snapshot_date).any() or (d.outcome_end<=d.snapshot_date).any():
        raise ValueError('Post-T feature or invalid future outcome horizon')
    cut,start,observed=[pd.to_datetime(x,utc=True) for x in [train_end,test_start,observed_through]]
    if not cut<start<observed:raise ValueError('Require train_end < test_start < observed_through')
    mature=d[d.outcome_end<=observed].copy()
    if not np.isfinite(mature[predictors+['next_engagement']].to_numpy(dtype=float)).all():
        raise ValueError('Missing/nonfinite values in mature rows; document preprocessing before fitting')
    train=mature[(mature.snapshot_date<=cut)&(mature.outcome_end<=cut)]
    raw_test=mature[mature.snapshot_date>=start]
    test=raw_test[~raw_test.visitorid.isin(train.visitorid)]
    if len(train)<len(predictors)+5 or len(test)<5:raise ValueError('Insufficient independent temporal train/test rows')
    if train.visitorid.nunique()<3:raise ValueError('Too few independent training visitors')
    if train.next_engagement.nunique()<2:raise ValueError('Constant outcome')
    def design(part,cols):return sm.add_constant(part[cols].astype(float),has_constant='add')
    X=design(train,predictors)
    if np.linalg.matrix_rank(X)<X.shape[1]:raise ValueError('Rank-deficient design')
    covariance={'cov_type':'cluster','cov_kwds':{'groups':train.visitorid}} if train.visitorid.duplicated().any() else {'cov_type':'HC3'}
    results={};fitted={}
    for label,cols in [('simple',predictors[:1]),('multiple',predictors)]:
        fit=sm.OLS(train.next_engagement.astype(float),design(train,cols)).fit(**covariance)
        prediction=fit.predict(design(test,cols));errors=test.next_engagement-prediction
        fitted[label]=fit
        results[label]={'predictors':cols,'coefficients':coefficients(fit),'n_train':len(train),'n_test':len(test),
            'r_squared':float(fit.rsquared),'adjusted_r_squared':float(fit.rsquared_adj),
            'test_mae':float(np.abs(errors).mean()),'test_rmse':float(np.sqrt(np.mean(errors**2))),
            'test_negative_predictions':int((prediction<0).sum()),'covariance':covariance['cov_type']}
    audit={'input_rows':len(d),'immature_rows_excluded':int((d.outcome_end>observed).sum()),
        'training_rows':len(train),'training_visitors':train.visitorid.nunique(),'test_rows':len(test),
        'test_repeat_visitors_excluded':len(raw_test)-len(test),
        'train_max_outcome_end':train.outcome_end.max().isoformat(),'test_min_snapshot':test.snapshot_date.min().isoformat(),
        'policy':'Chronological split with mature outcomes; test visitors absent from training'}
    return results,audit,fitted

def run(source,output_dir,predictors,train_end,test_start,observed_through,data_mode,outcome_definition):
    if data_mode not in {'real','synthetic'} or not outcome_definition.strip():raise ValueError('Mode and outcome definition required')
    frame=pd.read_csv(source,dtype={'visitorid':str})
    results,audit,fitted=analyze(frame,predictors,train_end,test_start,observed_through)
    payload={'schema_version':'ols-v1','data_mode':data_mode,'input_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        'outcome':'next_engagement','outcome_definition':outcome_definition,'split':audit,'models':results,
        'assumptions':['Correct linear conditional mean','Pre-T predictors only','HC3 for unique users, clustered covariance for repeated users'],
        'limitations':['Conditional associations, not causal effects','Real diagnostics and decision D-05 require team review','For a count response, assess count-model alternatives']}
    encoded=json.dumps(payload,indent=2,allow_nan=False)  # Fail rather than publish NaN inference.
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    for label,fit in fitted.items():
        pd.DataFrame(results[label]['coefficients']).to_csv(out/f'ols_{label}_coefficients.csv',index=False)
    (out/'ols_results.json').write_text(encoded,encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4));fit=fitted['multiple']
    axes[0].scatter(fit.fittedvalues,fit.resid,s=10);axes[0].axhline(0,color='black')
    axes[0].set(xlabel='Fitted next-period engagement',ylabel='Residual')
    sm.qqplot(fit.resid,line='s',ax=axes[1]);fig.suptitle(f'{data_mode.upper()} OLS diagnostics');fig.tight_layout()
    fig.savefig(out/'ols_residuals.png',dpi=150);plt.close(fig)
    return payload

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--predictors',nargs='+',required=True);p.add_argument('--train-end',required=True)
    p.add_argument('--test-start',required=True);p.add_argument('--observed-through',required=True)
    p.add_argument('--data-mode',choices=['real','synthetic'],required=True);p.add_argument('--outcome-definition',required=True)
    a=p.parse_args();run(a.input,a.output_dir,a.predictors,a.train_end,a.test_start,a.observed_through,a.data_mode,a.outcome_definition)

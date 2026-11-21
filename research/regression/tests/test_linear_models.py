import numpy as np
import pandas as pd
import pytest
from research.regression.linear_models import analyze,run

def fixture():
    rng=np.random.default_rng(24520995);rows=[]
    for i,t in enumerate(pd.date_range('2026-01-05',periods=8,freq='7D')):
        for j in range(20):
            x=float(rng.normal());z=float(rng.normal())
            rows.append(dict(visitorid=f'{i}-{j}',snapshot_date=str(t.date()),feature_max_event_time=str((t-pd.Timedelta(days=1)).date()),
                             outcome_end=str((t+pd.Timedelta(days=7)).date()),next_engagement=10+2*x-z+rng.normal(),sessions=x,recency=z))
    return pd.DataFrame(rows)

def fit(d):return analyze(d,['sessions','recency'],'2026-02-02','2026-02-09','2026-04-01')

def test_known_synthetic_effect_and_temporal_audit():
    models,audit,_=fit(fixture())
    coef={r['term']:r['coefficient'] for r in models['multiple']['coefficients']}
    assert 1.5<coef['sessions']<2.5 and -1.5<coef['recency']<-.5
    assert audit['train_max_outcome_end']<audit['test_min_snapshot']
    assert models['multiple']['covariance']=='HC3'

@pytest.mark.parametrize('kind',['future','duplicate','missing','rank','horizon'])
def test_invalid_input(kind):
    d=fixture()
    if kind=='future':d.loc[0,'feature_max_event_time']='2099-01-01'
    if kind=='duplicate':d=pd.concat([d,d.iloc[:1]])
    if kind=='missing':d.loc[0,'sessions']=np.nan
    if kind=='rank':d['recency']=d.sessions
    if kind=='horizon':d.loc[0,'outcome_end']='2025-01-01'
    with pytest.raises(ValueError):fit(d)

def test_repeated_train_user_clustered_and_excluded_from_test():
    d=fixture();d.loc[d.index%20==0,'visitorid']='repeat'
    models,audit,_=fit(d)
    assert models['multiple']['covariance']=='cluster' and audit['test_repeat_visitors_excluded']>0

def test_outputs_have_provenance(tmp_path):
    p=tmp_path/'fixture.csv';fixture().to_csv(p,index=False)
    result=run(p,tmp_path/'out',['sessions','recency'],'2026-02-02','2026-02-09','2026-04-01','synthetic','Artificial continuous response for software tests')
    assert result['data_mode']=='synthetic' and len(result['input_sha256'])==64
    assert (tmp_path/'out/ols_residuals.png').is_file()

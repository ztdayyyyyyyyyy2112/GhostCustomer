"""Availability-aware weekly rate forecasting; candidate orders chosen before test."""
import argparse
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller,acf,pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False))

def error_metrics(actual,pred):
    a,p=np.asarray(actual),np.asarray(pred);den=np.abs(a)+np.abs(p)
    ratio=np.divide(2*np.abs(a-p),den,out=np.zeros_like(den,dtype=float),where=den!=0)
    return {'n':len(a),'mae':float(np.abs(a-p).mean()),'rmse':float(np.sqrt(np.mean((a-p)**2))),'smape_percent':float(100*ratio.mean())}

def arima_fit(series,order):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        fit=ARIMA(np.asarray(series),order=order).fit(method_kwargs={"maxiter":200})
    if not fit.mle_retvals.get('converged',True):raise ValueError('ARIMA did not converge')
    return fit

def forecast_at(d,target,order=None):
    # Forecast is issued at target week's start; only labels matured strictly before it are available.
    known=d[(d.label_end<target)&(d.week_start<target)]
    minimum = 12 if order is not None else 6
    if len(known)<minimum:raise ValueError('Too few mature observations at forecast origin')
    if not known.week_start.diff().dropna().eq(pd.Timedelta(days=7)).all():raise ValueError('Mature history has gaps')
    steps=int((target-known.week_start.iloc[-1]).days//7)
    if steps<1:raise ValueError('Target must be after available history')
    if order is None:return float(known.rate.iloc[-1]),None,None,None
    fit=arima_fit(known.rate,order);f=fit.get_forecast(steps=steps);ci=np.asarray(f.conf_int())[-1]
    return float(np.clip(np.asarray(f.predicted_mean)[-1],0,1)),float(np.clip(ci[0],0,1)),float(np.clip(ci[1],0,1)),fit

def run(rates_path,outdir,observed_through,mode='real',horizon=4):
    if horizon < 1 or horizon > 4:raise ValueError('Forecast horizon must be 1 to 4 weeks')
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True);d=pd.read_csv(rates_path)
    if not set(d.columns)>={'week_start','label_end','ghost_count','eligible_count'}:raise ValueError('Rates schema mismatch')
    d.week_start=pd.to_datetime(d.week_start,utc=True);d.label_end=pd.to_datetime(d.label_end,utc=True)
    if (d.week_start.dt.weekday != 0).any() or not d.week_start.eq(d.week_start.dt.normalize()).all():
        raise ValueError('Use Monday 00:00 UTC weekly bins')
    if d[['week_start','label_end','ghost_count','eligible_count']].isna().any().any():raise ValueError('Missing rates values')
    if d.week_start.duplicated().any():raise ValueError('Duplicate weekly bins')
    if (d.eligible_count<=0).any() or (d.ghost_count<0).any() or (d.ghost_count>d.eligible_count).any():raise ValueError('Invalid denominator/count')
    if ((d.eligible_count%1!=0)|(d.ghost_count%1!=0)).any():raise ValueError('Counts must be integers')
    if (d.label_end<=d.week_start).any():raise ValueError('Label end must follow weekly origin')
    d=d.sort_values('week_start');end=pd.to_datetime(observed_through,utc=True)
    d=d[d.label_end<=end].copy();d['rate']=d.ghost_count/d.eligible_count
    if not d.week_start.diff().dropna().eq(pd.Timedelta(days=7)).all():raise ValueError('Weekly gaps: do not silently interpolate rates')
    d.to_csv(outdir/'weekly_rates_mature.csv',index=False)
    if len(d)<10 or (d.label_end < d.week_start.iloc[int(len(d)*.8)]).sum()<6:
        payload={'data_mode':mode,'available':False,'reason':'Insufficient mature weekly bins or available history at the first test origin','n_weeks':len(d)}
        save_json(outdir/'forecast.json',payload);return payload
    split1=int(len(d)*.6);split2=int(len(d)*.8)
    test=d.iloc[split2:]
    validation=d.iloc[split1:split2]
    validation=validation[validation.label_end < test.week_start.iloc[0]]
    selected=None;comparisons=[]
    if len(d)>=40 and len(validation)>=2 and (d.label_end < validation.week_start.iloc[0]).sum()>=12 and d.rate.nunique()>1:
        for order in [(1,0,0),(0,1,1)]:
            try:
                ps=[forecast_at(d,t,order)[0] for t in validation.week_start]
                comparisons.append({'order':list(order),**error_metrics(validation.rate,ps)})
            except Exception as exc:
                comparisons.append({'order':list(order),'failed':type(exc).__name__})
        valid=[r for r in comparisons if 'mae' in r]
        baseline = error_metrics(validation.rate, [forecast_at(d,t)[0] for t in validation.week_start])
        if valid:
            best = min(valid, key=lambda r:r['mae'])
            if best['mae'] < baseline['mae']:
                selected = tuple(best['order'])
    rows=[];fallback_origins=[]
    for _,r in test.iterrows():
        naive,_,_,_=forecast_at(d,r.week_start)
        try:
            pred,lo,hi,_=forecast_at(d,r.week_start,selected) if selected else (naive,None,None,None)
        except (ValueError,np.linalg.LinAlgError):
            pred,lo,hi=naive,None,None
            fallback_origins.append(r.week_start.strftime('%Y-%m-%d'))
        rows.append({'week_start':r.week_start.strftime('%Y-%m-%d'),'actual':r.rate,'naive':naive,'predicted':pred,'lower_ci':lo,'upper_ci':hi})
    pd.DataFrame(rows).to_csv(outdir/'forecast_backtest.csv',index=False)
    actual=[r['actual'] for r in rows]
    model_metrics={'naive':error_metrics(actual,[r['naive'] for r in rows]),'selected':error_metrics(actual,[r['predicted'] for r in rows])}
    validation_start = d.week_start.iloc[split1]
    train=d[(d.week_start<validation_start)&(d.label_end<validation_start)]
    diagnostics = {}
    if len(train) >= 12 and train.rate.nunique() > 1:
        adf = adfuller(train.rate)
        lag = min(10, len(train)//2-1)
        diagnostics = {'adf_p_train_only': float(adf[1]), 'acf_train': acf(train.rate,nlags=lag).tolist(), 'pacf_train': pacf(train.rate,nlags=lag).tolist()}
    fit=None
    if selected:
        try:
            fit=arima_fit(d.rate,selected)
            diagnostics['ljung_box_p_final_fit']=float(acorr_ljungbox(fit.resid,lags=[min(5,len(d)//5)],return_df=True).lb_pvalue.iloc[0])
        except (ValueError,np.linalg.LinAlgError):
            diagnostics['final_fit_failure']='ARIMA unavailable; final forecast falls back to naive'
    # Final forecast is issued after observed_through; bridge label-delay bins to the requested future week.
    next_week=end.normalize()+pd.Timedelta(days=7-end.weekday())
    forecasts=[]
    for k in range(horizon):
        target=next_week+pd.Timedelta(days=7*k);steps=int((target-d.week_start.iloc[-1]).days//7)
        if fit is not None:
            f=fit.get_forecast(steps=steps);ci=np.asarray(f.conf_int())[-1];point=float(np.clip(np.asarray(f.predicted_mean)[-1],0,1));lo,hi=map(float,np.clip(ci,0,1))
        else:point=float(d.rate.iloc[-1]);lo=hi=None
        forecasts.append({'week_start':target.strftime('%Y-%m-%d'),'rate':point,'lower_ci':lo,'upper_ci':hi})
    payload={'data_mode':mode,'available':True,'method':f'ARIMA{selected}' if fit is not None else 'Last mature value (naive)',
             'observed_through':str(end.date()),'n_weeks':len(d),'denominator':'Eligible visitors with known mature operational labels, one snapshot per visitor per weekly bin',
             'availability_policy':'Backtest origin=target week start; history label_end must be strictly earlier. Label-delay gaps are bridged.',
             'history':[{'week_start':r.week_start.strftime('%Y-%m-%d'),'rate':r.rate} for r in d.itertuples()],
             'predictions':forecasts,'test_metrics':model_metrics,'validation_candidates':comparisons,'test_fallback_origins':fallback_origins,'diagnostics':diagnostics,
             'limitations':['ARIMA bounds clipped to [0,1]; approximate intervals','Repeated visitors across weeks may induce dependence','Synthetic series exercises code only'] if mode=='demo' else ['Approximate clipped ARIMA intervals','Operational labels and finite horizon; verify weekly denominators', 'Short series: the naive holdout has very few weekly origins and no interval when ARIMA is unsupported']}
    save_json(outdir/'forecast.json',payload)
    pd.DataFrame(forecasts).to_csv(outdir/'forecast.csv', index=False)
    api = {
        'history': [{'date': row['week_start'], 'value': row['rate']} for row in payload['history']],
        'predictions': [{'date': row['week_start'], 'value': row['rate']} for row in forecasts],
        'lower_ci': [{'date': row['week_start'], 'value': row['lower_ci']} for row in forecasts if row['lower_ci'] is not None],
        'upper_ci': [{'date': row['week_start'], 'value': row['upper_ci']} for row in forecasts if row['upper_ci'] is not None],
        'dataset_notice': f'{mode.upper()} | Retailrocket weekly operational ghost rate; proposed 4+2+2 cohort/label, exploratory forecast',
        'method': payload['method'], 'unit': 'week', 'series_length': len(d),
        'train_end': d.week_start.iloc[-1].strftime('%Y-%m-%d'),
    }
    # Holdout metrics correspond to the strategy used at the historical origins.
    if fit is not None or selected is None:
        api.update(mae=model_metrics['selected']['mae'], rmse=model_metrics['selected']['rmse'],
                   smape=model_metrics['selected']['smape_percent'])
    save_json(outdir/'forecast_api_candidate.json',api)
    fig,ax=plt.subplots(figsize=(10,4));ax.plot(d.week_start,d.rate,label='Mature observations');ax.plot(pd.to_datetime([r['week_start'] for r in rows]),[r['predicted'] for r in rows],label='Availability-aware backtest');ax.plot(pd.to_datetime([r['week_start'] for r in forecasts]),[r['rate'] for r in forecasts],label='Future forecast')
    if fit is not None:ax.fill_between(pd.to_datetime([r['week_start'] for r in forecasts]),[r['lower_ci'] for r in forecasts],[r['upper_ci'] for r in forecasts],alpha=.2)
    ax.set(title=f'{mode.upper()} weekly ghost-rate forecast',ylabel='Rate',xlabel='Week start');ax.legend();fig.tight_layout();fig.savefig(outdir/'forecast.png',dpi=150);plt.close(fig)
    return payload

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rates',required=True);p.add_argument('--outdir',required=True);p.add_argument('--observed-through',required=True);p.add_argument('--mode',choices=['demo','real'],required=True)
    p.add_argument('--horizon',type=int,default=4,help='Future weekly points; use a short horizon for a short series')
    a=p.parse_args();run(a.rates,a.outdir,a.observed_through,a.mode,a.horizon)

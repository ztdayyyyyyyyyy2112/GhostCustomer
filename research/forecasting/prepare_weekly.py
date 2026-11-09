"""BE-10: prepare dated cohort rates only after all selected labels have matured."""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

REQUIRED = {'visitorid','snapshot_date','label_end','label_status','target_ghost'}
KNOWN = {'active','ghost','recovered','inactive'}
UNKNOWN = {'unknown','candidate'}

def iso_day(value: str) -> date:
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value: raise ValueError('Dates must be ISO YYYY-MM-DD')
    return parsed

def prepare(rows, observed_through: str):
    """Snapshot and observation dates mean 00:00 UTC. Weekly grid is Monday."""
    boundary=iso_day(observed_through);groups=defaultdict(list);keys=set();horizons=set()
    for raw in rows:
        if set(raw) != REQUIRED: raise ValueError('Label columns must match documented schema exactly')
        visitor=raw['visitorid'];t=iso_day(raw['snapshot_date']);end=iso_day(raw['label_end'])
        if not isinstance(visitor,str) or not visitor.strip(): raise ValueError('Missing visitorid')
        if t.weekday()!=0: raise ValueError('snapshot_date must be Monday 00:00 UTC')
        if end<=t: raise ValueError('label_end must be after snapshot_date')
        if (visitor,t) in keys: raise ValueError('Duplicate visitor snapshot')
        keys.add((visitor,t));horizons.add((end-t).days)
        status=raw['label_status'];target=raw['target_ghost']
        if status in UNKNOWN:
            if target not in ('',None): raise ValueError('UNKNOWN/candidate must have null target')
            y=None
        elif status in KNOWN:
            if str(target) not in ('0','1'):raise ValueError('Known statuses require target 0 or 1')
            y=int(target)
            if y!=int(status=='ghost'):raise ValueError('Target and operational status disagree')
        else:raise ValueError('Unknown label_status')
        groups[t].append((end,status,y))
    if not groups: raise ValueError('No label rows supplied')
    if len(horizons)!=1:raise ValueError('Mixed label horizons: produce separate series per horizon')
    rates=[];audit=[]
    for t,records in sorted(groups.items()):
        end=max(r[0] for r in records)
        unknown=sum(r[2] is None for r in records)
        mature=end<=boundary
        known=[r[2] for r in records if r[2] is not None]
        reason='immature bin' if not mature else 'no known labels' if not known else 'included'
        audit.append({'snapshot_date':t.isoformat(),'rows':len(records),'unknown_count':unknown,
                      'label_end':end.isoformat(),'reason':reason})
        if reason!='included':continue
        rates.append({'week_start':t.isoformat(),'label_end':end.isoformat(),'ghost_count':sum(known),
                      'eligible_count':len(known),'unknown_count':unknown,'ghost_rate':sum(known)/len(known)})
    all_dates=sorted(groups);missing=[];t=all_dates[0]
    while t<=all_dates[-1]:
        if t not in groups:missing.append(t.isoformat())
        t+=timedelta(days=7)
    meta={'observed_through':boundary.isoformat(),'input_rows':len(keys),'input_snapshot_dates':len(groups),
          'label_horizon_days':next(iter(horizons)),'mature_rate_points':len(rates),'missing_snapshot_dates':missing,
          'weekly_audit':audit,'denominator':'Known active/ghost/recovered/inactive eligible visitor snapshots; unknown and candidate excluded',
          'policy':'One snapshot per visitor per Monday. Entire immature bins excluded; unknown never becomes zero. Missing weeks not interpolated.',
          'decision_status':'D-02/D-03/D-06 remain subject to owner review; no final label definition approved here'}
    return rates,meta

def run(source: Path, output_dir: Path, observed_through: str, data_mode: str, label_version: str):
    if data_mode not in {'real','synthetic'} or not label_version.strip():raise ValueError('Mode and label version required')
    with source.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames is None or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError('Missing/duplicate CSV headers')
        rows=list(reader)
    rates,meta=prepare(rows,observed_through)
    meta.update(data_mode=data_mode,label_version=label_version,input_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    output_dir.mkdir(parents=True,exist_ok=True)
    fields=['week_start','label_end','ghost_count','eligible_count','unknown_count','ghost_rate']
    with (output_dir/'weekly_rates.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rates)
    (output_dir/'weekly_rates_metadata.json').write_text(json.dumps(meta,indent=2,allow_nan=False),encoding='utf-8')
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--labels',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--observed-through',required=True);p.add_argument('--data-mode',choices=['real','synthetic'],required=True)
    p.add_argument('--label-version',required=True)
    a=p.parse_args();print(json.dumps(run(a.labels,a.output_dir,a.observed_through,a.data_mode,a.label_version),indent=2))

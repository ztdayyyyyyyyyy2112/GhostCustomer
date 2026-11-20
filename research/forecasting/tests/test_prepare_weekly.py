import csv
import pytest
from research.forecasting.prepare_weekly import prepare,run

def row(id='001',t='2026-01-05',end='2026-01-19',status='ghost',y='1'):
    return dict(visitorid=id,snapshot_date=t,label_end=end,label_status=status,target_ghost=y)

def test_boundary_and_unknown_denominator():
    rows=[row(),row('002',status='active',y='0'),row('003',status='unknown',y='')]
    rates,meta=prepare(rows,'2026-01-19')
    assert rates[0]['ghost_rate']==.5 and rates[0]['eligible_count']==2
    assert rates[0]['unknown_count']==1
    assert prepare(rows,'2026-01-18')[0]==[]

def test_missing_week_not_invented_and_repeated_visitors_allowed():
    rates,meta=prepare([row(),row(t='2026-01-19',end='2026-02-02')],'2026-02-02')
    assert len(rates)==2 and meta['missing_snapshot_dates']==['2026-01-12']

def test_all_unknown_no_rate():
    rates,meta=prepare([row(status='unknown',y='')],'2026-01-19')
    assert rates==[] and meta['weekly_audit'][0]['reason']=='no known labels'

@pytest.mark.parametrize('rows',[
    [row(),row()], [row(t='2026-01-06')], [row(end='2026-01-05')],
    [row(status='unknown',y='0')], [row(status='ghost',y='0')],
    [row(),row('002',end='2026-01-26')], [row(id='')],
])
def test_invalid_labels_rejected(rows):
    with pytest.raises(ValueError):prepare(rows,'2026-03-01')

def test_cli_output_provenance_and_leading_zero_id(tmp_path):
    source=tmp_path/'labels.csv'
    with source.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=row().keys());w.writeheader();w.writerow(row())
    meta=run(source,tmp_path/'out','2026-01-19','synthetic','test-only')
    assert meta['data_mode']=='synthetic' and len(meta['input_sha256'])==64
    assert (tmp_path/'out/weekly_rates.csv').read_text().count('\n')==2

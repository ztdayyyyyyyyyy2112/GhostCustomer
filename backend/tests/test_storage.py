import sqlite3
import pytest
from backend.app.db import initialize,connect
from backend.app.repositories.customer_repository import CustomerRepository

def detail(day='2026-01-05',id='001'):
    return {'customer':{'customer_id':id,'snapshot_date':day,'status':'active','sessions':2,'views':5,'risk_score':None},
        'status':'active','current_features':{'sessions_4w':2},'weekly_timeline':[{'week_start':'2025-12-29','phase':'observation','views':5,'carts':0,'purchases':0,'sessions':2,'active_days':2}],
        'dataset_notice':'SYNTHETIC test fixture only'}

@pytest.fixture
def repo(tmp_path):
    path=tmp_path/'db.sqlite3';initialize(path);return CustomerRepository(path)

def test_roundtrip_two_snapshots_filters_and_sql_search(repo):
    repo.replace_all([detail(),detail('2026-01-12')],data_mode='synthetic',source_version='test')
    assert repo.get('001').customer.snapshot_date=='2026-01-12'
    assert repo.get('001','2026-01-05').current_features=={'sessions_4w':2}
    assert len(repo.get('001').weekly_timeline)==1
    assert repo.list(page_size=1)[1]==2
    assert repo.list(status='ghost')[1]==0
    assert repo.list(search="' OR 1=1 --")[1]==0
    assert repo.get('missing') is None

def test_duplicate_rejected_preserves_previous_data(repo):
    repo.replace_all([detail()],data_mode='synthetic',source_version='v1')
    with pytest.raises(ValueError,match='Duplicate'):repo.replace_all([detail(),detail()],data_mode='synthetic',source_version='v2')
    assert repo.list()[1]==1

def test_transaction_rollback(repo):
    with pytest.raises(sqlite3.IntegrityError):
        with connect(repo.path) as conn:
            conn.execute("INSERT INTO provenance VALUES ('check','x')")
            conn.execute("INSERT INTO customer_weekly VALUES ('missing','2026-01-05','2025-12-29','observation',1,0,0,1,1)")
    with connect(repo.path) as conn:assert conn.execute("SELECT * FROM provenance WHERE key='check'").fetchone() is None

def test_invalid_dates_nonfinite_features_and_weekly_counts(repo):
    for key,value in [('snapshot_date','2026-02-30'),('risk_score',1.5),('views',-1)]:
        d=detail();d['customer'][key]=value
        with pytest.raises(ValueError):repo.replace_all([d],data_mode='synthetic',source_version='test')
    d=detail();d['current_features']['x']=float('nan')
    with pytest.raises(ValueError):repo.replace_all([d],data_mode='synthetic',source_version='test')
    d=detail();d['weekly_timeline'][0]['active_days']=8
    with pytest.raises(ValueError):repo.replace_all([d],data_mode='synthetic',source_version='test')

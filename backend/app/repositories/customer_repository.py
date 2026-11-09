"""Typed snapshot storage; visitorid in SQLite maps explicitly to API customer_id."""
from datetime import date
import json
import math
from pathlib import Path

from backend.app.db import connect
from backend.app.schemas.api import Customer, CustomerDetailResponse, CustomerWeekly

STATUSES = {"active", "ghost", "candidate", "recovered", "inactive", "unknown"}

def iso_date(value):
    if date.fromisoformat(value).isoformat() != value:
        raise ValueError("Use ISO YYYY-MM-DD dates")
    return value

def validated(detail):
    detail = CustomerDetailResponse.model_validate(detail)
    row = detail.customer
    iso_date(row.snapshot_date)
    if not row.customer_id or detail.status != row.status:
        raise ValueError("Snapshot ID and status must be consistent")
    for value in [row.sessions, row.views]:
        if value is not None and value < 0: raise ValueError("Negative count")
    for value in [row.decay, row.risk_score, *detail.current_features.values()]:
        if value is not None and not math.isfinite(value): raise ValueError("Non-finite feature or score")
    if row.risk_score is not None and not 0 <= row.risk_score <= 1:
        raise ValueError("Invalid risk score")
    dates = set()
    for week in detail.weekly_timeline:
        iso_date(week.week_start)
        if week.week_start in dates: raise ValueError("Duplicate weekly bin")
        dates.add(week.week_start)
        if any(getattr(week, k)<0 for k in ["views","carts","purchases","sessions","active_days"]) or week.active_days>7:
            raise ValueError("Invalid weekly count")
    # Confirmation rows are allowed for retrospective display, never as model features.
    return detail

class CustomerRepository:
    def __init__(self, path: Path): self.path = Path(path)

    def replace_all(self, details, *, data_mode: str, source_version: str):
        if data_mode not in {"real", "synthetic"} or not source_version.strip():
            raise ValueError("Explicit data mode and source version required")
        rows = [validated(d) for d in details]
        keys = [(d.customer.customer_id,d.customer.snapshot_date) for d in rows]
        if len(keys)!=len(set(keys)): raise ValueError("Duplicate customer snapshot")
        with connect(self.path) as conn:
            # Predictions and weekly rows cascade; aggregate metrics are invalid after replacement.
            conn.execute("DELETE FROM customer_snapshot")
            conn.execute("DELETE FROM metrics")
            for d in rows:
                c=d.customer
                conn.execute("INSERT INTO customer_snapshot VALUES (?,?,?,?,?,?,?,?,?)", (
                    c.customer_id,c.snapshot_date,c.status,c.sessions,c.views,c.decay,c.risk_score,
                    json.dumps(d.current_features,allow_nan=False),d.dataset_notice))
                conn.executemany("INSERT INTO customer_weekly VALUES (?,?,?,?,?,?,?,?,?)", [
                    (c.customer_id,c.snapshot_date,w.week_start,w.phase,w.views,w.carts,w.purchases,w.sessions,w.active_days)
                    for w in d.weekly_timeline])
            conn.executemany("INSERT OR REPLACE INTO provenance VALUES (?,?)", [
                ("data_mode",data_mode),("source_version",source_version)])

    def get(self, customer_id: str, snapshot_date: str | None = None):
        params=[customer_id];where="visitorid=?"
        if snapshot_date:
            where+=" AND snapshot_date=?";params.append(iso_date(snapshot_date))
        with connect(self.path) as conn:
            row=conn.execute(f"SELECT * FROM customer_snapshot WHERE {where} ORDER BY snapshot_date DESC LIMIT 1",params).fetchone()
            if row is None:return None
            weeks=conn.execute("SELECT week_start,phase,views,carts,purchases,sessions,active_days FROM customer_weekly WHERE visitorid=? AND snapshot_date=? ORDER BY week_start",(row["visitorid"],row["snapshot_date"])).fetchall()
        customer=Customer(customer_id=row['visitorid'],**{k:row[k] for k in Customer.model_fields if k!='customer_id'})
        return CustomerDetailResponse(customer=customer,current_features=json.loads(row['current_features']),
            weekly_timeline=[CustomerWeekly(**dict(w)) for w in weeks],status=customer.status,dataset_notice=row['dataset_notice'])

    def list(self, *, page=1, page_size=20, status=None, search=None):
        if page<1 or not 1<=page_size<=100:raise ValueError("Invalid pagination")
        if status is not None and status not in STATUSES:raise ValueError("Invalid status")
        terms=[];values=[]
        if status:terms.append('status=?');values.append(status)
        if search:terms.append('instr(lower(visitorid),lower(?))>0');values.append(search)
        where=' WHERE '+' AND '.join(terms) if terms else ''
        with connect(self.path) as conn:
            total=conn.execute('SELECT COUNT(*) FROM customer_snapshot'+where,values).fetchone()[0]
            rows=conn.execute('SELECT * FROM customer_snapshot'+where+' ORDER BY snapshot_date DESC,visitorid LIMIT ? OFFSET ?',values+[page_size,(page-1)*page_size]).fetchall()
        return [Customer(customer_id=r['visitorid'],**{k:r[k] for k in Customer.model_fields if k!='customer_id'}) for r in rows],total

"""SYNERGY capital ledger: verified provenance, deduplicated import, allocation planning.

All side effects are LOCAL SQLite writes. No exchange, broker, bank or provider calls.
'verified' means verified dataset invariants and source identity, NOT bank certification.
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json, re
from . import service

D=Decimal
CATEGORIES=frozenset(("income","expense","transfer","investment","refund"))
ISO=re.compile(r"^[A-Z]{3}$")
DAY=re.compile(r"^\d{4}-\d{2}-\d{2}$")
UID=re.compile(r"^[a-zA-Z0-9_.:/-]{1,160}$")

def cents(value):
    if isinstance(value,bool) or not isinstance(value,(str,int,Decimal)):
        raise ValueError("amount must be decimal text")
    try:v=D(str(value))
    except InvalidOperation as e:raise ValueError("invalid amount") from e
    if not v.is_finite() or v<0 or v>1_000_000_000_000:raise ValueError("amount out of range")
    if v!=v.quantize(D(".01")):raise ValueError("only 2 decimal places supported")
    return int((v*100).to_integral_value())

def initialize(db):
    db.executescript("""CREATE TABLE IF NOT EXISTS capital_sources(
      id INTEGER PRIMARY KEY, source_id TEXT NOT NULL UNIQUE, sha256 TEXT NOT NULL,
      currency TEXT NOT NULL, period_start TEXT NOT NULL, period_end TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'source_supplied_unverified', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS capital_entries(
      id INTEGER PRIMARY KEY, source_id TEXT NOT NULL, entry_id TEXT NOT NULL,
      date TEXT NOT NULL, currency TEXT NOT NULL, kind TEXT NOT NULL, amount_minor INTEGER NOT NULL,
      memo TEXT NOT NULL, FOREIGN KEY(source_id) REFERENCES capital_sources(source_id),
      UNIQUE(source_id, entry_id));
    CREATE TABLE IF NOT EXISTS capital_plans(
      id INTEGER PRIMARY KEY, currency TEXT NOT NULL, period_start TEXT NOT NULL,
      period_end TEXT NOT NULL, source_hash TEXT NOT NULL, delta_minor INTEGER NOT NULL,
      reserve_minor INTEGER NOT NULL, contribution_minor INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE INDEX IF NOT EXISTS capital_entries_period ON capital_entries(currency,date);
    """)

def _valid_date(x):
    if not isinstance(x,str) or not DAY.fullmatch(x):raise ValueError("bad date")
    try:date.fromisoformat(x)
    except ValueError as e:raise ValueError("invalid date") from e
    return x

def _parse_batch(data):
    if not isinstance(data,dict):raise ValueError("object required")
    src=data.get("source_id")
    if not isinstance(src,str) or not UID.fullmatch(src):raise ValueError("source_id invalid")
    c=data.get("currency")
    if not isinstance(c,str) or not ISO.fullmatch(c):raise ValueError("currency ISO 4217 code required")
    start=_valid_date(data.get("period_start"));end=_valid_date(data.get("period_end"))
    if start>end:raise ValueError("inverted period")
    rows=data.get("entries")
    if not isinstance(rows,list) or not 1<=len(rows)<=1000:raise ValueError("1-1000 entries required")
    parsed=[];seen=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError("invalid entry")
        uid=row.get("entry_id")
        if not isinstance(uid,str) or not UID.fullmatch(uid) or uid in seen:raise ValueError("duplicate or invalid entry_id")
        seen.add(uid)
        day=_valid_date(row.get("date"))
        if not start<=day<=end:raise ValueError("entry outside declared period")
        if row.get("kind") not in CATEGORIES:raise ValueError("invalid kind")
        if row.get("currency",c)!=c:raise ValueError("mixed currencies forbidden")
        memo=row.get("memo","")
        if not isinstance(memo,str) or len(memo)>2000:raise ValueError("invalid memo")
        parsed.append({"entry_id":uid,"date":day,"currency":c,"kind":row["kind"],"amount_minor":cents(row.get("amount")),"memo":memo})
    return src,c,start,end,sorted(parsed,key=lambda x:x["entry_id"])

def import_entries(payload):
    """One source = one immutable set of rows. Replays are idempotent; changed source is a conflict."""
    src,c,start,end,rows=_parse_batch(payload)
    canonical=json.dumps({"source_id":src,"currency":c,"period_start":start,"period_end":end,"entries":rows},sort_keys=True,separators=(",",":"),ensure_ascii=False)
    digest=sha256(canonical.encode()).hexdigest()
    with service.LOCK,service.connect() as db:
        initialize(db)
        old=db.execute("SELECT sha256 FROM capital_sources WHERE source_id=?",(src,)).fetchone()
        if old:
            if old["sha256"]!=digest:raise ValueError("SOURCE_CONFLICT: import immutable; supply a new source_id")
            return {"source_id":src,"sha256":digest,"status":"duplicate_ignored","imported":0,"external_effects":False}
        db.execute("INSERT INTO capital_sources(source_id,sha256,currency,period_start,period_end) VALUES(?,?,?,?,?)",(src,digest,c,start,end))
        db.executemany("INSERT INTO capital_entries(source_id,entry_id,date,currency,kind,amount_minor,memo) VALUES(?,?,?,?,?,?,?)",[(src,x["entry_id"],x["date"],c,x["kind"],x["amount_minor"],x["memo"]) for x in rows])
        service.emit(db,"capital.import",src,{"count":len(rows),"sha256":digest,"currency":c,"verification":"source_supplied_unverified"})
    return {"source_id":src,"sha256":digest,"status":"imported_source_unverified","imported":len(rows),"external_effects":False}

def summary(currency,start,end):
    if not isinstance(currency,str) or not ISO.fullmatch(currency):raise ValueError("invalid currency")
    start=_valid_date(start);end=_valid_date(end)
    if start>end:raise ValueError("inverted period")
    with service.LOCK,service.connect() as db:
        initialize(db)
        rows=[dict(r) for r in db.execute(
         "SELECT kind,COALESCE(SUM(amount_minor),0) AS total,COUNT(*) AS count FROM capital_entries WHERE currency=? AND date BETWEEN ? AND ? GROUP BY kind",
         (currency,start,end))]
        srcs=[dict(r) for r in db.execute(
         "SELECT DISTINCT s.source_id,s.sha256,s.status FROM capital_sources s JOIN capital_entries e ON e.source_id=s.source_id WHERE e.currency=? AND e.date BETWEEN ? AND ? ORDER BY s.source_id",
         (currency,start,end))]
    totals={r["kind"]:r["total"] for r in rows}
    income=totals.get("income",0);expense=totals.get("expense",0)
    # Refunds are not assumed to be income: separately disclosed until reconciled.
    delta=income-expense
    provenance=sha256(json.dumps(srcs,sort_keys=True).encode()).hexdigest()
    return {"currency":currency,"period_start":start,"period_end":end,
     "income_minor":income,"expense_minor":expense,"delta_minor":delta,
     "transfers_minor":totals.get("transfer",0),"investments_minor":totals.get("investment",0),
     "refunds_pending_classification_minor":totals.get("refund",0),
     "source_count":len(srcs),"source_provenance":srcs,"source_hash":provenance,
     "verified_by_bank":False,"input_status":"SOURCE_SUPPLIED_UNVERIFIED","external_effects":False}

def allocation_plan(currency,start,end,reserve_pct,investment_pct,minimum_buffer="0"):
    s=summary(currency,start,end)
    if s["source_count"]==0:raise ValueError("NO_INPUT_SOURCES")
    try:reserve=D(str(reserve_pct));invest=D(str(investment_pct))
    except InvalidOperation as e:raise ValueError("invalid percent") from e
    if not reserve.is_finite() or not invest.is_finite() or min(reserve,invest)<0 or max(reserve,invest)>100:raise ValueError("percentage must be 0..100")
    buffer=cents(minimum_buffer)
    delta=max(0,s["delta_minor"])
    surplus=max(0,delta-buffer)
    r=int((D(surplus)*reserve/100).quantize(D("1"),rounding=ROUND_HALF_UP))
    contrib=int((D(surplus-r)*invest/100).quantize(D("1"),rounding=ROUND_HALF_UP))
    with service.LOCK,service.connect() as db:
        initialize(db)
        cur=db.execute("INSERT INTO capital_plans(currency,period_start,period_end,source_hash,delta_minor,reserve_minor,contribution_minor) VALUES(?,?,?,?,?,?,?)",
        (currency,start,end,s["source_hash"],s["delta_minor"],r,contrib))
        pid=cur.lastrowid
        service.emit(db,"capital.plan",str(pid),{"source_hash":s["source_hash"],"delta_minor":s["delta_minor"],"reserve_minor":r,"contribution_minor":contrib,"status":"draft"})
    return {"id":pid,"status":"draft_unapproved","currency":currency,"delta_minor":s["delta_minor"],
     "liquidity_buffer_minor":buffer,"reserve_minor":r,"investable_minor":contrib,
     "source_hash":s["source_hash"],"verified_by_bank":False,"trading_enabled":False,"external_effects":False}

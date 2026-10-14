"""Slow-moving CAN SLIM inputs. Missing data remains unknown, never fabricated."""
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf
from rules import safe

CACHE = Path(__file__).parent / "cache" / "fundamentals.json"
LOG = logging.getLogger("fundamentals")


def value(table, names, col):
    for name in names:
        if name in table.index:
            v = safe(table.loc[name, col])
            if v is not None:
                return v
    return None


def growth(now, previous):
    return safe((now/previous-1)*100) if now is not None and previous is not None and previous>0 else None


def read_one(symbol, asof):
    output = dict(status="Unknown / provider unavailable",
                  retrieved_at=datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
                  eps_growth=None, sales_growth=None, annual_pass=None,
                  annual_growth=None, roe=None, institutional_pct=None)
    try:
        ticker = yf.Ticker(symbol+".NS")
        quarterly = ticker.quarterly_income_stmt
        annual = ticker.income_stmt
        info = ticker.get_info()
        if not quarterly.empty:
            cols = sorted([c for c in quarterly.columns if pd.Timestamp(c)<=asof], reverse=True)
            if cols and (asof-pd.Timestamp(cols[0])).days <= 180:
                latest = cols[0]
                prior = [c for c in cols[1:] if 320<=(pd.Timestamp(latest)-pd.Timestamp(c)).days<=410]
                if prior:
                    prev=prior[0]
                    output["eps_growth"]=growth(value(quarterly,["Diluted EPS","Basic EPS"],latest),
                                                value(quarterly,["Diluted EPS","Basic EPS"],prev))
                    output["sales_growth"]=growth(value(quarterly,["Total Revenue","Operating Revenue"],latest),
                                                  value(quarterly,["Total Revenue","Operating Revenue"],prev))
                output["quarter_end"]=str(pd.Timestamp(latest).date())
        if not annual.empty:
            cols=sorted([c for c in annual.columns if pd.Timestamp(c)<=asof],reverse=True)
            if len(cols)>=4 and (asof-pd.Timestamp(cols[0])).days<=550:
                dates=cols[:4]
                eps=[value(annual,["Diluted EPS","Basic EPS"],c) for c in dates]
                changes=[growth(eps[i],eps[i+1]) for i in range(3)]
                if all(v is not None for v in changes):
                    valid_spacing=all(320<=(pd.Timestamp(dates[i])-pd.Timestamp(dates[i+1])).days<=410 for i in range(3))
                    output["annual_growth"]=changes
                    output["annual_pass"]=valid_spacing and all(v>=25 for v in changes) and all(v is not None and v>0 for v in eps)
                output["annual_end"]=str(pd.Timestamp(cols[0]).date())
                # ROE and ownership are current provider snapshots, not historic backtest facts.
                output["roe"]=safe(info.get("returnOnEquity")*100) if info.get("returnOnEquity") is not None else None
                output["institutional_pct"]=safe(info.get("heldPercentInstitutions")*100) if info.get("heldPercentInstitutions") is not None else None
        output["status"]="Available" if any(output[k] is not None for k in ("eps_growth","sales_growth","annual_pass")) else "Unknown / incomplete financial statements"
    except Exception as exc:
        LOG.debug("Fundamentals unavailable for %s: %s",symbol,exc)
    return symbol,output


def acquire(symbols, asof, cache_only=False):
    CACHE.parent.mkdir(exist_ok=True)
    cache=json.loads(CACHE.read_text()) if CACHE.exists() else {}
    today=datetime.now(ZoneInfo("Asia/Kolkata"))
    pending=[]
    for symbol in symbols:
        entry=cache.get(symbol,{})
        try:
            age=(today-datetime.fromisoformat(entry["retrieved_at"])).total_seconds()
            # Retry incomplete records daily; complete financials refresh weekly.
            ttl=86400 if entry.get("status")!="Available" else 7*86400
            if 0<=age<ttl:
                continue
        except (KeyError,ValueError,TypeError):
            pass
        pending.append(symbol)
    if not cache_only:
        LOG.info("Retrieving CAN SLIM fundamentals for %s stocks",len(pending))
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i,(symbol,entry) in enumerate(pool.map(lambda s:read_one(s,asof),pending)):
                cache[symbol]=entry
                if i%20==0:
                    CACHE.write_text(json.dumps(cache,allow_nan=False))
        CACHE.write_text(json.dumps(cache,allow_nan=False))
    # Enforce age checks even when restoring a cache after a prolonged outage.
    cleaned={}
    for symbol in symbols:
        entry=cache.get(symbol,{}).copy()
        if entry.get("quarter_end") and (asof-pd.Timestamp(entry["quarter_end"])).days>180:
            entry.update(eps_growth=None,sales_growth=None,status="Unknown / stale quarterly inputs")
        if entry.get("annual_end") and (asof-pd.Timestamp(entry["annual_end"])).days>550:
            entry.update(annual_pass=None,annual_growth=None,roe=None,institutional_pct=None,status="Unknown / stale annual inputs")
        cleaned[symbol]=entry
    return cleaned

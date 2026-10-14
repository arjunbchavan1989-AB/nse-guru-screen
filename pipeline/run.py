"""Independent daily Guru Screen. Production never reads another dashboard."""
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
from benchmark import load as load_benchmark, excess, NAME
from market_data import build, liquidity
from fundamentals import acquire
from rules import SCAN_DEFINITIONS, technical, add_ranks, assess, safe

ROOT=Path(__file__).resolve().parent.parent
PUBLIC=ROOT/"client/public"
LOG=logging.getLogger("guru")


def bootstrap(path):
    """One-time local BYOD import, never used by scheduled GitHub production."""
    source=json.loads((path/"data/latest.json").read_text())
    rows=[];frames={}
    for parent in source["rows"]:
        chart=json.loads((path/"data/charts"/(parent["symbol"]+".json")).read_text())
        frame=pd.DataFrame(chart["bars"]).rename(columns=dict(t="date",o="Open",h="High",l="Low",c="Close",v="Volume"))
        frame.index=pd.to_datetime(frame.pop("date"))
        vals,ok=liquidity(frame)
        if not ok or parent["market_cap_cr"]<=500:
            continue
        rows.append({**parent,**vals,"name":parent["symbol"]})
        frames[parent["symbol"]]=frame[["Open","High","Low","Close","Volume"]]
    return dict(rows=rows,last_trading_date=source["last_trading_date"],
                market_data=dict(mode="One-time local BYOD bootstrap; independent daily acquisition starts with GitHub workflow",
                                 official_listing_count=source["market_data"]["official_listing_count"],
                                 listing_history_coverage_pct=source["market_data"]["listing_history_coverage_pct"],
                                 bootstrap=True),filters=source["filters"],company_names={}),frames


def scan(bootstrap_path=None):
    source,frames=bootstrap(Path(bootstrap_path)) if bootstrap_path else build()
    session=pd.Timestamp(source["last_trading_date"])
    if bootstrap_path:
        benchmark=pd.read_csv(ROOT/"pipeline/benchmark_midsmall400.csv",parse_dates=["date"]).set_index("date").loc[:session]
    else:
        benchmark=load_benchmark(session)
    if benchmark.empty or benchmark.index[-1]!=session:
        raise RuntimeError("Benchmark and stock sessions do not match")
    bm=benchmark.close.rolling(50).mean()
    market_up=bool(benchmark.close.iloc[-1]>bm.iloc[-1] and bm.iloc[-1]>bm.iloc[-6]) if len(benchmark)>=55 else None
    rows=[];charts={}
    metadata={r["symbol"]:r for r in source["rows"]}
    names=source.get("company_names",{})
    for symbol,frame in frames.items():
        if symbol not in metadata or len(frame)<21:
            continue
        parent={**metadata[symbol],"name":names.get(symbol,metadata[symbol].get("name",symbol))}
        row,bars,events=technical(frame,parent)
        row["rs_excess_pct"]=safe(excess(frame.rename(columns=str.lower),benchmark))
        rows.append(row)
        charts[symbol]=dict(symbol=symbol,date=str(session.date()),bars=bars[-300:],events=events)
    if not rows or len(rows)/len(metadata)<.95:
        raise RuntimeError("Under 95% of universe has 21 completed bars; refusing output")
    add_ranks(rows)
    # Fetch slow fundamentals only for stocks not already ruled out by N/S/L.
    can_candidates=[r["symbol"] for r in rows if r["_high252"] is not None and
                    r["close"]>=.95*r["_high252"] and r["rvol"]>=1.25 and
                    (r.get("rs_3m") or 0)>=80 and r["_above50"]]
    funds=acquire(can_candidates,session,cache_only=bool(bootstrap_path))
    for row in rows:
        assess(row,funds.get(row["symbol"]),market_up)
    now=datetime.now(ZoneInfo("Asia/Kolkata"))
    counts={s["id"]:sum(s["id"] in r["matches"] for r in rows) for s in SCAN_DEFINITIONS}
    long_history_count=sum(len(frames[r["symbol"]])>=100 for r in rows)
    payload=dict(schema_version=1,generated_at=now.isoformat(),last_trading_date=str(session.date()),
                 benchmark=NAME,qualified_count=len(rows),market_data={**source["market_data"],
                 "technical_history_exclusions":len(metadata)-len(rows),
                 "long_history_count":long_history_count,
                 "short_history_count":len(rows)-long_history_count,
                 "fundamental_candidates":len(can_candidates),
                 "fundamentals_available":sum(f.get("status")=="Available" for f in funds.values())},
                 scans=SCAN_DEFINITIONS,rows=sorted(rows,key=lambda r:(-len(r["matches"]),-r["change_pct"],r["symbol"])),
                 counts=counts,multi_count=sum(len(r["matches"])>=2 for r in rows),
                 market_regime="Constructive" if market_up else "Defensive" if market_up is False else "Unknown",
                 filters=source["filters"],refresh_schedule="Every day at 19:30 Asia/Kolkata (14:00 UTC)",
                 notes=["Latest completed closing bars come from official, date-validated NSE EOD files; historical backfill is vendor data.",
                        "Price/volume candidates are not confirmed EPs; catalyst status remains unverified.",
                        "Universe ADR20 = mean((high − low) / previous close ×100), not true range.",
                        "Short-history listings stay in the universe. Each scan independently enforces its required lookbacks.",
                        "RS percentiles are cross-sectional within this eligible universe; RS excess uses Nifty MidSmallcap 400.",
                        "RVOL denominator excludes today's volume. Universe liquidity averages include the completed EOD bar.",
                        "Pattern thresholds are disclosed approximations, not proprietary guru code.",
                        "CAN SLIM matches are quantitative candidates; N/I/M use the documented proxies.",
                        "Qullamaggie original mode changes the gap gate only; other numeric gates remain disclosed implementation choices.",
                        "Reported statement dates are fiscal period ends, not original filing timestamps. Not a point-in-time backtest.",
                        "Non-trading days retain the last verified completed NSE session."])
    # Prepare JSON before replacing the last good public snapshot.
    text=json.dumps(payload,separators=(",",":"),allow_nan=False)
    data=PUBLIC/"data";(data/"charts").mkdir(parents=True,exist_ok=True)
    for symbol,chart in charts.items():
        (data/"charts"/f"{symbol}.json").write_text(json.dumps(chart,separators=(",",":"),allow_nan=False))
    temporary=data/"latest.next.json";temporary.write_text(text);temporary.replace(data/"latest.json")
    archive=ROOT/"snapshots";archive.mkdir(exist_ok=True)
    (archive/f"{session.date()}.json").write_text(text)
    index=sorted([p.stem for p in archive.glob("*.json")],reverse=True)
    (data/"sessions.json").write_text(json.dumps(index))
    (data/"history").mkdir(exist_ok=True)
    for old in archive.glob("*.json"):
        (data/"history"/old.name).write_bytes(old.read_bytes())
    LOG.info("Guru snapshot: %s eligible, %s multi-scan, session %s, scans %s",len(rows),payload["multi_count"],session.date(),counts)
    return payload


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(message)s")
    p=argparse.ArgumentParser()
    p.add_argument("--bootstrap",help="One-time local BYOD price import; never used in production")
    args=p.parse_args()
    scan(args.bootstrap)

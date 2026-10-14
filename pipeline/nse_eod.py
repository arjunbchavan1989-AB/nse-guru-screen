"""Date-validated official NSE closing bars, acquired by this repository itself."""
import logging
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile
import numpy as np
import pandas as pd

LOG=logging.getLogger("nse-eod")
CACHE=Path(__file__).parent/"cache"/"official-eod"

class OfficialBars(dict):
    def __init__(self, values, expected_sessions):
        super().__init__(values)
        self.expected_sessions=expected_sessions


def parse(data, session, udiff=False):
    f=pd.read_csv(BytesIO(data),skipinitialspace=True)
    f.columns=f.columns.str.strip()
    if udiff:
        f=f.rename(columns={"TckrSymb":"SYMBOL","SctySrs":"SERIES","TradDt":"DATE1",
                            "OpnPric":"OPEN_PRICE","HghPric":"HIGH_PRICE","LwPric":"LOW_PRICE",
                            "ClsPric":"CLOSE_PRICE","PrvsClsgPric":"PREV_CLOSE","TtlTradgVol":"TTL_TRD_QNTY"})
    required={"SYMBOL","SERIES","DATE1","OPEN_PRICE","HIGH_PRICE","LOW_PRICE","CLOSE_PRICE","PREV_CLOSE","TTL_TRD_QNTY"}
    if not required.issubset(f.columns):
        raise ValueError("Official EOD schema mismatch")
    f=f[f.SERIES.astype(str).str.strip()=="EQ"].copy()
    dates=pd.to_datetime(f.DATE1,dayfirst=not udiff,errors="coerce").dt.normalize()
    if dates.isna().any() or not (dates==pd.Timestamp(session).normalize()).all():
        raise ValueError("Official EOD redirected to a different session")
    f["SYMBOL"]=f.SYMBOL.str.strip()
    f=f.rename(columns={"OPEN_PRICE":"Open","HIGH_PRICE":"High","LOW_PRICE":"Low",
                        "CLOSE_PRICE":"Close","PREV_CLOSE":"PreviousClose","TTL_TRD_QNTY":"Volume"})
    for name in ["Open","High","Low","Close","PreviousClose","Volume"]:
        f[name]=pd.to_numeric(f[name],errors="coerce")
    f=f.dropna(subset=["Open","High","Low","Close","Volume"])
    f=f[(f.Volume>0)&(f.Close>0)&(f.Open>0)&(f.Low>0)&
        (f.High>=f[["Open","Close"]].max(axis=1)-.051)&
        (f.Low<=f[["Open","Close"]].min(axis=1)+.051)]
    if f.SYMBOL.duplicated().any():
        raise ValueError("Duplicate EQ symbol in official EOD")
    return f.set_index("SYMBOL")[["Open","High","Low","Close","PreviousClose","Volume"]]


def acquire(session):
    CACHE.mkdir(parents=True,exist_ok=True)
    def one(day):
        legacy=CACHE/f"{day.date()}.csv"
        udiff=CACHE/f"{day.date()}.udiff.csv"
        for path,kind in [(legacy,False),(udiff,True)]:
            if path.exists():
                try:return day,parse(path.read_bytes(),day,kind)
                except (ValueError,KeyError):pass
        urls=[
            (f"https://archives.nseindia.com/products/content/sec_bhavdata_full_{day:%d%m%Y}.csv",False),
            (f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip",True),
        ]
        for url,kind in urls:
            try:
                with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=20) as r:
                    data=r.read()
                if kind:
                    with ZipFile(BytesIO(data)) as z:
                        names=[name for name in z.namelist() if name.lower().endswith(".csv")]
                        if len(names)!=1:raise ValueError("Ambiguous official bhavcopy ZIP")
                        data=z.read(names[0])
                frame=parse(data,day,kind)
                if len(frame)<1000:raise ValueError("Incomplete official EQ close file")
                (udiff if kind else legacy).write_bytes(data)
                return day,frame
            except Exception as exc:
                LOG.debug("Official EOD unavailable %s: %s",url,exc)
        return day,None
    days=list(pd.bdate_range(session-pd.Timedelta(days=10),session))
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=dict(pool.map(one,days))
    results={day:f for day,f in results.items() if f is not None}
    if session not in results:
        raise RuntimeError(f"Official NSE closing bars unavailable for {session.date()}; refusing stale vendor prices")
    LOG.info("Official NSE EOD verified: %s EQ symbols for %s; %s recent files",
             len(results[session]),session.date(),len(results))
    benchmark_path=Path(__file__).parent/"benchmark_midsmall400.csv"
    calendar=pd.to_datetime(pd.read_csv(benchmark_path)["date"]) if benchmark_path.exists() else pd.DatetimeIndex([])
    expected=sorted(set(pd.Timestamp(d).normalize() for d in calendar)|set(results)|{session})
    return OfficialBars(results,expected)


def overlay(frame,symbol,session,official):
    """Append verified missing sessions, never jump an unverified history gap."""
    if frame is None or frame.empty:return frame
    out=frame.copy()
    earliest=min(official)
    if out.index[-1]<earliest:
        return out
    expected=getattr(official,"expected_sessions",list(official))
    if any(out.index[-1]<day<=session and day not in official for day in expected):
        # Let the history backfill repair this gap rather than fabricate continuity.
        return out
    for day,daily in sorted(official.items()):
        if day>session or day<out.index[-1] or symbol not in daily.index:
            continue
        r=daily.loc[symbol]
        # Reconcile an official adjusted previous-close reference on split-like
        # events. Do not manufacture history through large unexplained differences.
        if day>out.index[-1] and r.PreviousClose>0:
            ratio=float(r.PreviousClose/out.Close.iloc[-1])
            recognised=any(abs(ratio-k)/k<.001 for k in (.1,.2,.25,1/3,.5,2,3,4,5,10))
            if abs(ratio-1)>.02 and recognised:
                out.loc[:,["Open","High","Low","Close"]]*=ratio
                out.loc[:,"Volume"]/=ratio
                LOG.warning("Split-like reference reconciliation %s %s ratio %.6f",symbol,day.date(),ratio)
        out.loc[day,["Open","High","Low","Close","Volume"]]=r[["Open","High","Low","Close","Volume"]].to_numpy()
    return out.sort_index()

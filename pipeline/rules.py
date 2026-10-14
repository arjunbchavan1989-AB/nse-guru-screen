"""Public rules plus explicitly disclosed engineering adaptations.

All pivots and RVOL baselines exclude the signal day. Cross-sectional ranks
use the full eligible universe, before any guru scan is applied.
"""
import math
import numpy as np
import pandas as pd
from cycle import classify as kell_classify, PHASES
from ep_rules import metrics as ep_metrics

PHASE_NAMES = {p[0]: p[1] for p in PHASES}
Q_SOURCE = "https://x.com/SteveDJacobs/status/1971976586355220541"
KK_SOURCE = "https://qullamaggie.com/my-3-timeless-setups-that-have-made-me-tens-of-millions/"
J_SOURCE = "https://x.com/SteveDJacobs/status/1973670043725529454"
TL_SOURCE = "https://traderlion.com/technical-analysis/finding-your-trading-edge/"
SCAN_DEFINITIONS = [
    dict(id="q_breakout", name="Qullamaggie Breakout", short="Q Breakout", guru="Qullamaggie",
         kind="Published Jacobs filter",
         description="A momentum-leader screen, not proof of a completed consolidation breakout.",
         rules=["RS percentile ≥97 on any of 1W / 1M / 3M / 6M.",
                "Close ≥ EMA10 ≥ SMA20 ≥ SMA50 ≥ SMA100 ≥ SMA200.",
                "ATR%-percentile ≥50 within the eligible NSE universe (explicit proxy for Jacobs' ATR RS).",
                "Close in the upper half of its 20-session high/low range."],
         sources=[dict(title="Jacobs' explicit Qullamaggie criteria", url=Q_SOURCE),
                  dict(title="Kristjan's public setup guide", url=KK_SOURCE)]),
    dict(id="q_ep", name="Qullamaggie EP", short="Q EP", guru="Qullamaggie",
         kind="Technical candidate",
         description="A price/volume EP candidate. News and earnings surprise must be verified separately.",
         rules=["India mode: gap >3%; original mode: gap ≥10%.",
                "RVOL >3× the previous 20-session average; close ≥open; positive day.",
                "Close in the upper 35% of the day's high/low range.",
                "Prior-price/volume neglect score ≥60 and prior 20-session return ≤10%.",
                "Catalyst is NOT inferred from price. An unverified candidate is never labelled confirmed EP."],
         sources=[dict(title="Qullamaggie's original EP rules", url=KK_SOURCE)]),
    dict(id="kell", name="Oliver Kell", short="Kell", guru="Oliver Kell",
         kind="Coded pattern approximation",
         description="Fresh bullish Wedge Pop, EMA Crossback or Base 'n Break. EE and TR are context, not fresh entry signals.",
         rules=["EMA10 / EMA20, Wilder ATR14 and shifted 5/10-session pivots.",
                "WP: reclaim both EMAs and prior 5-session high after weakness; RVOL ≥1.2.",
                "CB: first supportive EMA retest within 30 sessions after a Wedge Pop.",
                "BB: contracted 10-session base breakout, bullish EMA structure and RVOL ≥1.2.",
                "Only today's WP / CB / BB counts as a match; retained historical phases do not."],
         sources=[dict(title="Public Cycle of Price Action", url="https://traderlion.com/technical-analysis/chart-patterns/cycle-of-price-action-by-oliver-kell/")]),
    dict(id="sb4", name="Stockbee 4% Move", short="SB 4%", guru="Stockbee",
         kind="Public concept / 20D volume adaptation",
         description="Daily gain of at least 4% on above-average share volume.",
         rules=["Close / previous close −1 ≥4%.", "Volume >mean of the previous 20 sessions.",
                "The signal day is excluded from its average-volume denominator."],
         sources=[dict(title="Stockbee's 4% breakout scan", url="https://stockbee.blogspot.com/2017/09/how-to-use-4-and-breakout-scans.html")]),
    dict(id="sb8", name="Stockbee 8 Million EP Hunt", short="SB 8M", guru="Stockbee",
         kind="User-requested 8M adaptation",
         description="High-volume up-day discovery list, not an assertion that an episodic catalyst exists.",
         rules=["Daily share volume ≥8,000,000.", "RVOL ≥1.25× the previous 20-session average.",
                "Close >previous close. Catalyst still requires review.",
                "Jacobs publishes 9 million shares; this explicitly uses your requested 8 million."],
         sources=[dict(title="Jacobs' 9 Million Movers criteria", url="https://x.com/SteveDJacobs/status/1931686377663475773")]),
    dict(id="canslim", name="O'Neil CAN SLIM", short="CAN SLIM", guru="William O'Neil",
         kind="Quantitative candidates only",
         description="C/A earnings checks plus explicit N/S/L/I/M proxies. A quantitative pass is not a full discretionary CAN SLIM endorsement.",
         rules=["C: latest quarterly EPS and sales each ≥25% YoY, with positive prior EPS.",
                "A: three consecutive annual EPS growth rates ≥25%, positive EPS, ROE ≥17%.",
                "N proxy: close within 5% of its 252-session high.",
                "S proxy: RVOL ≥1.25; L proxy: 3M RS percentile ≥80 and close ≥SMA50.",
                "I proxy: reported institutional ownership >0; this does not prove rising sponsorship.",
                "M proxy: Nifty MidSmallcap 400 above rising SMA50.",
                "Quarterly data older than 180 days or annual data older than 550 days is unknown, never a pass."],
         sources=[dict(title="IBD's CAN SLIM framework", url="https://myibd.investors.com/welcome/"),
                  dict(title="IBD's current earnings requirement", url="https://www.investors.com/ibd-university/can-slim/quarterly-earnings/")]),
    dict(id="club97", name="97 Club", short="97 Club", guru="Steve Jacobs",
         kind="Published rule / NSE-relative ranks",
         description="Top 3% on all three horizons, ranked before any guru filter.",
         rules=["Daily RS percentile ≥97.", "Weekly (5-session) RS percentile ≥97.",
                "Monthly (21-session) RS percentile ≥97.",
                "Ranks are within the eligible NSE universe, not proprietary IBD RS ratings."],
         sources=[dict(title="Jacobs explains the 97 Club", url=J_SOURCE)]),
    dict(id="launchpad", name="TraderLion Launchpad", short="Launchpad", guru="TraderLion",
         kind="Coded pattern approximation",
         description="A pre-breakout compression list built from the publicly described tightness, dry-up and MA-support concepts.",
         rules=["Close >rising EMA20; EMA10 ≥EMA20; close ≥SMA50; 3M RS ≥80.",
                "Five-session high/low width ≤10%, and average range ≤80% of preceding 20 sessions.",
                "Five-session mean volume ≤75% of preceding 20-session mean.",
                "Close within 1 ATR of EMA10 or EMA20, and within 10% of 63-session high.",
                "Numerical thresholds are transparent engineering choices, not TraderLion's private scan."],
         sources=[dict(title="TraderLion's public Launch Pad description", url=TL_SOURCE)]),
    dict(id="htf", name="TraderLion High Tight Flag", short="HTF", guru="TraderLion",
         kind="Public geometry / coded approximation",
         description="A genuine prior doubling with a separate 3–5 week flag. Both constructive flags and today's breakout are visible.",
         rules=["Flagpole: price doubles in 20–40 sessions, ending before the flag starts.",
                "Flag duration 15–25 sessions; flag depth 10–25% from the pole high.",
                "No deep undercut: no flag low below 75% of the pole high.",
                "Constructive flag: close within 10% of flag high and volume dries below 80% of pole mean.",
                "Breakout: close clears the prior flag high with RVOL ≥1.25.",
                "Flagpole and flag do not overlap. Fundamental catalyst requires separate review."],
         sources=[dict(title="TraderLion's published HTF criteria", url="https://traderlion.com/technical-analysis/high-tight-flag-pattern/")]),
]


def safe(v, digits=4):
    try:
        return round(float(v), digits) if math.isfinite(float(v)) else None
    except (ValueError, TypeError):
        return None


def gate(label, passed, value):
    return dict(label=label, passed=bool(passed) if passed is not None else None, value=str(value))


def htf_geometry(d):
    """Find an ordered pole then a non-overlapping flag, never today's own pivot."""
    for flag_n in range(15, 26):
        for pole_n in range(20, 41):
            if len(d) < flag_n + pole_n + 2:
                continue
            flag = d.iloc[-flag_n-1:-1]
            pole = d.iloc[-flag_n-pole_n-1:-flag_n-1]
            pole_high = float(pole.high.max())
            gain = pole_high / float(pole.close.iloc[0]) - 1
            if gain < 1 or float(pole.high.iloc[-5:].max()) < pole_high * .98:
                continue
            if float(flag.high.max()) > pole_high * 1.05:
                continue
            depth = 1 - float(flag.low.min()) / pole_high
            if not .10 <= depth <= .25:
                continue
            close = float(d.close.iloc[-1])
            pivot = float(flag.high.max())
            baseline = float(d.volume.iloc[-21:-1].mean())
            rvol = float(d.volume.iloc[-1]) / baseline if baseline > 0 else 0
            dry = flag.volume.mean() <= pole.volume.mean() * .8
            setup = dry and .9 * pivot <= close <= pivot
            triggered = close > pivot and rvol >= 1.25
            if setup or triggered:
                return dict(passed=True, state="Breakout" if triggered else "Flag forming",
                            pole_gain=round(gain*100, 2), flag_days=flag_n,
                            depth=round(depth*100, 2), pivot=round(pivot, 2))
    return dict(passed=False, state="No valid pole + flag")


def technical(frame, parent):
    d = frame.rename(columns=str.lower).copy().sort_index()
    p = d.close.shift(1)
    tr = pd.concat([d.high-d.low, (d.high-p).abs(), (d.low-p).abs()], axis=1).max(axis=1)
    # Wilder ATR, same initialization as the standalone Kell engine.
    atr = pd.Series(np.nan, index=d.index)
    if len(d) >= 14:
        atr.iloc[13] = tr.iloc[:14].mean()
        for i in range(14, len(d)):
            atr.iloc[i] = (atr.iloc[i-1]*13+tr.iloc[i])/14
    last = d.iloc[-1]
    e10 = d.close.ewm(span=10, adjust=False).mean()
    e20 = d.close.ewm(span=20, adjust=False).mean()
    mas = {n: d.close.rolling(n).mean() for n in (20, 50, 100, 200)}
    prior_vol = float(d.volume.iloc[-21:-1].mean())
    vratio = float(last.volume / prior_vol) if prior_vol > 0 else 0
    a = float(atr.iloc[-1])
    records = [dict(t=str(t.date()), o=float(r.open), h=float(r.high), l=float(r.low),
                    c=float(r.close), v=int(r.volume)) for t, r in d.iterrows()]
    ep = ep_metrics(records, parent)
    latest, _ = kell_classify(d)
    high20 = float(d.high.tail(20).max())
    low20 = float(d.low.tail(20).min())
    position20 = (last.close-low20)/(high20-low20)*100 if high20>low20 else None
    high63 = float(d.high.tail(63).max())
    high252 = float(d.high.tail(252).max()) if len(d) >= 252 else None
    high5, low5 = float(d.high.tail(5).max()), float(d.low.tail(5).min())
    prior_range = float(tr.iloc[-25:-5].mean())
    contraction = float(tr.tail(5).mean()/prior_range) if prior_range > 0 else None
    volume_dry = float(d.volume.tail(5).mean()/d.volume.iloc[-25:-5].mean()) if d.volume.iloc[-25:-5].mean()>0 else None
    stack = (len(d)>=200 and last.close>=e10.iloc[-1]>=mas[20].iloc[-1]>=
             mas[50].iloc[-1]>=mas[100].iloc[-1]>=mas[200].iloc[-1])
    row = dict(symbol=parent["symbol"], name=parent.get("name", parent["symbol"]),
               date=str(d.index[-1].date()), close=safe(last.close), change_pct=safe(ep["change_pct"]),
               gap_pct=safe(ep["gap_pct"]), rvol=safe(vratio), volume=int(last.volume),
               market_cap_cr=safe(parent["market_cap_cr"]), avg_vol_20d=safe(parent["avg_vol_20d"]),
               avg_rvol_20d_cr=safe(parent["avg_rvol_20d_cr"]),
               avg_range_pct_20d=safe(parent["avg_range_pct_20d"]),
               atr_extension=safe((last.close-mas[50].iloc[-1])/a) if a>0 else None,
               atr_pct=safe(a/last.close*100),
               phase=latest["phase"], phase_name=PHASE_NAMES[latest["phase"]],
               kell_signal=latest["signal"], kell_reasons=latest["reasons"],
               close_position_pct=ep["close_position_pct"], neglect_score=ep["neglect_score"],
               neglect_pass=ep["neglect_pass"], catalyst="Unverified",
               fundamental_status="Unknown", fundamentals_date=None,
               eps_growth=None, sales_growth=None, warnings=ep["warnings"],
               spark=[safe(v,2) for v in d.close.tail(45)], gates={},
               _stack=bool(stack) if len(d)>=200 else None, _position20=safe(position20), _high252=safe(high252),
               _above50=bool(len(d)>=50 and last.close>=mas[50].iloc[-1]),
               _launch_trend=bool(len(d)>=53 and last.close>e20.iloc[-1] and e10.iloc[-1]>=e20.iloc[-1]
                                 and e20.iloc[-1]>e20.iloc[-4] and last.close>=mas[50].iloc[-1]),
               _width5=safe((high5-low5)/last.close*100), _contraction=safe(contraction),
               _dry=safe(volume_dry),
               _support=bool(a>0 and min(abs(last.close-e10.iloc[-1]), abs(last.close-e20.iloc[-1]))<=a),
               _nearhigh=bool(last.close>=high63*.9), _htf=htf_geometry(d))
    row["history_sessions"]=len(d)
    if len(d)<200:
        row["warnings"].append(f"Only {len(d)} completed sessions: long-lookback scans remain unavailable; daily move and volume scans can still qualify.")
    for name, n in (("day",1),("week",5),("month",21),("3m",63),("6m",126)):
        row[f"return_{name}"] = safe((last.close/d.close.iloc[-n-1]-1)*100) if len(d)>n else None
    return row, records, latest["events"]


def add_ranks(rows):
    frame = pd.DataFrame(rows)
    for name in ("day", "week", "month", "3m", "6m"):
        # Inclusive percentile, symmetric for ties. A one-stock universe has no useful RS.
        series = frame[f"return_{name}"]
        rank = series.rank(method="average", pct=True)*100 if series.notna().sum()>1 else series*np.nan
        for i, row in enumerate(rows):
            row[f"rs_{name}"] = safe(rank.iloc[i], 2)
    rank = frame.atr_pct.rank(method="average", pct=True)*100 if len(frame)>1 else frame.atr_pct*np.nan
    for i, row in enumerate(rows):
        row["atr_rank"] = safe(rank.iloc[i],2)


def assess(row, fundamentals, market_up):
    r = row
    qrank = max([r.get("rs_"+p) or 0 for p in ("week","month","3m","6m")])
    qg = [gate("RS ≥97 on 1W/1M/3M/6M", qrank>=97, qrank),
          gate("Bullish 10/20/50/100/200 MA stack", r["_stack"], r["_stack"]),
          gate("ATR% percentile ≥50 (proxy)", (r.get("atr_rank") or 0)>=50, r.get("atr_rank")),
          gate("20-session range position ≥50%", (r["_position20"] or 0)>=50, r["_position20"])]
    india_ep = [gate("Opening gap >3%", r["gap_pct"]>3, r["gap_pct"]),
                gate("RVOL >3× previous 20 sessions", r["rvol"]>3, r["rvol"]),
                gate("Close in upper 35% of range", (r["close_position_pct"] or 0)>=65, r["close_position_pct"]),
                gate("Positive day and holds opening gap", r["change_pct"]>0 and r.get("_close_above_open",True), r["change_pct"]),
                gate("Pre-event neglect", r["neglect_pass"], r["neglect_score"])]
    # close >= open is equivalent to close return >= opening gap when both use prior close.
    india_ep[3] = gate("Positive day; close ≥open", r["change_pct"]>0 and r["change_pct"]>=r["gap_pct"]-1e-7, r["change_pct"])
    original_ep = [*india_ep]
    original_ep[0] = gate("Original opening gap ≥10%", r["gap_pct"]>=10, r["gap_pct"])
    kg = [gate("Fresh WP / CB / BB today", r["kell_signal"] in ("WP","CB","BB"), r["kell_signal"] or "None"),
          gate("Cycle phase", True, r["phase_name"])]
    sg = [gate("Daily close-to-close move ≥4%", r["change_pct"]>=4, r["change_pct"]),
          gate("Above previous 20-session mean volume", r["rvol"]>1, r["rvol"])]
    s8 = [gate("Daily share volume ≥8 million", r["volume"]>=8_000_000, r["volume"]),
          gate("RVOL ≥1.25×", r["rvol"]>=1.25, r["rvol"]),
          gate("Positive close-to-close day", r["change_pct"]>0, r["change_pct"])]
    cg = [gate(f"{label} RS percentile ≥97", (r.get("rs_"+key) or 0)>=97, r.get("rs_"+key))
          for label,key in (("Daily","day"),("Weekly","week"),("Monthly","month"))]
    lg = [gate("Rising EMA structure / SMA50 support",r["_launch_trend"],r["_launch_trend"]),
          gate("3M RS percentile ≥80",(r.get("rs_3m") or 0)>=80,r.get("rs_3m")),
          gate("Five-session range ≤10%",r["_width5"] is not None and r["_width5"]<=10,r["_width5"]),
          gate("Range contraction ≤0.80",r["_contraction"] is not None and r["_contraction"]<=.8,r["_contraction"]),
          gate("Volume dry-up ≤0.75",r["_dry"] is not None and r["_dry"]<=.75,r["_dry"]),
          gate("Within 1 ATR of EMA10 or EMA20",r["_support"],r["_support"]),
          gate("Within 10% of 63-session high",r["_nearhigh"],r["_nearhigh"])]
    hg = [gate("Ordered doubling + 3–5 week flag",r["_htf"]["passed"],r["_htf"]["state"])]
    f = fundamentals or {}
    r["fundamentals_status"] = f.get("status","Unknown / not retrieved")
    r["fundamentals_date"] = f.get("retrieved_at")
    r["eps_growth"] = f.get("eps_growth")
    r["sales_growth"] = f.get("sales_growth")
    r["htf_detail"] = r["_htf"]
    def check(key, threshold):
        value=f.get(key)
        return None if value is None else value>=threshold
    can = [
        gate("C: quarterly EPS growth ≥25% YoY",check("eps_growth",25),f.get("eps_growth","Unknown")),
        gate("C: quarterly sales growth ≥25% YoY",check("sales_growth",25),f.get("sales_growth","Unknown")),
        gate("A: 3 consecutive annual EPS growth rates ≥25%",f.get("annual_pass"),f.get("annual_growth","Unknown")),
        gate("A: ROE ≥17%",check("roe",17),f.get("roe","Unknown")),
        gate("N proxy: within 5% of 252-session high",None if r["_high252"] is None else r["close"]>=.95*r["_high252"],r["_high252"]),
        gate("S proxy: RVOL ≥1.25",r["rvol"]>=1.25,r["rvol"]),
        gate("L proxy: 3M RS ≥80 and close ≥SMA50",(r.get("rs_3m") or 0)>=80 and r["_above50"],r.get("rs_3m")),
        gate("I proxy: reported institutional ownership >0",None if f.get("institutional_pct") is None else f["institutional_pct"]>0,f.get("institutional_pct","Unknown")),
        gate("M proxy: MidSmallcap 400 above rising SMA50",market_up,"Unknown" if market_up is None else market_up),
    ]
    r["gates"] = dict(q_breakout=qg,q_ep=india_ep,q_ep_original=original_ep,kell=kg,
                      sb4=sg,sb8=s8,canslim=can,club97=cg,launchpad=lg,htf=hg)
    r["matches"] = [key for key in ("q_breakout","q_ep","kell","sb4","sb8","canslim","club97","launchpad","htf")
                    if all(g["passed"] is True for g in r["gates"][key])]
    r["matches_original"] = [key for key in r["matches"] if key!="q_ep"]
    if all(g["passed"] is True for g in original_ep):
        r["matches_original"].append("q_ep")
    r["canslim_state"] = "Quantitative pass" if "canslim" in r["matches"] else "Fail" if any(g["passed"] is False for g in can) else "Unknown"
    for key in list(r):
        if key.startswith("_"):
            del r[key]
    return r

"""Transparent EOD proxies, not proprietary Stockbee rules or proven signals."""
import math
from statistics import mean

CONFIG={"gap_pct":3.0,"rvol":3.0,"close_position_pct":65.0,
        "neglect_score":60,"mover_pct":4.0,"volume_window":20,
        "neglect_sessions":60}


def pct(a,b):
    return (a/b-1)*100 if b else None


def rounded(value,digits=4):
    return round(value,digits) if value is not None and math.isfinite(value) else None


def metrics(bars,parent):
    if len(bars)<21:
        raise ValueError("At least 21 daily bars required")
    last,prev=bars[-1],bars[-2]
    if not all(last.get(k) is not None for k in ("o","h","l","c","v")):
        raise ValueError("Missing OHLCV")
    if min(last["o"],last["l"],last["c"],prev["c"])<=0 or last["h"]<max(last["o"],last["c"],last["l"]) or last["l"]>min(last["o"],last["c"]) or last["v"]<0:
        raise ValueError("Invalid prices")
    avg=mean(b["v"] for b in bars[-21:-1])
    if avg<=0: raise ValueError("No valid prior volume")
    gap=rounded(pct(last["o"],prev["c"]),8)
    change=pct(last["c"],prev["c"])
    position=rounded((last["c"]-last["l"])/(last["h"]-last["l"])*100,8) if last["h"]>last["l"] else None
    rvol=rounded(last["v"]/avg,8)
    prior=bars[:-1]
    ret20=pct(prev["c"],prior[-21]["c"]) if len(prior)>=21 else None
    ret60=pct(prev["c"],prior[-61]["c"]) if len(prior)>=61 else None
    volume_contraction=avg/mean(b["v"] for b in prior[-60:-20]) if len(prior)>=60 and mean(b["v"] for b in prior[-60:-20])>0 else None
    # Every neglect input excludes the event day. Coverage/ownership is unknown.
    score=0
    reasons=[]
    available=ret60 is not None and volume_contraction is not None
    if available:
        points=30 if ret20<=5 else 20 if ret20<=10 else 0
        score+=points
        reasons.append({"test":"No pre-event 20-session run-up","value":rounded(ret20),"points":points,"max_points":30})
        points=25 if ret60<=10 else 15 if ret60<=20 else 0
        score+=points
        reasons.append({"test":"Flat/weak prior 60-session performance","value":rounded(ret60),"points":points,"max_points":25})
        points=25 if volume_contraction<=.7 else 15 if volume_contraction<=1 else 0
        score+=points
        reasons.append({"test":"Prior 20-session volume / preceding 40 sessions","value":rounded(volume_contraction),"points":points,"max_points":25})
        previous_bursts=0
        for i in range(max(21,len(prior)-60),len(prior)):
            p=prior[i];base=mean(b["v"] for b in prior[i-20:i])
            if pct(p["c"],prior[i-1]["c"])>=10 and base>0 and p["v"]/base>3:
                previous_bursts+=1
        points=20 if previous_bursts==0 else 0
        score+=points
        reasons.append({"test":"No earlier +10% / >3x-volume burst in 60 sessions","value":previous_bursts,"points":points,"max_points":20})
    neglected=available and score>=CONFIG["neglect_score"] and ret20<=10
    gates={"gap":gap>CONFIG["gap_pct"],"rvol":rvol>CONFIG["rvol"],
           "close_position":position is not None and position>=CONFIG["close_position_pct"],
           "positive_session":change>0 and last["c"]>=last["o"],"neglect":neglected}
    technical=all(gates[k] for k in ("gap","rvol","close_position","positive_session"))
    strict=technical and neglected
    volume_led=(not gates["gap"]) and gates["rvol"] and gates["close_position"] and gates["positive_session"] and neglected and change>=CONFIG["mover_pct"]
    warnings=[]
    if position is None: warnings.append("One-price / zero-range bar: close-position undefined, strict EP excluded")
    if any(abs(change-x)<.15 for x in (5,10,20)): warnings.append("Circuit-like percentage move; actual price band and exit liquidity require verification")
    if rvol>50: warnings.append("Extreme RVOL: check bulk/block trades, corporate actions and data quality")
    if available and ret60<-35: warnings.append("Deep prior drawdown: neglect may be distress, not a healthy base")
    if not available: warnings.append("Insufficient pre-event history for a complete neglect assessment")
    if parent["close"] and abs(last["c"]/parent["close"]-1)>.03:
        warnings.append("Adjusted chart close differs from the raw input close")
    return {**{k:parent.get(k) for k in ("symbol","market_cap_cr","avg_vol_20d","avg_rvol_20d_cr","avg_range_pct_20d","rs_pct","rs_excess_pct")},
            "date":last["t"],"close":parent["close"],"open":last["o"],"high":last["h"],"low":last["l"],
            "volume":last["v"],"prior_avg_vol20":rounded(avg),"gap_pct":rounded(gap),
            "change_pct":rounded(change),"rvol":rounded(rvol),"close_position_pct":rounded(position),
            "neglect_score":score if available else None,"neglect_available":available,
            "return20_prior":rounded(ret20),"return60_prior":rounded(ret60),
            "volume_contraction":rounded(volume_contraction),"neglect_reasons":reasons,
            "neglect_pass":neglected,"gates":gates,"technical_pass":technical,"ep_candidate":strict,
            "volume_led":volume_led,"mover":change>=CONFIG["mover_pct"],"warnings":warnings,
            "setup_score":round(min(max(gap,0)/6,1)*20+min(rvol/10,1)*25+(position or 0)*.25+score*.30)}

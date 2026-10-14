import copy
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"pipeline"))
from rules import technical, assess, add_ranks, htf_geometry, SCAN_DEFINITIONS
from market_data import liquidity


def frame(n=270):
    close=np.linspace(70,100,n)
    return pd.DataFrame(dict(open=close-.3,high=close+2,low=close-2,close=close,
                             volume=np.full(n,100000.)),index=pd.bdate_range("2025-01-01",periods=n))


def parent():
    return dict(symbol="TEST",name="Test Ltd",close=100,market_cap_cr=1000,
                avg_vol_20d=100000,avg_rvol_20d_cr=5,avg_range_pct_20d=4)


class RulesTest(unittest.TestCase):
    def test_nine_unique_scans_with_sources(self):
        self.assertEqual(len(SCAN_DEFINITIONS),9)
        self.assertEqual(len({s["id"] for s in SCAN_DEFINITIONS}),9)
        self.assertTrue(all(s["rules"] and all(x["url"].startswith("https://") for x in s["sources"]) for s in SCAN_DEFINITIONS))

    def test_volume_baseline_excludes_signal_day(self):
        d=frame()
        d.loc[d.index[-1],"volume"]=500000
        r,_,_=technical(d,parent())
        self.assertEqual(r["rvol"],5)

    def test_stockbee_four_percent_boundary(self):
        d=frame()
        previous=float(d.close.iloc[-2])
        d.loc[d.index[-1],["open","high","low","close","volume"]]=[previous,previous*1.06,previous*.99,previous*1.04,200000]
        r,_,_=technical(d,parent())
        add_ranks([r])
        assess(r,{},True)
        self.assertIn("sb4",r["matches"])

    def test_no_four_percent_on_average_volume(self):
        d=frame()
        p=float(d.close.iloc[-2])
        d.loc[d.index[-1],["high","close"]]=[p*1.06,p*1.05]
        r,_,_=technical(d,parent());add_ranks([r]);assess(r,{},True)
        self.assertNotIn("sb4",r["matches"])

    def test_eight_million_in_shares_not_rupees(self):
        d=frame()
        d.loc[d.index[-1],"volume"]=8_000_000
        r,_,_=technical(d,parent());add_ranks([r]);assess(r,{},True)
        self.assertIn("sb8",r["matches"])
        self.assertEqual(r["catalyst"],"Unverified")

    def test_missing_fundamentals_cannot_pass_canslim(self):
        r,_,_=technical(frame(),parent())
        add_ranks([r]);assess(r,{},True)
        self.assertNotIn("canslim",r["matches"])
        self.assertTrue(any(g["passed"] is None for g in r["gates"]["canslim"]))

    def test_97_club_requires_all_three_horizons(self):
        r,_,_=technical(frame(),parent());add_ranks([r])
        r.update(rs_day=99,rs_week=99,rs_month=96)
        assess(r,{},True)
        self.assertNotIn("club97",r["matches"])
        r,_,_=technical(frame(),parent());add_ranks([r])
        r.update(rs_day=97,rs_week=97,rs_month=97)
        assess(r,{},True)
        self.assertIn("club97",r["matches"])

    def test_short_history_does_not_invent_rs(self):
        d=frame(100);r,_,_=technical(d,parent());add_ranks([r])
        self.assertIsNone(r["rs_6m"])
        self.assertIsNone(r["rs_day"])

    def test_ranks_use_all_rows_and_handle_ties(self):
        rows=[dict(atr_pct=i+1,**{f"return_{k}":i for k in ("day","week","month","3m","6m")}) for i in range(100)]
        add_ranks(rows)
        self.assertEqual(rows[-1]["rs_day"],100)
        self.assertEqual(rows[-4]["rs_day"],97)
        self.assertEqual(rows[0]["rs_day"],1)

    def test_htf_does_not_treat_one_sharp_day_as_flag(self):
        d=frame()
        d.loc[d.index[-1],["open","high","low","close"]]=[100,205,100,200]
        self.assertFalse(htf_geometry(d)["passed"])

    def test_htf_uses_separate_ordered_pole_and_flag(self):
        d=frame(100)
        prices=np.concatenate([np.full(44,40.),np.linspace(40,100,40),np.full(15,90.),[91.]])
        d["close"]=prices;d["open"]=prices;d["high"]=prices+1;d["low"]=prices-1
        d.loc[d.index[-16:-1],"volume"]=50000
        result=htf_geometry(d)
        self.assertTrue(result["passed"])
        self.assertEqual(result["state"],"Flag forming")
        self.assertGreaterEqual(result["pole_gain"],100)

    def test_actual_range_not_gap_true_range_for_universe(self):
        d=frame(30)
        d["close"]=np.where(np.arange(30)%2==0,100.,110.)
        d["open"]=d["close"];d["high"]=d["close"]+.2;d["low"]=d["close"]-.2
        d["volume"]=1_000_000
        values,passed=liquidity(d)
        self.assertLess(values["avg_range_pct_20d"],1)
        self.assertFalse(passed)

    def test_no_duplicate_scan_ids_in_overlap(self):
        r,_,_=technical(frame(),parent());add_ranks([r]);assess(r,{},True)
        self.assertEqual(len(r["matches"]),len(set(r["matches"])))

    def test_original_ep_gap_is_not_india_threshold(self):
        r,_,_=technical(frame(),parent());add_ranks([r])
        r.update(gap_pct=5,change_pct=8,rvol=4,close_position_pct=90,neglect_pass=True,neglect_score=90)
        assess(r,{},True)
        self.assertIn("q_ep",r["matches"])
        self.assertNotIn("q_ep",r["matches_original"])


if __name__=="__main__":
    unittest.main()

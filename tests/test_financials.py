import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"pipeline"))
from fundamentals import read_one
from rules import technical, add_ranks, assess
from test_rules import frame,parent


class Statements:
    quarterly_income_stmt = pd.DataFrame(
        [[4,3.5,3,2.5,2],[1000,900,800,700,500]],
        index=["Diluted EPS","Total Revenue"],
        columns=pd.to_datetime(["2026-06-30","2026-03-31","2025-12-31","2025-09-30","2025-06-30"]))
    income_stmt = pd.DataFrame(
        [[8,6,4,2]],index=["Diluted EPS"],
        columns=pd.to_datetime(["2026-03-31","2025-03-31","2024-03-31","2023-03-31"]))
    def get_info(self):
        return dict(returnOnEquity=.2,heldPercentInstitutions=.1)


class FundamentalTest(unittest.TestCase):
    @patch("fundamentals.yf.Ticker",return_value=Statements())
    def test_positive_year_over_year_and_annual_checks(self,_):
        symbol,data=read_one("TEST",pd.Timestamp("2026-10-14"))
        self.assertEqual(symbol,"TEST")
        self.assertEqual(data["eps_growth"],100)
        self.assertEqual(data["sales_growth"],100)
        self.assertTrue(data["annual_pass"])
        self.assertEqual(data["roe"],20)
        self.assertEqual(data["institutional_pct"],10)

    @patch("fundamentals.yf.Ticker",return_value=Statements())
    def test_stale_statements_do_not_pass(self,_):
        _,data=read_one("TEST",pd.Timestamp("2027-10-14"))
        self.assertIsNone(data["eps_growth"])
        self.assertIsNone(data["sales_growth"])
        self.assertIsNone(data["annual_pass"])

    @patch("fundamentals.yf.Ticker",return_value=Statements())
    def test_complete_quantitative_canslim_can_pass(self,_):
        _,data=read_one("TEST",pd.Timestamp("2026-10-14"))
        r,_,_=technical(frame(),parent());add_ranks([r])
        r.update(rs_3m=95,rvol=2,_high252=r["close"],_above50=True)
        assess(r,data,True)
        self.assertIn("canslim",r["matches"])
        self.assertTrue(all(g["passed"] is True for g in r["gates"]["canslim"]))

    @patch("fundamentals.yf.Ticker",return_value=Statements())
    def test_defensive_market_blocks_canslim(self,_):
        _,data=read_one("TEST",pd.Timestamp("2026-10-14"))
        r,_,_=technical(frame(),parent());add_ranks([r])
        r.update(rs_3m=95,rvol=2,_high252=r["close"],_above50=True)
        assess(r,data,False)
        self.assertNotIn("canslim",r["matches"])

    @patch("fundamentals.yf.Ticker",side_effect=RuntimeError("Provider outage"))
    def test_provider_outage_remains_unknown(self,_):
        _,data=read_one("TEST",pd.Timestamp("2026-10-14"))
        self.assertIsNone(data["eps_growth"])
        self.assertIsNone(data["annual_pass"])
        self.assertIn("Unknown",data["status"])


if __name__=="__main__":
    unittest.main()

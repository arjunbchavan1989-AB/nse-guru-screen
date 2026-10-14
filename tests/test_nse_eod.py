import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"pipeline"))
from nse_eod import parse,overlay,OfficialBars

CSV=b"SYMBOL,SERIES,DATE1,OPEN_PRICE,HIGH_PRICE,LOW_PRICE,CLOSE_PRICE,PREV_CLOSE,TTL_TRD_QNTY\nTEST,EQ,14-Oct-2026,100,110,98,108,99,8000000\n"


class OfficialEodTest(unittest.TestCase):
    def test_dated_official_csv(self):
        f=parse(CSV,pd.Timestamp("2026-10-14"))
        self.assertEqual(f.loc["TEST","Close"],108)
        self.assertEqual(f.loc["TEST","Volume"],8_000_000)

    def test_redirected_date_rejected(self):
        with self.assertRaises(ValueError):
            parse(CSV,pd.Timestamp("2026-10-13"))

    def test_append_to_prior_session_history(self):
        d=pd.DataFrame(dict(Open=[98.],High=[101.],Low=[97.],Close=[99.],Volume=[100000.]),index=pd.to_datetime(["2026-10-13"]))
        official={pd.Timestamp("2026-10-14"):parse(CSV,pd.Timestamp("2026-10-14")),
                  pd.Timestamp("2026-10-13"):pd.DataFrame()}
        out=overlay(d,"TEST",pd.Timestamp("2026-10-14"),official)
        self.assertEqual(len(out),2)
        self.assertEqual(out.Close.iloc[-1],108)

    def test_do_not_jump_old_unverified_history_gap(self):
        d=pd.DataFrame(dict(Open=[98.],High=[101.],Low=[97.],Close=[99.],Volume=[100000.]),index=pd.to_datetime(["2026-09-01"]))
        official={pd.Timestamp("2026-10-14"):parse(CSV,pd.Timestamp("2026-10-14"))}
        out=overlay(d,"TEST",pd.Timestamp("2026-10-14"),official)
        self.assertEqual(len(out),1)

    def test_udiff_column_mapping(self):
        csv=b"TckrSymb,SctySrs,TradDt,OpnPric,HghPric,LwPric,ClsPric,PrvsClsgPric,TtlTradgVol\nTEST,EQ,2026-10-14,100,110,98,108,99,8000000\n"
        f=parse(csv,pd.Timestamp("2026-10-14"),udiff=True)
        self.assertEqual(f.loc["TEST","Close"],108)

    def test_known_missing_session_is_not_skipped(self):
        d=pd.DataFrame(dict(Open=[98.],High=[101.],Low=[97.],Close=[99.],Volume=[100000.]),index=pd.to_datetime(["2026-10-12"]))
        official=OfficialBars({pd.Timestamp("2026-10-14"):parse(CSV,pd.Timestamp("2026-10-14"))},
                              list(pd.to_datetime(["2026-10-12","2026-10-13","2026-10-14"])))
        self.assertEqual(len(overlay(d,"TEST",pd.Timestamp("2026-10-14"),official)),1)

    def test_latest_bar_can_extend_known_previous_session(self):
        d=pd.DataFrame(dict(Open=[98.],High=[101.],Low=[97.],Close=[99.],Volume=[100000.]),index=pd.to_datetime(["2026-10-13"]))
        official=OfficialBars({pd.Timestamp("2026-10-14"):parse(CSV,pd.Timestamp("2026-10-14"))},
                              list(pd.to_datetime(["2026-10-13","2026-10-14"])))
        self.assertEqual(len(overlay(d,"TEST",pd.Timestamp("2026-10-14"),official)),2)


if __name__=="__main__":
    unittest.main()

# Guru Screen | Indian Momentum Desk

A public-method screening dashboard for liquid NSE equities. Nine scans, a dedicated multi-scan overlap column, a match matrix, stock-level rule explanations and one-click TradingView symbol copying.

## Public dashboard and automation

- Dashboard: https://arjunbchavan1989-ab.github.io/nse-guru-screen/
- Workflow: https://github.com/arjunbchavan1989-AB/nse-guru-screen/actions/workflows/daily-update.yml
- Schedule: `0 14 * * *`, every calendar day at 7:30 PM IST.
- Scheduled runs acquire data; code pushes rebuild the frontend without re-downloading prices.
- Run the workflow manually with `refresh_data=true` for a complete refresh, or `false` for a UI-only deployment.
- GitHub schedules are best-effort and may start late. On non-trading days the last verified exchange session remains visible.
- Coverage, source mode and timestamps are shown in **Data & automation**. Failed validation prevents replacing the last good output.

## Universe

Official NSE EQ-series equities, using strict greater-than comparisons:

- Market capitalisation > ₹500 crore.
- Mean daily share volume over 20 completed sessions >70,000.
- Mean of daily `close × volume` over 20 completed sessions >₹3 crore.
- ADR20 >3%, defined here as the mean of `100 × (high − low) / previous close`.

ADR deliberately measures the daily high-low range, not gap-inclusive true range. This can differ from older dashboards that used true range under the same label. Stocks need at least 100 completed bars to enter this technical dashboard; individual scans may need 200 or 252. Insufficient lookbacks remain unknown.

## Scan methodology and sources

All operational definitions are in `pipeline/rules.py`, embedded in the snapshot, and visible in the dashboard.

- **Qullamaggie Breakout:** Jacobs' explicit MA-stack / multi-horizon RS / 20-day range-position scan. ATR%-percentile is an explicitly labelled proxy for his unspecified ATR RS: https://x.com/SteveDJacobs/status/1971976586355220541
- **Qullamaggie EP:** original gap threshold is 10%; the default India adaptation uses >3%. RVOL, close-position and neglect thresholds are stated engineering choices. Technical candidates do not confirm news or an earnings surprise: https://qullamaggie.com/my-3-timeless-setups-that-have-made-me-tens-of-millions/
- **Oliver Kell:** deterministic approximation of Wedge Pop / EMA Crossback / Base 'n Break, not proprietary Kell code. Only fresh bullish events count as scan matches: https://traderlion.com/technical-analysis/chart-patterns/cycle-of-price-action-by-oliver-kell/
- **Stockbee 4%:** close-to-close ≥4% with share volume above the preceding 20-session mean: https://stockbee.blogspot.com/2017/09/how-to-use-4-and-breakout-scans.html
- **Stockbee 8M EP hunt:** user-requested 8-million-share up-day filter with RVOL ≥1.25; Jacobs' published version uses 9 million. This is an EP discovery list, not a verified EP: https://x.com/SteveDJacobs/status/1931686377663475773
- **CAN SLIM:** EPS and sales growth, three annual growth checks, ROE and disclosed N/S/L/I/M quantitative proxies. Unknown financials never pass. Not a replacement for discretionary company and market analysis: https://myibd.investors.com/welcome/ and https://www.investors.com/ibd-university/can-slim/quarterly-earnings/
- **97 Club:** ≥97 cross-sectional percentile on each of day / week / month, calculated across the eligible universe before any guru filter: https://x.com/SteveDJacobs/status/1973670043725529454
- **TraderLion Launchpad:** disclosed numerical approximation of tightness, low volume and moving-average support: https://traderlion.com/technical-analysis/finding-your-trading-edge/
- **TraderLion HTF:** separate 20–40-session doubling pole followed by a 15–25-session flag, 10–25% depth; geometric candidate or volume-backed breakout: https://traderlion.com/technical-analysis/high-tight-flag-pattern/
- **Dashboard reference:** occurrence-ranked Guru Scans: https://x.com/SteveDJacobs/status/2109436930198773904

## Relative strength

RS percentiles are computed within the full eligible NSE universe, not within scan results and not across the entire exchange. The 97 Club uses 1/5/21-session returns. Other horizons use 63/126 sessions. Ties use average percentile rank. These are not proprietary IBD ratings. Separate RS excess measures 63-session performance against the exact **Nifty MidSmallcap 400**, aligned by session.

## Data provenance and independence

The scheduled workflow independently acquires:

- Official EQ listing: https://archives.nseindia.com/content/equities/EQUITY_L.csv
- Dated NSE index archives: `https://archives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv`
- Equity OHLCV, shares and financial statements: Yahoo Finance through yfinance.

No production code reads the retired NSE Stage dashboard, the Kell dashboard or the EP dashboard. Code modules were adapted into this repository, not connected as data dependencies.

A one-time local `--bootstrap` import can create an explicitly labelled BYOD preview from existing chart files. It is never used by the GitHub workflow. The frontend rejects a remote bootstrap as a current independent feed and exposes fallback mode visibly. The first successful independent acquisition replaces this initial snapshot.

Prices are vendor OHLCV. Corporate actions, extraordinary volumes and circuits require review. Market cap is current shares × raw close, not a historical point-in-time valuation. Financial statement dates are fiscal period ends rather than original filing timestamps. This is not a backtest engine.

## Freshness and missing data

- Price histories must cover ≥95% of official listings.
- At least 95% of retrieved price histories must match the verified exchange session.
- Shares must cover ≥95% of liquidity-qualified candidates.
- Technical history must cover ≥90% of the market-cap-qualified universe.
- Fundamentals are fetched for stocks that have not already failed the CAN SLIM N/S/L technical gates; complete records refresh weekly and incomplete records daily.
- Quarterly inputs expire after 180 days from period end; annual inputs after 550 days.
- EP catalysts remain **Unverified**. The app does not invent or infer company news.
- Historical sessions hide current price charts instead of mismatching snapshot and chart dates.

## Development

```sh
npm ci
pip install -r pipeline/requirements.txt
python -m unittest discover -s tests -v
npm run check
npm run dev
```

```sh
# Independently acquire and validate a completed EOD snapshot
python pipeline/run.py

# Build GitHub Pages client
npx vite build
```

The app reads the repository's latest validated snapshot with a minute-level cache-busting key and falls back to its bundled dated snapshot if the repository feed is unavailable. Refresh reads published data; it does not trigger an authenticated workflow. No account credentials, brokerage access, trading endpoints, cookies or browser local storage are required.

TradingView copying normalises NSE punctuation to TradingView IDs, for example `BAJAJ-AUTO` becomes `NSE:BAJAJ_AUTO`, while the dashboard retains the actual exchange symbol. The canonical instrument is documented at https://www.tradingview.com/symbols/NSE-BAJAJ_AUTO/.

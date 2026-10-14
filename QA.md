# QA inventory

## Functional checks

- Nine sourced scans and a deduplicated multi-scan column.
- Board and matrix; sidebar scan selection and return to all.
- Search symbols and company names; unmatched search; clear/reset.
- Multi-scan toggle; 2/3/4/5 minimum counts; sorting by count/change/RVOL/RS/symbol.
- Original ≥10% versus India >3% EP gap gate.
- Per-column TradingView copy, matrix copy, one-symbol copy and blocked-clipboard fallback.
- CSV export reflects current filters, mode and session.
- Stock detail chart, same-session validation, rule checks, missing fundamentals, EP catalyst warning, close via button/Escape/backdrop.
- Rules page, all scan selectors, public methodology URLs and matching-stock navigation.
- Data/automation page, schedule, coverage and source details.
- Archived session selection when present; prohibit chart/session mismatch.
- Manual published-snapshot refresh and visible fallback.
- Light/dark toggle; mobile sidebar; board horizontal scroll.
- All calculations use the completed snapshot session; no invented EP catalysts.

## Visual checks

- Desktop 1440×1000, mobile 390×844; no document-level horizontal overflow.
- Light and dark modes.
- Initial board, horizontally scrolled final scans, matrix, rules, health and stock dialog.
- Empty-result state and blocked/missing-data states.
- Readable stage labels and long symbols; accessible keyboard focus.

## Automated coverage

Python regression tests exercise prior-day volume denominators, 4% boundaries,
8-million share units, unknown fundamentals, all-three-horizon 97 Club logic,
cross-sectional ranking, actual range versus gap true range, distinct scan IDs,
India versus original EP thresholds, and non-overlapping HTF pole/flag geometry.

## Executed checks

- 19 Python tests passed, including positive/negative CAN SLIM fixtures, stale statements, defensive market context and provider failure.
- Four TradingView symbol-normalisation tests passed.
- TypeScript type-check passed.
- npm production dependency audit: no reported vulnerabilities.
- Desktop 1440×1000 and mobile 390×844 had no document-level horizontal overflow.
- Light and dark layouts visually reviewed.
- Board, matrix, CAN SLIM methodology, data-health screen and mobile stock dialog visually reviewed.
- Search, no-results/reset, 3+ overlap filtering and return to 2+, sorting and EP-mode round trip passed.
- Include-unmatched toggled from the matched subset to the complete snapshot and back.
- Column clipboard contained all symbols, not just the initially rendered cards.
- Blocked-clipboard fixture exposed a selectable manual fallback.
- CSV download had the dated expected filename.
- Stock chart rendered close/EMA10/EMA20 from the matching snapshot date.
- Escape closed the stock dialog; Tab wrapped within the dialog; background scroll restored.
- Published-snapshot refresh showed its dated result and explicitly did not claim to trigger an authenticated scan.
- Mobile navigation opened and selected the overlap view successfully.
- No browser page errors were observed during these checks.

Archive navigation is implemented; the first production session has no earlier
independent archive to select. The chart intentionally refuses to combine an
archived session with a current-session chart.

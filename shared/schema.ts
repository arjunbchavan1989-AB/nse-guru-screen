export type ScanId = "q_breakout" | "q_ep" | "kell" | "sb4" | "sb8" | "canslim" | "club97" | "launchpad" | "htf";
export type Gate = { label: string; passed: boolean | null; value: string };
export type ScanDefinition = {
  id: ScanId; name: string; short: string; guru: string;
  kind: string; description: string; rules: string[]; sources: { title: string; url: string }[];
};
export type Stock = {
  symbol: string; name: string; date: string; close: number; change_pct: number;
  gap_pct: number; rvol: number; volume: number; market_cap_cr: number;
  avg_vol_20d: number; avg_rvol_20d_cr: number; avg_range_pct_20d: number;
  rs_day: number | null; rs_week: number | null; rs_month: number | null;
  rs_3m: number | null; rs_6m: number | null; rs_excess_pct: number | null;
  atr_extension: number | null; phase: string; phase_name: string;
  matches: ScanId[]; matches_original: ScanId[];
  gates: Record<string, Gate[]>; warnings: string[];
  close_position_pct: number | null; neglect_score: number | null;
  catalyst: string; fundamentals_status: string; fundamentals_date: string | null;
  spark: number[]; eps_growth: number | null; sales_growth: number | null;
};
export type Snapshot = {
  schema_version: number; generated_at: string; last_trading_date: string;
  benchmark: string; qualified_count: number; market_data: Record<string, any>;
  scans: ScanDefinition[]; rows: Stock[]; counts: Record<ScanId, number>;
  multi_count: number; market_regime: string; notes: string[];
  filters: Record<string, number>; refresh_schedule: string;
};

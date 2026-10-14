// TradingView's NSE symbol IDs normalise exchange punctuation to underscores.
// Keep the actual NSE exchange symbol unchanged everywhere else.
export function tradingViewSymbol(symbol: string): string {
  return "NSE:" + symbol.toUpperCase().replace(/[^A-Z0-9_]/g, "_");
}

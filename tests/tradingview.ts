import { strict as assert } from "node:assert";
import { tradingViewSymbol } from "../shared/symbols";
for (const [input, expected] of [
  ["M&M", "NSE:M_M"],
  ["BAJAJ-AUTO", "NSE:BAJAJ_AUTO"],
  ["J&KBANK", "NSE:J_KBANK"],
  ["IDBI", "NSE:IDBI"],
]) {
  assert.equal(tradingViewSymbol(input), expected);
}
console.log("TradingView normalisation: four cases passed.");

// expect: switch-exhaustiveness-check
// expect: error TS2345
import type { Stock } from "./delivery.js";
import { unreachable } from "./unreachable.js";

export function restockDays(stock: Stock): number {
  switch (stock.status) {
    case "in_stock":
      return 0;
    default:
      return unreachable(stock);
  }
}

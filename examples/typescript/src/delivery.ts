import { z } from "zod";

import type { Invalid, Postcode } from "./postcode.js";
import { unreachable } from "./unreachable.js";

// region: stock
const RestockDays = z.int().min(0).max(65535).brand<"RestockDays">();

export const Stock = z.discriminatedUnion("status", [
  z.object({ status: z.literal("in_stock") }),
  z.object({ status: z.literal("backorder"), restock_days: RestockDays }),
]);
export type Stock = z.infer<typeof Stock>;

export function deliveryDate(postcode: Postcode, stock: Stock, today: Date): Date {
  const date = new Date(today);
  date.setUTCDate(date.getUTCDate() + days(postcode, stock));
  return date;
}

function days(postcode: Postcode, stock: Stock): number {
  switch (stock.status) {
    case "in_stock":
      return shippingDays(postcode);
    case "backorder":
      return stock.restock_days + shippingDays(postcode);
    default:
      return unreachable(stock);
  }
}
// endregion

// region: spring
export function stockOf(json: string): Stock | Invalid {
  let data: unknown;
  try {
    data = JSON.parse(json);
  } catch {
    return { invalid: "the warehouse sent no JSON" };
  }
  const parsed = Stock.safeParse(data);
  return parsed.success ? parsed.data : { invalid: parsed.error.message };
}
// endregion

function shippingDays(postcode: Postcode): number {
  return postcode.code.startsWith("1") ? 2 : 3;
}

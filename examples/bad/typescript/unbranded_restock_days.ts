// expect: error TS2322
import type { Stock } from "./delivery.js";

export const backorder: Stock = { status: "backorder", restock_days: -3 };

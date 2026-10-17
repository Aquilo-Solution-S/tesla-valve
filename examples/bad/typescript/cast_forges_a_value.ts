// expect: consistent-type-assertions
import type { Stock } from "./delivery.js";

export function forged(raw: string): Stock {
  return JSON.parse(raw) as Stock;
}

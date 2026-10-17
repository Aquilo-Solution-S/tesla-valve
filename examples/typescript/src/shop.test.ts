import assert from "node:assert/strict";
import { test } from "node:test";

import { deliveryDate, Stock, stockOf } from "./delivery.js";
import { Postcode } from "./postcode.js";

function berlin(): Postcode {
  const postcode = Postcode.parse("10115");
  assert.ok(postcode instanceof Postcode);
  return postcode;
}

test("ordered on Tuesday arrives on Thursday", () => {
  const inStock = Stock.parse({ status: "in_stock" });
  const arrives = deliveryDate(berlin(), inStock, new Date("2026-10-06"));
  assert.deepEqual(arrives, new Date("2026-10-08"));
});

test("a backorder ships once restocked", () => {
  const backorder = Stock.parse({ status: "backorder", restock_days: 5 });
  const arrives = deliveryDate(berlin(), backorder, new Date("2026-10-06"));
  assert.deepEqual(arrives, new Date("2026-10-13"));
});

test("the warehouse spring refuses what it does not know", () => {
  for (const raw of [
    "not json",
    '{"status": "discontinued"}',
    '{"status": "backorder"}',
    '{"status": "backorder", "restock_days": -3}',
    '{"status": "backorder", "restock_days": 70000}',
    '{"status": "backorder", "restock_days": 2.5}',
    '{"status": "backorder", "restock_days": "3"}',
  ]) {
    assert.ok("invalid" in stockOf(raw), `accepted ${raw}`);
  }
});

test("the checkout spring refuses what is not a postcode", () => {
  for (const raw of ["1011", "101155", "1011a", "１０１１５"]) {
    assert.ok(!(Postcode.parse(raw) instanceof Postcode), `accepted ${raw}`);
  }
});

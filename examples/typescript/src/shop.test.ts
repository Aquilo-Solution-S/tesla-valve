import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { z } from "zod";

import { deliveryDate, shippingDays, Stock, stockOf } from "./delivery.js";
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

// `Spec.backorder_not_sooner`
test("a backorder never arrives sooner", () => {
  const today = new Date("2026-10-06");
  const inStock = deliveryDate(berlin(), Stock.parse({ status: "in_stock" }), today);
  for (const restock_days of [0, 1, 30]) {
    const backorder = Stock.parse({ status: "backorder", restock_days });
    assert.ok(deliveryDate(berlin(), backorder, today).getTime() >= inStock.getTime());
  }
});

// `Spec.not_one_promise`
test("a backorder is not promised the date of an item in stock", () => {
  const today = new Date("2026-10-06");
  const inStock = deliveryDate(berlin(), Stock.parse({ status: "in_stock" }), today);
  const backorder = Stock.parse({ status: "backorder", restock_days: 1 });
  assert.notDeepEqual(deliveryDate(berlin(), backorder, today), inStock);
});

// Replay `Spec.deliveryDays` with the inputs encoded by `Spec.stockJson`.
const written: unknown = JSON.parse(
  readFileSync(new URL("../src/delivery_days.json", import.meta.url), "utf8"),
);
const vectors = z.array(z.object({ shipping: z.int(), stock: Stock, days: z.int() })).parse(written);

test("the code decides the days the spec decides", () => {
  const today = new Date("2026-10-06");
  for (const code of ["10115", "20095"]) {
    const postcode = Postcode.parse(code);
    assert.ok(postcode instanceof Postcode);
    const replayed = vectors.filter((vector) => vector.shipping === shippingDays(postcode));
    assert.ok(replayed.length > 0, `no vector ships in the days of ${code}`);
    for (const vector of replayed) {
      const arrives = new Date(today);
      arrives.setUTCDate(arrives.getUTCDate() + vector.days);
      assert.deepEqual(deliveryDate(postcode, vector.stock, today), arrives);
    }
  }
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

//! The delivery date at checkout, the step the manifesto walks through.

use chrono::{Days, NaiveDate};
use serde::Deserialize;

pub mod before;
mod postcode;

pub use postcode::Postcode;

#[derive(Debug)]
pub struct Invalid(pub &'static str);

// region: stock-proofs
/// A backorder carries its restock days, and they fit in a `u16`:
///
/// ```
/// shop::Stock::Backorder { restock_days: 5 };
/// ```
///
/// ```compile_fail
/// shop::Stock::Backorder { restock_days: None };
/// ```
///
/// ```compile_fail
/// shop::Stock::Backorder { restock_days: 70000 };
/// ```
// endregion
// region: stock
#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum Stock {
    InStock,
    Backorder { restock_days: u16 },
}

pub fn delivery_date(postcode: &Postcode, stock: Stock, today: NaiveDate) -> NaiveDate {
    let days = match stock {
        Stock::InStock => shipping_days(postcode),
        Stock::Backorder { restock_days } => u64::from(restock_days) + shipping_days(postcode),
    };
    today + Days::new(days)
}
// endregion

/// The warehouse's JSON, parsed where it enters.
pub fn stock_of(json: &str) -> Result<Stock, serde_json::Error> {
    serde_json::from_str(json)
}

pub fn shipping_days(postcode: &Postcode) -> u64 {
    if postcode.as_str().starts_with('1') { 2 } else { 3 }
}

// region: clock
/// The clock is a spring: read it here, once, and pass the date in.
#[expect(clippy::disallowed_methods, reason = "the one place that reads the clock")]
pub fn today() -> NaiveDate {
    chrono::Local::now().date_naive()
}
// endregion

#[cfg(test)]
mod tests {
    use super::*;

    fn date(year: i32, month: u32, day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(year, month, day).unwrap()
    }

    // region: intent
    #[test]
    fn ordered_on_tuesday_arrives_on_thursday() {
        let tuesday = date(2026, 10, 6);
        let berlin = Postcode::parse("10115").unwrap();
        let arrives = delivery_date(&berlin, Stock::InStock, tuesday);
        assert_eq!(arrives, date(2026, 10, 8));
    }
    // endregion

    #[test]
    fn a_backorder_ships_once_restocked() {
        let berlin = Postcode::parse("10115").unwrap();
        let backorder = Stock::Backorder { restock_days: 5 };
        assert_eq!(delivery_date(&berlin, backorder, date(2026, 10, 6)), date(2026, 10, 13));
    }

    // @holds backorder_not_sooner
    #[test]
    fn a_backorder_never_arrives_sooner() {
        let berlin = Postcode::parse("10115").unwrap();
        let today = date(2026, 10, 6);
        let in_stock = delivery_date(&berlin, Stock::InStock, today);
        for restock_days in [0, 1, 30] {
            assert!(delivery_date(&berlin, Stock::Backorder { restock_days }, today) >= in_stock);
        }
    }

    // @holds not_one_promise
    #[test]
    fn a_backorder_is_not_promised_the_date_of_an_item_in_stock() {
        let berlin = Postcode::parse("10115").unwrap();
        let today = date(2026, 10, 6);
        let backorder = delivery_date(&berlin, Stock::Backorder { restock_days: 1 }, today);
        assert_ne!(backorder, delivery_date(&berlin, Stock::InStock, today));
    }

    #[derive(Deserialize)]
    struct Vector {
        shipping: u64,
        stock: Stock,
        days: u64,
    }

    #[test]
    fn the_code_decides_the_days_the_spec_decides() {
        let today = date(2026, 10, 6);
        for code in ["10115", "20095"] {
            let postcode = Postcode::parse(code).unwrap();
            // @holds Vectors: `lake exe vectors`, in examples/lean, writes this file.
            let vectors: Vec<Vector> = serde_json::from_str(include_str!("delivery_days.json")).unwrap();
            let mut replayed = 0;
            for vector in vectors.into_iter().filter(|vector| vector.shipping == shipping_days(&postcode)) {
                assert_eq!(delivery_date(&postcode, vector.stock, today), today + Days::new(vector.days));
                replayed += 1;
            }
            assert!(replayed > 0, "no vector ships in the days of {code}");
        }
    }

    #[test]
    fn the_warehouse_spring_refuses_what_it_does_not_know() {
        for json in [
            r#"{"status":"discontinued"}"#,
            r#"{"status":"backorder"}"#,
            r#"{"status":"backorder","restock_days":-3}"#,
            r#"{"status":"backorder","restock_days":70000}"#,
        ] {
            assert!(stock_of(json).is_err(), "accepted {json}");
        }
    }

    #[test]
    fn the_checkout_spring_refuses_what_is_not_a_postcode() {
        for raw in ["1011", "101155", "1011a", "１０１１５"] {
            assert!(Postcode::parse(raw).is_err(), "accepted {raw}");
        }
        assert!(serde_json::from_str::<Postcode>(r#""hello""#).is_err());
    }
}

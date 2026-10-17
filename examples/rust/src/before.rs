//! The loose version the manifesto starts from. Nothing calls it.

use chrono::{Days, NaiveDate};

use crate::{Postcode, shipping_days};

// region: before
pub struct WarehouseStock {
    status: String,
    restock_days: Option<u64>,
}

pub fn delivery_date(postcode: &Postcode, stock: &WarehouseStock, today: NaiveDate) -> NaiveDate {
    let days = match stock.status.as_str() {
        "in_stock" => shipping_days(postcode),
        "backorder" => match stock.restock_days {
            Some(restock_days) => restock_days + shipping_days(postcode),
            None => panic!("backorder without restock days"),
        },
        other => panic!("unknown stock status: {other}"),
    };
    today + Days::new(days)
}
// endregion

// expect: E0308
use crate::Stock;

pub fn backorder() -> Stock {
    Stock::Backorder { restock_days: None }
}

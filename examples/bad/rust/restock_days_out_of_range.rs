// expect: overflowing_literals
use crate::Stock;

pub fn backorder() -> Stock {
    Stock::Backorder { restock_days: 70000 }
}

// expect: E0004
use crate::Stock;

pub fn restock_days(stock: Stock) -> u16 {
    match stock {
        Stock::Backorder { restock_days } => restock_days,
    }
}

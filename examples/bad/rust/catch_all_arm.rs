// expect: match_wildcard_for_single_variants
use crate::Stock;

pub fn restock_days(stock: Stock) -> u16 {
    match stock {
        Stock::Backorder { restock_days } => restock_days,
        _ => 0,
    }
}

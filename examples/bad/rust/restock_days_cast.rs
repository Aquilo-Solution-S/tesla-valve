// expect: cast_possible_truncation
pub fn backorder(raw: u64) -> crate::Stock {
    crate::Stock::Backorder { restock_days: raw as u16 }
}

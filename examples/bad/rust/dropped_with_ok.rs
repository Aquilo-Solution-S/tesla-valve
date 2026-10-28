// expect: unused_result_ok
pub struct SoldOut;

pub fn reserve(stock: &mut u16) -> Result<(), SoldOut> {
    *stock = stock.checked_sub(1).ok_or(SoldOut)?;
    Ok(())
}

pub fn place_order(stock: &mut u16) {
    reserve(stock).ok();
}

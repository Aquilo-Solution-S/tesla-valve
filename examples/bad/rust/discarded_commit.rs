// expect: let_underscore_must_use
pub struct SoldOut;

pub fn reserve(stock: &mut u16) -> Result<(), SoldOut> {
    *stock = stock.checked_sub(1).ok_or(SoldOut)?;
    Ok(())
}

pub fn place_order(stock: &mut u16) {
    let _ = reserve(stock);
}

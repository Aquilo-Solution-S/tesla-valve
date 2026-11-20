-- slot: Spec/Stock/Rush.lean
-- expect: no code under [../python/shop, ../python/tests] names in_stock_takes_shipping_only
import Spec.Stock

/-- An item in stock takes the shipping time and no more. -/
theorem in_stock_takes_shipping_only (shipping : Nat) : deliveryDays shipping .inStock = shipping :=
  rfl

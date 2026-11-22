-- expect: Spec.in_stock_takes_shipping_only is named by no file under
import Spec.Stock

namespace Spec

/-- An item in stock takes the shipping time and no more. -/
theorem in_stock_takes_shipping_only (shipping : Nat) : deliveryDays shipping .inStock = shipping :=
  rfl

end Spec

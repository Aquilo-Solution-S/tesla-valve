/-! Shipping promises -/

-- region: shipping
namespace Shop.Shipping

/-- The two shipping speeds the shop offers. -/
inductive Speed where
  | local
  | standard

/-- Postcodes in the local delivery area start with this prefix. -/
def localPrefix : String := "1"

/-- Days for local shipping. -/
def localDays : Nat := 2

/-- Days for standard shipping. -/
def standardDays : Nat := 3

/-- Days in transit for each speed. -/
def shippingDays : Speed → Nat
  | .local => localDays
  | .standard => standardDays

/-- Local shipping takes fewer days than standard shipping. -/
theorem local_shipping_is_faster : shippingDays .local < shippingDays .standard := by
  decide

end Shop.Shipping
-- endregion

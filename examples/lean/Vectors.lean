import Shop.Shipping
import Spec.Stock.Wire

open Shop.Shipping Spec

-- region: vectors
/-- What the code replays: both shipping times it knows, in stock and on backorder. -/
def inputs : List (Nat × Stock) :=
  [shippingDays .local, shippingDays .standard].flatMap fun shipping =>
    [.inStock, .backorder 0, .backorder 1, .backorder 5, .backorder 65535].map (shipping, ·)

/-- Where each codebase keeps the vectors its test replays. -/
def replayedBy : List System.FilePath := [
  "../go/testdata/delivery_days.json",
  "../python/tests/delivery_days.json",
  "../rust/src/delivery_days.json",
  "../typescript/src/delivery_days.json",
]

def main : IO Unit := do
  let vectors := inputs.map fun (shipping, stock) =>
    s!"  \{\"shipping\": {shipping}, \"stock\": {stockJson stock}, \"days\": {deliveryDays shipping stock}}"
  for path in replayedBy do
    IO.FS.writeFile path s!"[\n{",\n".intercalate vectors}\n]\n"
-- endregion

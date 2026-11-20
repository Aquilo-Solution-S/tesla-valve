import Spec.Stock

-- region: wire
/-- A stock status, as the warehouse sends it. -/
def stockJson : Stock → String
  | .inStock => "{\"status\": \"in_stock\"}"
  | .backorder restockDays => s!"\{\"status\": \"backorder\", \"restock_days\": {restockDays}}"
-- endregion

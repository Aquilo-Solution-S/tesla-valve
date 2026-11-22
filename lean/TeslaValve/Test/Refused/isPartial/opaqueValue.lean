/-- A value that reduction cannot read. -/
opaque hiddenValue : Bool := true

/-- A list whose tail cannot be computed. -/
opaque hiddenList : List Nat := []

/-- The known head followed by the hidden tail. -/
def partialList : List Nat := 1 :: hiddenList

/-- Whether to include the known head and hidden tail. -/
def chooseList : Bool → List Nat
  | true => partialList
  | false => []

/-! A Lean value that exceeds Rust's literal range. -/

namespace Accepted.LargeNat

/-- One more than the largest Rust integer literal. -/
def tooLarge : Nat := 340282366920938463463374607431768211456

end Accepted.LargeNat

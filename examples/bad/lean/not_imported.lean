-- expect: Tactic `decide` proved that the proposition
-- Nothing imports this module, and the gate still builds it.
example : 2 + 2 = 5 := by decide

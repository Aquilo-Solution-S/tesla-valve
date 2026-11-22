/-- A signed number. -/
def offset : Int := -1

/-- An option whose payload is another option. -/
def nested : Option (Option Bool) := some none

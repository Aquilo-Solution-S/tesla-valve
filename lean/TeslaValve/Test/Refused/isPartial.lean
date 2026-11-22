/-- A signal. -/
inductive Signal where
  /-- Up. -/
  | up
  | down
  deriving DecidableEq

/-- A decision over a closed choice that may not end: only its being partial refuses it. -/
partial def forever : Signal → Bool
  | s => forever s

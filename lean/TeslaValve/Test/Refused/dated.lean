/-- A switch's position, ruled on 2026-11-12. -/
inductive Toggle where
  /-- On. -/
  | on
  | off
  deriving DecidableEq

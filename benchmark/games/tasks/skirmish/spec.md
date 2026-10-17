# Ashline skirmish

Two squads fight on a fixed field. The game is deterministic. Coordinates are `[x,y]`,
with x increasing right and y increasing down. Input is UTF-8 text. Each input line is a JSON request;
produce exactly one JSON object and newline per line, in input order, and exit at EOF.
Write and flush each reply before reading the next line: a client waits for every reply.
Keep running after refusals. A refusal is exactly `{"ok":false,"error":CODE}` and changes
nothing, including pending orders and every fact affecting future play. A success has
exactly the members specified below. Object member order is immaterial. Array order is
specified. JSON integers exclude booleans, decimals and exponent notation. Duplicate
object members are outside the input domain. No request may have unlisted members.

## 1. Orders on the field

The map is nine rows of nine cells. `.` is plain, `s` is thicket, and `#` is crag:

```text
.........
..ss..#..
.s.#..#..
...#ss...
.##...##.
...ss#...
..#..#.s.
..#..ss..
.........
```

| Kind | Maximum hp | Attack | Attack range | Movement range |
| --- | ---: | ---: | ---: | ---: |
| lancer | 8 | 3 | 1 | 3 |
| bolt | 6 | 2 | 3 | 2 |
| glider | 5 | 2 | 2 | 4 |

Distance is Manhattan distance. Units cannot stand on crag. A move's destination must
be in bounds, different from its source, within movement range, and unoccupied by any
other unit. Intermediate cells do not matter. Attacks require a different, enemy unit
within attack range; intervening cells do not block attacks. Damage equals Attack.

`{"cmd":"new"}` starts a new game with these units at maximum hp, clearing all orders:

| id | owner | kind | x | y |
| ---: | ---: | --- | ---: | ---: |
| 1 | 1 | lancer | 1 | 0 |
| 2 | 1 | bolt | 4 | 0 |
| 3 | 1 | glider | 7 | 0 |
| 11 | 2 | lancer | 1 | 8 |
| 12 | 2 | bolt | 4 | 8 |
| 13 | 2 | glider | 7 | 8 |

Alternatively `new` may have `units`, an array of 2..20 deployment objects with exactly
`id`, `owner`, `kind`, `x`, `y`. IDs are distinct integers 1..99, owners are 1 or 2,
kinds are from the table, coordinates are integers 0..8 on terrain the kind can stand
on, and positions are distinct. Both owners must occur. Array order has no significance.
Bad deployments are `bad_request`; a valid new game may replace any phase.

`{"cmd":"state"}` returns `{"ok":true,"state":SNAPSHOT}`. A snapshot has exactly
`turn`, `phase`, `winner`, `ended`, `units`. Units are sorted by increasing id and have
exactly `id`, `owner`, `kind`, `x`, `y`, `hp`, `order`. An order is null or one of:
`{"type":"hold"}`, `{"type":"move","to":[x,y]}`, `{"type":"attack","target":id}`.
Before any game, the snapshot is `{"turn":0,"phase":"idle","winner":null,"ended":[],"units":[]}`.
After new, turn is 1, phase is `planning`, winner is null, ended is empty, and all
orders are null. During planning ended is a sorted subset of [1,2] with at most one
member, hp is 1..maximum, and orders retain their submitted values. No unit is removed
except through resolution or new. After a resolved turn, increment turn by one,
clear ended and all surviving orders. If both owners retain units, phase remains
planning and winner null. Otherwise phase is `finished` and winner is 1 or 2 for the
sole surviving owner, or 0 for no survivors. Finished snapshots retain survivors and
their hp/positions, with ended empty and orders null. State works in every phase.

`{"cmd":"order","player":p,"unit":id,"order":ORDER}` sets or replaces that own
unit's order. Player must be 1 or 2, unit and target IDs must be integers 1..99, and
move coordinates integers 0..8. Order syntax is exactly as above. Hold always works
for an available own unit. There is at most one stored order per unit. Success is
`{"ok":true}`. `{"cmd":"end_turn","player":p}` succeeds with the same reply, locks
that player's orders, and adds the player to ended. Missing orders behave as hold.
When both players have ended, resolution completes before that reply is sent:

1. Consider all move orders together, using pre-move positions. Moves with a shared
   destination, and both members of a two-unit position swap, are cancelled. Repeatedly
   cancel any move whose destination is occupied by a unit with no uncancelled move,
   until no more cancellations occur. Apply remaining moves together. A cycle of at
   least three moves is permitted. Cancelled moves leave the unit at its source.
2. Consider all attack orders from the post-move positions. Each still deals Attack
   if its target exists, is an enemy, and is in range; otherwise it deals zero. Apply
   all damage together, then remove units at hp <= 0. A unit killed in this turn still
   performs its attack.
3. Update turn, ended, orders, phase, and winner as defined above.

`{"cmd":"reachable","player":p,"unit":id}` returns `{"ok":true,"cells":[[x,y],...]}`,
sorted by y then x: exactly the destinations a move order from that player and unit
would accept under the current field. It ignores stored orders. `{"cmd":"forecast",
"player":p,"unit":id,"target":id}` returns `{"ok":true,"effect":"damage","amount":n}`:
exactly the damage that attack would deal if resolved at the current positions.
Forecast ignores pending orders and considers only the named attack.
Forecast uses the same validation as an attack order; out of range is a refusal, not
a successful zero. Both queries work during planning even after the player has ended,
and do not change anything. They must always agree with order acceptance and the
resolution rule. They refuse in idle and finished phases as below.

The closed error list is `bad_json`, `bad_request`, `unknown_command`, `not_started`,
`finished`, `turn_ended`, `unavailable`, `invalid_order`. Precedence is:
invalid JSON -> bad_json; non-object, absent/non-string cmd -> bad_request; unknown
string cmd -> unknown_command; any wrong request shape/type/enum/numeric domain ->
bad_request; for order/end_turn/reachable/forecast idle -> not_started or finished ->
finished; for order/end_turn an already-ended player -> turn_ended; a missing or
non-owned acting unit, or missing target -> unavailable; a wrong target side, bad
move destination terrain/occupancy/range, or out-of-range target -> invalid_order.
New deployment validation is request validation. Unit availability precedes target
availability and both precede geometric/side validation. State has no phase refusals.

## 2. Routes through terrain

Movement range is now a path cost budget. A route uses cardinal neighbor cells.
Entering plain costs 1 and entering thicket costs 2. Crag is impassable except that a
glider may enter and stand on it at cost 3. The source cell costs zero. Intermediate
units do not block routes; destination occupancy follows section 1. A different
destination is legal exactly when a route costs at most the kind's movement budget.
This replaces section 1's Manhattan movement rule for every move decision, including
the two queries' agreement requirements. Standing on crag is legal for gliders in new
deployments. All other commands, phases and snapshot values follow section 1.

## 3. A player's sight

Sight ranges are lancer 3, bolt 4, glider 2. A cell is visible to a player when its
Manhattan distance from at least one of that player's surviving units is at most that
unit's sight range. Terrain and other units do not block sight. Visibility is calculated
from current positions, independently of pending orders and ended status.

`{"cmd":"view","player":p}` returns `{"ok":true,"view":V}`. V has exactly the snapshot
members and `visible`, a y-then-x sorted array of all visible cells. Include all own
units and only enemies standing on visible cells. Own units include their actual order;
every included enemy's order is null, even when it has submitted an order. Turn, phase,
winner and ended equal state in every phase. Idle views have no units or visible cells.
Finished views use surviving units' sight; a player with no survivors sees no cells or
units. View works in all phases; its shape/player validation is bad_request.

Order, reachable and forecast decisions must use only what that player can see.
An unseen enemy does not block a destination at submission; it participates in movement
collisions at resolution. An unseen target has precisely the same `unavailable` reply
as an absent target, before target-side/range checks. Player-scoped replies never reveal
unseen units through unit data, destinations, amounts or error codes. End_turn only
returns its ordinary acknowledgement; public turn, phase, winner and ended may disclose
turn completion and victory. Own resolved positions and hp are always shown, including
the effects of collisions or attacks involving unseen enemies; this does not authorize
replies to include those enemies' identities, positions or orders. State remains an
observer's full snapshot. Existing fields
and resolution behavior otherwise follow sections 1 and 2.

## 4. Field tenders

The additional kind `mender` has maximum hp 7, movement budget 3, sight range 5 and
interaction range 1. It cannot stand on crag. Its attack order targets a different ally
and repairs up to 2 hp, capped at the ally's maximum. A mender's forecast has effect
`repair` and amount equal to the hp it would restore at current positions; a full-health
ally is a valid target with amount 0. All repairs happen together after movement and
before damage; sum repairs for each target and cap once. Then attacks and removals
follow section 1. A mender killed by that damage still repairs. Menders are units for
ownership and victory: a side with only menders is still in play. They are available
in new deployments; the default deployment stays as in section 1. Existing snapshot
and view fields have the same values and meaning in every phase.

## 5. Shelter from attacks

Damage is now `max(0, Attack - defence)`, replacing the Attack-only damage rule.
Defence is 2 when the target stands on thicket and 0 on plain or crag, using post-move
positions during resolution. Repair amounts are unaffected. The forecast agreement
requirement still applies. Commands, visibility, phases and existing fields are unchanged.

## 6. Portable battles

`{"cmd":"export"}` returns `{"ok":true,"document":D}` in any phase, with no mutation.
D is exactly a full state snapshot, including orders; it contains no version or map.
`{"cmd":"import","document":D}` replaces the entire game and returns `{"ok":true}`.
Missing/extra top-level request members are bad_request. Invalid documents are
`bad_document`, added to the closed error list, and leave the old game and its future
behavior untouched. Import works in every phase. No other fields change meaning.

A document has exactly the snapshot members. Turn is an integer 0..2147483647;
phase is idle/planning/finished; winner is null/0/1/2; ended is a sorted list of distinct
players 1 or 2; units is a list of at most 20 full unit objects sorted by strictly
increasing id. Unit objects have exactly the snapshot members; all ID/owner/kind/position
rules of deployment apply, hp is an integer 1..the kind's maximum, and orders have the
exact syntax and numeric domains of section 1. Positions cannot coincide. No unknown
members or kinds are allowed. Idle requires turn 0, winner null, ended empty and units
empty. Planning requires turn >= 1, winner null, at least one unit of each owner, and
ended either empty or a singleton. Finished requires turn >= 2, ended empty, every
order null, at most one surviving owner and winner exactly as in section 1.

Each non-null planning order must be acceptable under the current field and the
ordering player's sight (ignoring that player's ended status). Thus targets must exist
and be visible, sides/ranges must be correct, and moves must meet current route and
visible-destination rules. Orders for missing acting units cannot occur because each
order belongs to its containing unit. Both ended players in a planning document is
invalid: such a turn would already have resolved. Import imposes these structural and
local consistency checks, not a proof that a historical sequence produced the position.
Export followed by import must continue identically, including a half-ended turn.
To keep the turn domain closed, end_turn refuses with bad_request when turn is
2147483647 (before phase/ended checks); no resolution overflows the domain.

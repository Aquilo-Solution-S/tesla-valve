use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::io::{self, BufRead, Write};

const MAP: [&str; 9] = [
    ".........",
    "..ss..#..",
    ".s.#..#..",
    "...#ss...",
    ".##...##.",
    "...ss#...",
    "..#..#.s.",
    "..#..ss..",
    ".........",
];

#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Unit {
    id: i64,
    owner: i64,
    kind: String,
    x: i64,
    y: i64,
    hp: i64,
    order: Option<Value>,
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Game {
    turn: i64,
    phase: String,
    winner: Option<i64>,
    ended: Vec<i64>,
    units: Vec<Unit>,
}

#[derive(Clone, Copy)]
struct Facts {
    hp: i64,
    attack: i64,
    range: i64,
    movement: i64,
}

fn facts(kind: &str) -> Option<Facts> {
    let (hp, attack, range, movement) = match kind {
        "lancer" => (8, 3, 1, 3),
        "bolt" => (6, 2, 3, 2),
        "glider" => (5, 2, 2, 4),
        _ => return None,
    };
    Some(Facts {
        hp,
        attack,
        range,
        movement,
    })
}

fn keys(v: &Value, names: &[&str]) -> bool {
    v.as_object()
        .is_some_and(|o| o.len() == names.len() && names.iter().all(|k| o.contains_key(*k)))
}
fn integer(v: &Value, low: i64, high: i64) -> bool {
    v.as_i64().is_some_and(|n| (low..=high).contains(&n))
}
fn distance(a: (i64, i64), b: (i64, i64)) -> i64 {
    (a.0 - b.0).abs() + (a.1 - b.1).abs()
}
fn tile(x: i64, y: i64) -> u8 {
    MAP[y as usize].as_bytes()[x as usize]
}
fn stand(kind: &str, x: i64, y: i64) -> bool {
    if !(0..9).contains(&x) || !(0..9).contains(&y) {
        return false;
    }
    let _ = kind;
    tile(x, y) != b'#'
}
fn order_shape(v: &Value) -> bool {
    match v["type"].as_str() {
        Some("hold") => keys(v, &["type"]),
        Some("move") => {
            keys(v, &["type", "to"])
                && v["to"]
                    .as_array()
                    .is_some_and(|a| a.len() == 2 && a.iter().all(|n| integer(n, 0, 8)))
        }
        Some("attack") => keys(v, &["type", "target"]) && integer(&v["target"], 1, 99),
        _ => false,
    }
}

impl Game {
    fn idle() -> Self {
        Self {
            turn: 0,
            phase: "idle".into(),
            winner: None,
            ended: vec![],
            units: vec![],
        }
    }
    fn index(&self, id: i64) -> Option<usize> {
        self.units.iter().position(|u| u.id == id)
    }
    fn visible(&self, player: i64, unit: &Unit) -> bool {
        let _ = (player, unit);
        true
    }
    fn route(&self, u: &Unit, x: i64, y: i64) -> bool {
        if (x, y) == (u.x, u.y) || !stand(&u.kind, x, y) {
            return false;
        }
        let budget = facts(&u.kind).unwrap().movement;
        distance((u.x, u.y), (x, y)) <= budget
    }
    fn move_allowed(&self, u: &Unit, x: i64, y: i64) -> bool {
        self.route(u, x, y)
            && !self
                .units
                .iter()
                .any(|v| v.id != u.id && v.x == x && v.y == y && self.visible(u.owner, v))
    }
    fn interaction(&self, u: &Unit, target: i64) -> Result<(String, i64), &'static str> {
        let v = self
            .index(target)
            .map(|i| &self.units[i])
            .filter(|v| self.visible(u.owner, v))
            .ok_or("unavailable")?;
        let f = facts(&u.kind).unwrap();
        if u.id == v.id || u.owner == v.owner || distance((u.x, u.y), (v.x, v.y)) > f.range {
            return Err("invalid_order");
        }
        Ok(("damage".into(), self.damage(u, v)))
    }
    fn damage(&self, u: &Unit, v: &Unit) -> i64 {
        let _ = v;
        facts(&u.kind).unwrap().attack
    }
    fn valid_order(&self, u: &Unit, o: &Value) -> Result<(), &'static str> {
        match o["type"].as_str().unwrap() {
            "move" => {
                if !self.move_allowed(
                    u,
                    o["to"][0].as_i64().unwrap(),
                    o["to"][1].as_i64().unwrap(),
                ) {
                    return Err("invalid_order");
                }
            }
            "attack" => {
                self.interaction(u, o["target"].as_i64().unwrap())?;
            }
            _ => (),
        }
        Ok(())
    }
    fn resolve(&mut self) {
        let n = self.units.len();
        let mut moves: Vec<Option<(i64, i64)>> = self
            .units
            .iter()
            .map(|u| {
                u.order.as_ref().and_then(|o| {
                    if o["type"] == "move" {
                        Some((o["to"][0].as_i64().unwrap(), o["to"][1].as_i64().unwrap()))
                    } else {
                        None
                    }
                })
            })
            .collect();
        let proposed = moves.clone();
        for i in 0..n {
            if let Some(to) = proposed[i] {
                for (j, other) in proposed.iter().enumerate() {
                    if i == j {
                        continue;
                    }
                    if *other == Some(to)
                        || (to == (self.units[j].x, self.units[j].y)
                            && *other == Some((self.units[i].x, self.units[i].y)))
                    {
                        moves[i] = None;
                    }
                }
            }
        }
        loop {
            let before = moves.clone();
            for i in 0..n {
                if let Some(to) = before[i] {
                    if (0..n)
                        .any(|j| (self.units[j].x, self.units[j].y) == to && before[j].is_none())
                    {
                        moves[i] = None;
                    }
                }
            }
            if moves == before {
                break;
            }
        }
        for (u, to) in self.units.iter_mut().zip(moves) {
            if let Some((x, y)) = to {
                u.x = x;
                u.y = y;
            }
        }
        let mut hits = vec![0; n];
        for u in &self.units {
            if let Some(o) = &u.order {
                if o["type"] == "attack" {
                    if let Some(j) = self.index(o["target"].as_i64().unwrap()) {
                        let v = &self.units[j];
                        if u.owner != v.owner
                            && distance((u.x, u.y), (v.x, v.y)) <= facts(&u.kind).unwrap().range
                        {
                            hits[j] += self.damage(u, v);
                        }
                    }
                }
            }
        }
        for (u, hit) in self.units.iter_mut().zip(hits) {
            u.hp -= hit;
            u.order = None;
        }
        self.units.retain(|u| u.hp > 0);
        self.turn += 1;
        self.ended.clear();
        let a = self.units.iter().any(|u| u.owner == 1);
        let b = self.units.iter().any(|u| u.owner == 2);
        if !a || !b {
            self.phase = "finished".into();
            self.winner = Some(if a {
                1
            } else if b {
                2
            } else {
                0
            });
        }
    }
    fn deployment(v: &Value) -> Result<Vec<Unit>, &'static str> {
        let a = v
            .as_array()
            .filter(|a| (2..=20).contains(&a.len()))
            .ok_or("bad_request")?;
        let mut units = Vec::<Unit>::new();
        for r in a {
            if !keys(r, &["id", "owner", "kind", "x", "y"])
                || !integer(&r["id"], 1, 99)
                || !integer(&r["owner"], 1, 2)
                || !integer(&r["x"], 0, 8)
                || !integer(&r["y"], 0, 8)
            {
                return Err("bad_request");
            }
            let kind = r["kind"]
                .as_str()
                .filter(|k| facts(k).is_some())
                .ok_or("bad_request")?;
            let x = r["x"].as_i64().unwrap();
            let y = r["y"].as_i64().unwrap();
            let id = r["id"].as_i64().unwrap();
            if !stand(kind, x, y) || units.iter().any(|u| u.id == id || (u.x, u.y) == (x, y)) {
                return Err("bad_request");
            }
            units.push(Unit {
                id,
                owner: r["owner"].as_i64().unwrap(),
                kind: kind.into(),
                x,
                y,
                hp: facts(kind).unwrap().hp,
                order: None,
            });
        }
        if !(1..=2).all(|p| units.iter().any(|u| u.owner == p)) {
            return Err("bad_request");
        }
        units.sort_by_key(|u| u.id);
        Ok(units)
    }
    fn dispatch(&mut self, r: &Value) -> Result<Value, &'static str> {
        let cmd = r["cmd"].as_str().ok_or("bad_request")?;
        let shape = match cmd {
            "new" => keys(r, &["cmd"]) || keys(r, &["cmd", "units"]),
            "state" => keys(r, &["cmd"]),
            "order" => keys(r, &["cmd", "player", "unit", "order"]) && order_shape(&r["order"]),
            "end_turn" => keys(r, &["cmd", "player"]),
            "reachable" => keys(r, &["cmd", "player", "unit"]),
            "forecast" => {
                keys(r, &["cmd", "player", "unit", "target"]) && integer(&r["target"], 1, 99)
            }
            _ => return Err("unknown_command"),
        };
        if !shape {
            return Err("bad_request");
        }
        if r.get("player").is_some() && !integer(&r["player"], 1, 2) {
            return Err("bad_request");
        }
        if r.get("unit").is_some() && !integer(&r["unit"], 1, 99) {
            return Err("bad_request");
        }
        match cmd {
            "state" => return Ok(json!({"ok":true,"state":self})),
            "new" => {
                let defaults = json!([
                    {"id":1,"owner":1,"kind":"lancer","x":1,"y":0}, {"id":2,"owner":1,"kind":"bolt","x":4,"y":0},
                    {"id":3,"owner":1,"kind":"glider","x":7,"y":0}, {"id":11,"owner":2,"kind":"lancer","x":1,"y":8},
                    {"id":12,"owner":2,"kind":"bolt","x":4,"y":8}, {"id":13,"owner":2,"kind":"glider","x":7,"y":8}]);
                let units = Self::deployment(r.get("units").unwrap_or(&defaults))?;
                *self = Self {
                    turn: 1,
                    phase: "planning".into(),
                    winner: None,
                    ended: vec![],
                    units,
                };
                return Ok(json!({"ok":true}));
            }
            _ => (),
        }
        if self.phase == "idle" {
            return Err("not_started");
        }
        if self.phase == "finished" {
            return Err("finished");
        }
        let p = r["player"].as_i64().unwrap();
        if ["order", "end_turn"].contains(&cmd) && self.ended.contains(&p) {
            return Err("turn_ended");
        }
        if cmd == "end_turn" {
            self.ended.push(p);
            self.ended.sort();
            if self.ended.len() == 2 {
                self.resolve();
            }
            return Ok(json!({"ok":true}));
        }
        let i = self
            .index(r["unit"].as_i64().unwrap())
            .filter(|i| self.units[*i].owner == p)
            .ok_or("unavailable")?;
        let u = &self.units[i];
        match cmd {
            "order" => {
                self.valid_order(u, &r["order"])?;
                self.units[i].order = Some(r["order"].clone());
                Ok(json!({"ok":true}))
            }
            "reachable" => {
                let mut cells = Vec::new();
                for y in 0..9 {
                    for x in 0..9 {
                        if self.move_allowed(u, x, y) {
                            cells.push([x, y]);
                        }
                    }
                }
                Ok(json!({"ok":true,"cells":cells}))
            }
            "forecast" => {
                let (effect, amount) = self.interaction(u, r["target"].as_i64().unwrap())?;
                Ok(json!({"ok":true,"effect":effect,"amount":amount}))
            }
            _ => unreachable!(),
        }
    }
}

fn main() {
    let mut game = Game::idle();
    let stdin = io::stdin();
    let mut stdout = io::stdout().lock();
    for line in stdin.lock().lines() {
        let Ok(line) = line else { break };
        let result = match serde_json::from_str::<Value>(&line) {
            Err(_) => Err("bad_json"),
            Ok(r) if !r.is_object() => Err("bad_request"),
            Ok(r) => {
                // Commit only successful commands, including a completely validated import.
                let mut next = game.clone();
                let reply = next.dispatch(&r);
                if reply.is_ok() {
                    game = next;
                }
                reply
            }
        };
        let reply = result.unwrap_or_else(|e| json!({"ok":false,"error":e}));
        if writeln!(stdout, "{reply}")
            .and_then(|()| stdout.flush())
            .is_err()
        {
            break;
        }
    }
}

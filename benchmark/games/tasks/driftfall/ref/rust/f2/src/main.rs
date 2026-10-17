use serde_json::{json, Value};
use std::io::{self, BufRead, Write};

const SHAPES: &[&[(i32, i32)]] = &[
    &[(0, 0), (0, 1), (1, 1)],
    &[(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
    &[(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
    &[(0, 0), (2, 0), (0, 1), (1, 1), (2, 1)],
    &[(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)],
];
const NAMES: &[&str] = &["sprig", "prong", "ramp", "arch", "reed"];

#[derive(Clone)]
struct Piece {
    kind: usize,
    cells: Vec<(i32, i32)>,
    x: i32,
    y: i32,
}

#[derive(Clone)]
struct Game {
    board: Vec<Vec<bool>>,
    phase: &'static str,
    active: Option<Piece>,
    rng: u32,
    score: u64,
    lines: u64,
    credit: u64,
}

fn members(v: &Value, required: &[&str], optional: &[&str]) -> bool {
    v.as_object().is_some_and(|m| {
        required.iter().all(|k| m.contains_key(*k))
            && m.keys()
                .all(|k| required.contains(&k.as_str()) || optional.contains(&k.as_str()))
    })
}
fn integer(v: &Value, max: u64) -> Option<u64> {
    v.as_u64().filter(|n| *n <= max)
}
fn fail(code: &str) -> Value {
    json!({"ok": false, "error": code})
}

impl Game {
    fn idle() -> Self {
        Self {
            board: vec![vec![false; 10]; 18],
            phase: "idle",
            active: None,
            rng: 0,
            score: 0,
            lines: 0,
            credit: 0,
        }
    }
    fn draw(&mut self) -> usize {
        self.rng ^= self.rng << 13;
        self.rng ^= self.rng >> 17;
        self.rng ^= self.rng << 5;
        (self.rng % 5) as usize
    }
    fn level(&self) -> u64 {
        1 + self.lines / 4
    }
    fn interval(&self) -> u64 {
        600u64.saturating_sub(45 * (self.level() - 1)).max(90)
    }
    fn fits(&self, p: &Piece) -> bool {
        p.cells.iter().all(|(cx, cy)| {
            let (x, y) = (p.x + cx, p.y + cy);
            (0..10).contains(&x) && (0..18).contains(&y) && !self.board[y as usize][x as usize]
        })
    }
    fn spawn(&mut self, kind: usize) {
        let p = Piece {
            kind,
            cells: SHAPES[kind].to_vec(),
            x: 4,
            y: 0,
        };
        if self.fits(&p) {
            self.active = Some(p);
        } else {
            self.phase = "over";
            self.active = None;
        }
    }
    fn next_kind(&mut self) -> usize {
        self.draw()
    }
    fn start(&mut self, seed: u32) {
        *self = Self::idle();
        self.phase = "playing";
        self.rng = if seed == 0 { 2463534242 } else { seed };
        let kind = self.draw();
        self.spawn(kind);
    }
    fn lock(&mut self) {
        let p = self.active.take().expect("lock requires an active piece");
        self.credit = 0;
        for (x, y) in p.cells {
            self.board[(p.y + y) as usize][(p.x + x) as usize] = true;
        }
        self.score += 7;
        let old_level = self.level();
        let before = self.board.len();
        self.board.retain(|row| !row.iter().all(|v| *v));
        let count = before - self.board.len();
        for _ in 0..count {
            self.board.insert(0, vec![false; 10]);
        }
        self.score += 80 * (count as u64).pow(2) * old_level;
        self.lines += count as u64;
        let next = self.next_kind();
        self.spawn(next);
    }
    fn translate(&mut self, dx: i32, dy: i32) -> bool {
        let mut candidate = self.active.as_ref().expect("playing has a piece").clone();
        candidate.x += dx;
        candidate.y += dy;
        if !self.fits(&candidate) {
            return false;
        }
        self.active = Some(candidate);
        true
    }
    fn rotate(&mut self) {
        let mut p = self.active.as_ref().expect("playing has a piece").clone();
        let h = p.cells.iter().map(|c| c.1).max().unwrap() + 1;
        for c in &mut p.cells {
            *c = (h - 1 - c.1, c.0);
        }
        let min_x = p.cells.iter().map(|c| c.0).min().unwrap();
        let min_y = p.cells.iter().map(|c| c.1).min().unwrap();
        for c in &mut p.cells {
            c.0 -= min_x;
            c.1 -= min_y;
        }
        if self.fits(&p) {
            self.active = Some(p);
        }
    }
    fn playable(&self) -> Result<(), &'static str> {
        match self.phase {
            "idle" => Err("not_started"),
            "paused" => Err("paused"),
            "playing" => Ok(()),
            _ => Err("finished"),
        }
    }
    fn tick(&mut self, ms: u64) -> Result<(), &'static str> {
        self.playable()?;
        self.credit += ms;
        while self.phase == "playing" && self.credit >= self.interval() {
            self.credit -= self.interval();
            if !self.translate(0, 1) {
                self.lock();
            }
        }
        Ok(())
    }
    fn pause(&mut self, resume: bool) -> Result<(), &'static str> {
        match self.phase {
            "idle" => return Err("not_started"),
            "over" | "won" => return Err("finished"),
            _ => (),
        }
        self.phase = if resume { "playing" } else { "paused" };
        Ok(())
    }
    fn input(&mut self, key: &str) -> Result<(), &'static str> {
        self.playable()?;
        match key {
            "left" => {
                self.translate(-1, 0);
            }
            "right" => {
                self.translate(1, 0);
            }
            "rotate" => self.rotate(),
            "soft" => {
                if self.translate(0, 1) {
                    self.score += 1;
                } else {
                    self.lock();
                }
            }
            "hard" => {
                while self.translate(0, 1) {
                    self.score += 2;
                }
                self.lock();
            }
            _ => unreachable!("input is validated before dispatch"),
        }
        Ok(())
    }
    fn snapshot(&self) -> Value {
        let board: Vec<String> = self
            .board
            .iter()
            .map(|row| row.iter().map(|b| if *b { '#' } else { '.' }).collect())
            .collect();
        let active = self.active.as_ref().map(|p| {
            let mut cells: Vec<(i32, i32)> =
                p.cells.iter().map(|(x, y)| (p.x + x, p.y + y)).collect();
            cells.sort_by_key(|(x, y)| (*y, *x));
            json!({"kind": NAMES[p.kind], "cells": cells})
        });
        let mut value = json!({"phase": self.phase, "board": board, "active": active,
            "score": self.score, "lines": self.lines, "level": self.level()});
        // Keep the binding mutable in base versions without special-case source formatting.
        value.as_object_mut().expect("snapshot is an object");
        value
    }
    fn command(&mut self, v: &Value) -> Value {
        let Some(cmd) = v.get("cmd").and_then(Value::as_str) else {
            return fail("bad_request");
        };
        let result = match cmd {
            "state" => {
                if !members(v, &["cmd"], &[]) {
                    return fail("bad_request");
                }
                return json!({"ok": true, "state": self.snapshot()});
            }
            "new" => {
                let optional: &[&str] = &[];
                if !members(v, &["cmd", "seed"], optional) {
                    return fail("bad_request");
                }
                let Some(seed) = integer(&v["seed"], u32::MAX as u64) else {
                    return fail("bad_request");
                };
                self.start(seed as u32);
                Ok(())
            }
            "tick" => {
                if !members(v, &["cmd", "ms"], &[]) {
                    return fail("bad_request");
                }
                let Some(ms) = integer(&v["ms"], 1000000) else {
                    return fail("bad_request");
                };
                self.tick(ms)
            }
            "input" => {
                if !members(v, &["cmd", "key"], &[]) {
                    return fail("bad_request");
                }
                let Some(key) = v["key"].as_str().filter(|s| valid_key(s)) else {
                    return fail("bad_request");
                };
                self.input(key)
            }
            "pause" | "resume" => {
                if !members(v, &["cmd"], &[]) {
                    return fail("bad_request");
                }
                self.pause(cmd == "resume")
            }
            _ => Err("unknown_command"),
        };
        match result {
            Ok(()) => json!({"ok": true}),
            Err(code) => fail(code),
        }
    }
}
fn valid_key(key: &str) -> bool {
    matches!(key, "left" | "right" | "rotate" | "soft" | "hard")
}
fn main() {
    let stdin = io::stdin();
    let mut out = io::BufWriter::new(io::stdout().lock());
    let mut game = Game::idle();
    for line in stdin.lock().lines() {
        let Ok(line) = line else {
            break;
        };
        let reply = match serde_json::from_str::<Value>(&line) {
            Ok(v) => game.command(&v),
            Err(_) => fail("bad_json"),
        };
        if writeln!(out, "{reply}").and_then(|()| out.flush()).is_err() {
            break;
        }
    }
}

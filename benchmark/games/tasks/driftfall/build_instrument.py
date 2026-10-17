"""Materialize versioned reference sources; no network or dependencies are needed."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent


def select(source, step):
    result, stack = [], [True]
    for line in source.splitlines():
        match = re.fullmatch(r'\s*// @if ([1-6])', line)
        if match:
            stack.append(stack[-1] and step >= int(match[1]))
        elif line.strip() == '// @end':
            stack.pop()
        elif stack[-1]:
            result.append(line)
    assert len(stack) == 1
    return '\n'.join(result) + '\n'


RUST = r'''
use serde_json::{json, Value};
use std::io::{self, BufRead, Write};

const SHAPES: &[&[(i32, i32)]] = &[
    &[(0, 0), (0, 1), (1, 1)],
    &[(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
    &[(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
    &[(0, 0), (2, 0), (0, 1), (1, 1), (2, 1)],
    &[(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)],
    // @if 4
    &[(0, 0), (0, 1), (0, 2)],
    // @end
];
const NAMES: &[&str] = &[
    "sprig", "prong", "ramp", "arch", "reed",
    // @if 4
    "pulse",
    // @end
];

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
    // @if 3
    held: Option<usize>,
    preview: Vec<usize>,
    hold_available: bool,
    // @end
    // @if 5
    mode: String,
    elapsed_ms: u64,
    // @end
}

fn members(v: &Value, required: &[&str], optional: &[&str]) -> bool {
    v.as_object().is_some_and(|m| {
        required.iter().all(|k| m.contains_key(*k))
            && m.keys().all(|k| required.contains(&k.as_str()) || optional.contains(&k.as_str()))
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
            phase: "idle", active: None, rng: 0, score: 0, lines: 0, credit: 0,
            // @if 3
            held: None, preview: Vec::new(), hold_available: false,
            // @end
            // @if 5
            mode: "endless".into(), elapsed_ms: 0,
            // @end
        }
    }
    fn draw(&mut self) -> usize {
        self.rng ^= self.rng << 13;
        self.rng ^= self.rng >> 17;
        self.rng ^= self.rng << 5;
        // @if 4
        if self.rng % 16 == 15 { return 5; }
        // @end
        (self.rng % 5) as usize
    }
    fn level(&self) -> u64 { 1 + self.lines / 4 }
    fn interval(&self) -> u64 { 600u64.saturating_sub(45 * (self.level() - 1)).max(90) }
    fn fits(&self, p: &Piece) -> bool {
        p.cells.iter().all(|(cx, cy)| {
            let (x, y) = (p.x + cx, p.y + cy);
            (0..10).contains(&x) && (0..18).contains(&y) && !self.board[y as usize][x as usize]
        })
    }
    fn spawn(&mut self, kind: usize) {
        let p = Piece { kind, cells: SHAPES[kind].to_vec(), x: 4, y: 0 };
        if self.fits(&p) { self.active = Some(p); }
        else {
            self.phase = "over"; self.active = None;
            // @if 3
            self.hold_available = false;
            // @end
        }
    }
    fn next_kind(&mut self) -> usize {
        // @if 3
        if !self.preview.is_empty() {
            let kind = self.preview.remove(0);
            let tail = self.draw();
            self.preview.push(tail);
            return kind;
        }
        // @end
        self.draw()
    }
    fn start(&mut self, seed: u32) {
        *self = Self::idle();
        self.phase = "playing";
        self.rng = if seed == 0 { 2463534242 } else { seed };
        let kind = self.draw();
        // @if 3
        for _ in 0..3 { let next = self.draw(); self.preview.push(next); }
        self.hold_available = true;
        // @end
        self.spawn(kind);
    }
    fn lock(&mut self) {
        let p = self.active.take().expect("lock requires an active piece");
        self.credit = 0;
        // @if 4
        if p.kind == 5 {
            let mut erased = 0;
            for y in (p.y + 1).max(0)..=(p.y + 3).min(17) {
                for x in (p.x - 1).max(0)..=(p.x + 1).min(9) {
                    if self.board[y as usize][x as usize] { erased += 1; }
                    self.board[y as usize][x as usize] = false;
                }
            }
            self.score += 11 + 3 * erased;
        } else {
        // @end
        for (x, y) in p.cells { self.board[(p.y + y) as usize][(p.x + x) as usize] = true; }
        self.score += 7;
        // @if 4
        }
        // @end
        let old_level = self.level();
        let before = self.board.len();
        self.board.retain(|row| !row.iter().all(|v| *v));
        let count = before - self.board.len();
        for _ in 0..count { self.board.insert(0, vec![false; 10]); }
        self.score += 80 * (count as u64).pow(2) * old_level;
        self.lines += count as u64;
        // @if 5
        if self.mode == "rush" && self.lines >= 4 {
            self.phase = "won";
            self.hold_available = false;
            return;
        }
        // @end
        // @if 3
        self.hold_available = true;
        // @end
        let next = self.next_kind();
        self.spawn(next);
    }
    fn translate(&mut self, dx: i32, dy: i32) -> bool {
        let mut candidate = self.active.as_ref().expect("playing has a piece").clone();
        candidate.x += dx; candidate.y += dy;
        if !self.fits(&candidate) { return false; }
        self.active = Some(candidate); true
    }
    fn rotate(&mut self) {
        let mut p = self.active.as_ref().expect("playing has a piece").clone();
        // @if 4
        if p.kind == 5 { return; }
        // @end
        let h = p.cells.iter().map(|c| c.1).max().unwrap() + 1;
        for c in &mut p.cells { *c = (h - 1 - c.1, c.0); }
        let min_x = p.cells.iter().map(|c| c.0).min().unwrap();
        let min_y = p.cells.iter().map(|c| c.1).min().unwrap();
        for c in &mut p.cells { c.0 -= min_x; c.1 -= min_y; }
        if self.fits(&p) { self.active = Some(p); }
    }
    fn playable(&self) -> Result<(), &'static str> {
        match self.phase {
            "idle" => Err("not_started"),
            // @if 2
            "paused" => Err("paused"),
            // @end
            "playing" => Ok(()),
            _ => Err("finished"),
        }
    }
    fn tick(&mut self, ms: u64) -> Result<(), &'static str> {
        self.playable()?;
        // @if 5
        self.elapsed_ms += ms;
        // @end
        self.credit += ms;
        while self.phase == "playing" && self.credit >= self.interval() {
            self.credit -= self.interval();
            if !self.translate(0, 1) { self.lock(); }
        }
        Ok(())
    }
    // @if 2
    fn pause(&mut self, resume: bool) -> Result<(), &'static str> {
        match self.phase {
            "idle" => return Err("not_started"),
            "over" | "won" => return Err("finished"),
            _ => (),
        }
        self.phase = if resume { "playing" } else { "paused" };
        Ok(())
    }
    // @end
    // @if 3
    fn hold(&mut self) -> Result<(), &'static str> {
        if !self.hold_available { return Err("hold_used"); }
        let outgoing = self.active.as_ref().unwrap().kind;
        let incoming = self.held.unwrap_or_else(|| self.next_kind());
        self.held = Some(outgoing);
        self.credit = 0;
        self.hold_available = false;
        self.spawn(incoming);
        Ok(())
    }
    // @end
    fn input(&mut self, key: &str) -> Result<(), &'static str> {
        self.playable()?;
        match key {
            "left" => { self.translate(-1, 0); }
            "right" => { self.translate(1, 0); }
            "rotate" => self.rotate(),
            "soft" => { if self.translate(0, 1) { self.score += 1; } else { self.lock(); } }
            "hard" => { while self.translate(0, 1) { self.score += 2; } self.lock(); }
            // @if 3
            "hold" => return self.hold(),
            // @end
            _ => unreachable!("input is validated before dispatch"),
        }
        Ok(())
    }
    fn snapshot(&self) -> Value {
        let board: Vec<String> = self.board.iter().map(|row| row.iter().map(|b| if *b {'#'} else {'.'}).collect()).collect();
        let active = self.active.as_ref().map(|p| {
            let mut cells: Vec<(i32, i32)> = p.cells.iter().map(|(x,y)| (p.x+x,p.y+y)).collect();
            cells.sort_by_key(|(x,y)| (*y,*x));
            json!({"kind": NAMES[p.kind], "cells": cells})
        });
        let mut value = json!({"phase": self.phase, "board": board, "active": active,
            "score": self.score, "lines": self.lines, "level": self.level()});
        // @if 3
        value["held"] = json!(self.held.map(|k| NAMES[k]));
        value["preview"] = json!(self.preview.iter().map(|k| NAMES[*k]).collect::<Vec<_>>());
        value["hold_available"] = json!(self.hold_available);
        // @end
        // @if 5
        value["mode"] = json!(self.mode);
        value["elapsed_ms"] = json!(self.elapsed_ms);
        // @end
        // Keep the binding mutable in base versions without special-case source formatting.
        value.as_object_mut().expect("snapshot is an object");
        value
    }
    // @if 6
    fn replay(&mut self, doc: &Value) -> Result<(), &'static str> {
        if !members(doc, &["seed", "mode", "events", "end_ms"], &[]) { return Err("bad_replay"); }
        let seed = integer(&doc["seed"], u32::MAX as u64).ok_or("bad_replay")?;
        let mode = doc["mode"].as_str().filter(|s| matches!(*s, "endless" | "rush")).ok_or("bad_replay")?;
        let end = integer(&doc["end_ms"], 1000000).ok_or("bad_replay")?;
        let events = doc["events"].as_array().filter(|a| a.len() <= 4096).ok_or("bad_replay")?;
        let mut previous = 0;
        let mut validated = Vec::new();
        for event in events {
            if !members(event, &["at_ms", "key"], &[]) { return Err("bad_replay"); }
            let at = integer(&event["at_ms"], 1000000).ok_or("bad_replay")?;
            let key = event["key"].as_str().filter(|s| valid_key(s) || matches!(*s, "pause" | "resume")).ok_or("bad_replay")?;
            if at < previous || at > end { return Err("bad_replay"); }
            validated.push((at, key)); previous = at;
        }
        let mut fresh = Self::idle();
        fresh.start(seed as u32); fresh.mode = mode.into();
        previous = 0;
        for (at, key) in validated {
            let _ = fresh.tick(at - previous);
            match key {
                "pause" => { let _ = fresh.pause(false); }
                "resume" => { let _ = fresh.pause(true); }
                _ => { let _ = fresh.input(key); }
            }
            previous = at;
        }
        let _ = fresh.tick(end - previous);
        *self = fresh;
        Ok(())
    }
    // @end
    fn command(&mut self, v: &Value) -> Value {
        let Some(cmd) = v.get("cmd").and_then(Value::as_str) else { return fail("bad_request"); };
        let result = match cmd {
            "state" => {
                if !members(v, &["cmd"], &[]) { return fail("bad_request"); }
                return json!({"ok": true, "state": self.snapshot()});
            }
            "new" => {
                let optional: &[&str] = &[
                    // @if 5
                    "mode",
                    // @end
                ];
                if !members(v, &["cmd", "seed"], optional) { return fail("bad_request"); }
                let Some(seed) = integer(&v["seed"], u32::MAX as u64) else { return fail("bad_request"); };
                // @if 5
                let mode = if v.get("mode").is_some() {
                    match v["mode"].as_str() { Some("endless") => "endless", Some("rush") => "rush", _ => return fail("bad_request") }
                } else { "endless" };
                // @end
                self.start(seed as u32);
                // @if 5
                self.mode = mode.into();
                // @end
                Ok(())
            }
            "tick" => {
                if !members(v, &["cmd", "ms"], &[]) { return fail("bad_request"); }
                let Some(ms) = integer(&v["ms"], 1000000) else { return fail("bad_request"); };
                self.tick(ms)
            }
            "input" => {
                if !members(v, &["cmd", "key"], &[]) { return fail("bad_request"); }
                let Some(key) = v["key"].as_str().filter(|s| valid_key(s)) else { return fail("bad_request"); };
                self.input(key)
            }
            // @if 2
            "pause" | "resume" => {
                if !members(v, &["cmd"], &[]) { return fail("bad_request"); }
                self.pause(cmd == "resume")
            }
            // @end
            // @if 6
            "replay" => {
                if !members(v, &["cmd", "document"], &[]) { return fail("bad_request"); }
                self.replay(&v["document"])
            }
            // @end
            _ => Err("unknown_command"),
        };
        match result { Ok(()) => json!({"ok": true}), Err(code) => fail(code) }
    }
}
fn valid_key(key: &str) -> bool {
    matches!(key, "left" | "right" | "rotate" | "soft" | "hard")
    // @if 3
    || key == "hold"
    // @end
}
fn main() {
    let stdin = io::stdin();
    let mut out = io::BufWriter::new(io::stdout().lock());
    let mut game = Game::idle();
    for line in stdin.lock().lines() {
        let Ok(line) = line else { break; };
        let reply = match serde_json::from_str::<Value>(&line) {
            Ok(v) => game.command(&v), Err(_) => fail("bad_json"),
        };
        if writeln!(out, "{reply}").and_then(|()| out.flush()).is_err() { break; }
    }
}
'''

GO = r'''
package main

import (
    "bufio"
    "encoding/json"
    "io"
    "os"
    "sort"
    "strconv"
    "strings"
)

type cell struct { x, y int }
type piece struct { kind, x, y int; cells []cell }
var shapes = [][]cell{
    {{0,0},{0,1},{1,1}},
    {{0,0},{1,0},{2,0},{1,1},{1,2}},
    {{0,0},{0,1},{1,1},{1,2},{2,2}},
    {{0,0},{2,0},{0,1},{1,1},{2,1}},
    {{0,0},{0,1},{0,2},{0,3},{1,3}},
    // @if 4
    {{0,0},{0,1},{0,2}},
    // @end
}
var names = []string{
    "sprig", "prong", "ramp", "arch", "reed",
    // @if 4
    "pulse",
    // @end
}
type game struct {
    board [18][10]bool
    phase string
    active *piece
    rng uint32
    score, lines, credit uint64
    // @if 3
    held *int
    preview []int
    holdAvailable bool
    // @end
    // @if 5
    mode string
    elapsedMS uint64
    // @end
}
func idle() game {
    g := game{phase:"idle"}
    // @if 5
    g.mode = "endless"
    // @end
    return g
}
func object(v any) map[string]any { m, _ := v.(map[string]any); return m }
func text(v any) string { s, _ := v.(string); return s }
func members(m map[string]any, required, optional []string) bool {
    if m == nil { return false }
    allowed := make(map[string]bool)
    for _, k := range required { if _, ok := m[k]; !ok { return false }; allowed[k] = true }
    for _, k := range optional { allowed[k] = true }
    for k := range m { if !allowed[k] { return false } }
    return true
}
func integer(v any, maximum uint64) (uint64, bool) {
    n, ok := v.(json.Number); if !ok { return 0, false }
    parsed, err := strconv.ParseUint(string(n), 10, 64)
    return parsed, err == nil && parsed <= maximum
}
func fail(code string) map[string]any { return map[string]any{"ok":false,"error":code} }
func (g *game) draw() int {
    g.rng ^= g.rng << 13; g.rng ^= g.rng >> 17; g.rng ^= g.rng << 5
    // @if 4
    if g.rng % 16 == 15 { return 5 }
    // @end
    return int(g.rng % 5)
}
func (g *game) level() uint64 { return 1 + g.lines/4 }
func (g *game) interval() uint64 {
    reduction := 45 * (g.level()-1)
    if reduction >= 510 { return 90 }; return 600-reduction
}
func (g *game) fits(p *piece) bool {
    for _, c := range p.cells {
        x, y := p.x+c.x, p.y+c.y
        if x < 0 || x >= 10 || y < 0 || y >= 18 || g.board[y][x] { return false }
    }
    return true
}
func (g *game) spawn(kind int) {
    p := &piece{kind:kind, x:4, y:0, cells:append([]cell(nil), shapes[kind]...)}
    if g.fits(p) { g.active = p } else {
        g.phase = "over"; g.active = nil
        // @if 3
        g.holdAvailable = false
        // @end
    }
}
func (g *game) nextKind() int {
    // @if 3
    if len(g.preview)>0 {
        kind := g.preview[0]
        g.preview = append(g.preview[1:], g.draw())
        return kind
    }
    // @end
    return g.draw()
}
func (g *game) start(seed uint32) {
    *g = idle(); g.phase = "playing"; g.rng = seed
    if seed == 0 { g.rng = 2463534242 }
    kind := g.draw()
    // @if 3
    for range 3 { g.preview = append(g.preview, g.draw()) }
    g.holdAvailable = true
    // @end
    g.spawn(kind)
}
func (g *game) lock() {
    p := g.active; g.active = nil; g.credit = 0
    // @if 4
    if p.kind == 5 {
        erased := uint64(0)
        for y := max(0,p.y+1); y <= min(17,p.y+3); y++ {
            for x := max(0,p.x-1); x <= min(9,p.x+1); x++ {
                if g.board[y][x] { erased++ }; g.board[y][x] = false
            }
        }
        g.score += 11+3*erased
    } else {
    // @end
    for _, c := range p.cells { g.board[p.y+c.y][p.x+c.x] = true }
    g.score += 7
    // @if 4
    }
    // @end
    oldLevel := g.level(); cleared := uint64(0); dest := 17
    var board [18][10]bool
    for y := 17; y >= 0; y-- {
        full := true
        for _, occupied := range g.board[y] { if !occupied { full = false; break } }
        if full { cleared++ } else { board[dest] = g.board[y]; dest-- }
    }
    g.board = board; g.score += 80*cleared*cleared*oldLevel; g.lines += cleared
    // @if 5
    if g.mode == "rush" && g.lines >= 4 {
        g.phase = "won"; g.holdAvailable = false; return
    }
    // @end
    // @if 3
    g.holdAvailable = true
    // @end
    g.spawn(g.nextKind())
}
func (g *game) translate(dx, dy int) bool {
    p := *g.active; p.x += dx; p.y += dy
    if !g.fits(&p) { return false }; g.active = &p; return true
}
func (g *game) rotate() {
    p := *g.active
    // @if 4
    if p.kind == 5 { return }
    // @end
    h := 0
    for _, c := range p.cells { h = max(h,c.y+1) }
    p.cells = make([]cell,len(p.cells)); minX, minY := 100,100
    for i, c := range g.active.cells { p.cells[i] = cell{h-1-c.y,c.x}; minX = min(minX,p.cells[i].x); minY = min(minY,p.cells[i].y) }
    for i := range p.cells { p.cells[i].x -= minX; p.cells[i].y -= minY }
    if g.fits(&p) { g.active = &p }
}
func (g *game) playable() string {
    switch g.phase {
    case "idle": return "not_started"
    // @if 2
    case "paused": return "paused"
    // @end
    case "playing": return ""
    default: return "finished"
    }
}
func (g *game) tick(ms uint64) string {
    if err := g.playable(); err != "" { return err }
    // @if 5
    g.elapsedMS += ms
    // @end
    g.credit += ms
    for g.phase == "playing" && g.credit >= g.interval() {
        g.credit -= g.interval()
        if !g.translate(0,1) { g.lock() }
    }
    return ""
}
// @if 2
func (g *game) pause(resume bool) string {
    if g.phase == "idle" { return "not_started" }
    if g.phase == "over" || g.phase == "won" { return "finished" }
    if resume { g.phase = "playing" } else { g.phase = "paused" }
    return ""
}
// @end
// @if 3
func (g *game) hold() string {
    if !g.holdAvailable { return "hold_used" }
    outgoing := g.active.kind
    var incoming int
    if g.held == nil { incoming = g.nextKind() } else { incoming = *g.held }
    g.held = &outgoing; g.credit = 0; g.holdAvailable = false; g.spawn(incoming)
    return ""
}
// @end
func validKey(key string) bool {
    switch key {
    case "left", "right", "rotate", "soft", "hard": return true
    // @if 3
    case "hold": return true
    // @end
    default: return false
    }
}
func (g *game) input(key string) string {
    if err := g.playable(); err != "" { return err }
    switch key {
    case "left": g.translate(-1,0)
    case "right": g.translate(1,0)
    case "rotate": g.rotate()
    case "soft": if g.translate(0,1) { g.score++ } else { g.lock() }
    case "hard": for g.translate(0,1) { g.score += 2 }; g.lock()
    // @if 3
    case "hold": return g.hold()
    // @end
    }
    return ""
}
func (g *game) snapshot() map[string]any {
    board := make([]string,18)
    for y, row := range g.board {
        var s strings.Builder
        for _, b := range row { if b { s.WriteByte('#') } else { s.WriteByte('.') } }
        board[y] = s.String()
    }
    var active any
    if g.active != nil {
        p := g.active; cells := make([][2]int,len(p.cells))
        for i,c := range p.cells { cells[i] = [2]int{p.x+c.x,p.y+c.y} }
        sort.Slice(cells,func(i,j int) bool { if cells[i][1] == cells[j][1] { return cells[i][0]<cells[j][0] }; return cells[i][1]<cells[j][1] })
        active = map[string]any{"kind":names[p.kind],"cells":cells}
    }
    result := map[string]any{"phase":g.phase,"board":board,"active":active,"score":g.score,"lines":g.lines,"level":g.level()}
    // @if 3
    var held any
    if g.held != nil { held = names[*g.held] }
    preview := make([]string,len(g.preview))
    for i,k := range g.preview { preview[i] = names[k] }
    result["held"] = held; result["preview"] = preview; result["hold_available"] = g.holdAvailable
    // @end
    // @if 5
    result["mode"] = g.mode; result["elapsed_ms"] = g.elapsedMS
    // @end
    return result
}
// @if 6
type event struct { at uint64; key string }
func (g *game) replay(doc any) string {
    m := object(doc)
    if !members(m,[]string{"seed","mode","events","end_ms"},nil) { return "bad_replay" }
    seed, seedOK := integer(m["seed"],4294967295)
    end, endOK := integer(m["end_ms"],1000000)
    mode := text(m["mode"])
    events, eventsOK := m["events"].([]any)
    if !seedOK || !endOK || (mode != "endless" && mode != "rush") || !eventsOK || len(events)>4096 { return "bad_replay" }
    previous := uint64(0); validated := make([]event,0,len(events))
    for _, raw := range events {
        e := object(raw)
        if !members(e,[]string{"at_ms","key"},nil) { return "bad_replay" }
        at, ok := integer(e["at_ms"],1000000); key := text(e["key"])
        if !ok || at < previous || at > end || (!validKey(key) && key != "pause" && key != "resume") { return "bad_replay" }
        validated = append(validated,event{at,key}); previous = at
    }
    fresh := idle(); fresh.start(uint32(seed)); fresh.mode = mode; previous = 0
    for _, e := range validated {
        fresh.tick(e.at-previous)
        if e.key == "pause" { fresh.pause(false) } else if e.key == "resume" { fresh.pause(true) } else { fresh.input(e.key) }
        previous = e.at
    }
    fresh.tick(end-previous); *g = fresh; return ""
}
// @end
func (g *game) command(value any) map[string]any {
    m := object(value)
    cmd, ok := m["cmd"].(string)
    if !ok { return fail("bad_request") }
    err := ""
    switch cmd {
    case "state":
        if !members(m,[]string{"cmd"},nil) { return fail("bad_request") }
        return map[string]any{"ok":true,"state":g.snapshot()}
    case "new":
        optional := []string{
            // @if 5
            "mode",
            // @end
        }
        if !members(m,[]string{"cmd","seed"},optional) { return fail("bad_request") }
        seed, ok := integer(m["seed"],4294967295); if !ok { return fail("bad_request") }
        // @if 5
        mode := "endless"
        if raw, exists := m["mode"]; exists { mode = text(raw); if mode != "endless" && mode != "rush" { return fail("bad_request") } }
        // @end
        g.start(uint32(seed))
        // @if 5
        g.mode = mode
        // @end
    case "tick":
        if !members(m,[]string{"cmd","ms"},nil) { return fail("bad_request") }
        ms, ok := integer(m["ms"],1000000); if !ok { return fail("bad_request") }; err = g.tick(ms)
    case "input":
        if !members(m,[]string{"cmd","key"},nil) { return fail("bad_request") }
        key := text(m["key"]); if !validKey(key) { return fail("bad_request") }; err = g.input(key)
    // @if 2
    case "pause", "resume":
        if !members(m,[]string{"cmd"},nil) { return fail("bad_request") }; err = g.pause(cmd=="resume")
    // @end
    // @if 6
    case "replay":
        if !members(m,[]string{"cmd","document"},nil) { return fail("bad_request") }; err = g.replay(m["document"])
    // @end
    default: err = "unknown_command"
    }
    if err != "" { return fail(err) }; return map[string]any{"ok":true}
}
func decode(line string) (any, error) {
    d := json.NewDecoder(strings.NewReader(line)); d.UseNumber()
    var v any
    if err := d.Decode(&v); err != nil { return nil,err }
    var extra any
    if err := d.Decode(&extra); err != io.EOF { if err == nil { return nil,io.ErrUnexpectedEOF }; return nil,err }
    return v,nil
}
func main() {
    in := bufio.NewReader(os.Stdin); out := bufio.NewWriter(os.Stdout); g := idle()
    for {
        line, err := in.ReadString('\n')
        if len(line)>0 {
            value, parseErr := decode(line)
            reply := fail("bad_json"); if parseErr == nil { reply = g.command(value) }
            if json.NewEncoder(out).Encode(reply) != nil || out.Flush() != nil { return }
        }
        if err != nil { return }
    }
}
'''


def project(path, lang, source):
    path.mkdir(parents=True, exist_ok=True)
    if lang == 'rust':
        (path/'src').mkdir(exist_ok=True)
        (path/'src/main.rs').write_text(source)
        (path/'Cargo.toml').write_text('[package]\nname = "driftfall"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\nserde_json = "1"\n')
        ci = 'cargo fmt --check\ncargo clippy --offline -- -D warnings\ncargo test --offline'
    else:
        (path/'main.go').write_text(source)
        (path/'go.mod').write_text('module driftfall\n\ngo 1.22\n')
        ci = 'test -z "$(gofmt -l .)"\ngo vet ./...\ngo test ./...'
    (path/'README.md').write_text('# Driftfall\n\nCI commands (run in this directory):\n\n```sh\n'+ci+'\n```\n\nBuild offline and run the binary as a JSON-lines process.\n')


def main():
    for lang, template in [('rust',RUST),('go',GO)]:
        project(ROOT/'fixture'/lang,lang,'fn main() {}\n' if lang=='rust' else 'package main\n\nfunc main() {}\n')
        for step in range(1,7):
            project(ROOT/'ref'/lang/f'f{step}',lang,select(template,step))
    # A bounded omission: the held-piece consumer still assumes five kinds.
    missed4 = select(RUST,4).replace('self.spawn(incoming);','self.spawn(if incoming == 5 { 0 } else { incoming });')
    project(ROOT/'ref_missed/rust/f4','rust',missed4)
    # A plausible event validator checks bounds but forgets monotonicity.
    missed6 = select(RUST,6).replace('if at < previous || at > end {', 'if at > end {').replace('let mut previous = 0;\n        let mut validated', 'let mut validated').replace('validated.push((at, key)); previous = at;', 'validated.push((at, key));').replace('previous = 0;\n        for (at, key)', 'let mut previous = 0;\n        for (at, key)').replace('fresh.tick(at - previous)', 'fresh.tick(at.saturating_sub(previous))')
    project(ROOT/'ref_missed/rust/f6','rust',missed6)
    for manifest in ROOT.glob('**/Cargo.toml'):
        subprocess.run(['cargo','fmt','--manifest-path',str(manifest)],check=True)
    for source in ROOT.glob('**/main.go'):
        subprocess.run(['gofmt','-w',str(source)],check=True)

if __name__ == '__main__':
    main()

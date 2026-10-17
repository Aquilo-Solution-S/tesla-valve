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

type cell struct{ x, y int }
type piece struct {
	kind, x, y int
	cells      []cell
}

var shapes = [][]cell{
	{{0, 0}, {0, 1}, {1, 1}},
	{{0, 0}, {1, 0}, {2, 0}, {1, 1}, {1, 2}},
	{{0, 0}, {0, 1}, {1, 1}, {1, 2}, {2, 2}},
	{{0, 0}, {2, 0}, {0, 1}, {1, 1}, {2, 1}},
	{{0, 0}, {0, 1}, {0, 2}, {0, 3}, {1, 3}},
	{{0, 0}, {0, 1}, {0, 2}},
}
var names = []string{
	"sprig", "prong", "ramp", "arch", "reed",
	"pulse",
}

type game struct {
	board                [18][10]bool
	phase                string
	active               *piece
	rng                  uint32
	score, lines, credit uint64
	held                 *int
	preview              []int
	holdAvailable        bool
	mode                 string
	elapsedMS            uint64
}

func idle() game {
	g := game{phase: "idle"}
	g.mode = "endless"
	return g
}
func object(v any) map[string]any { m, _ := v.(map[string]any); return m }
func text(v any) string           { s, _ := v.(string); return s }
func members(m map[string]any, required, optional []string) bool {
	if m == nil {
		return false
	}
	allowed := make(map[string]bool)
	for _, k := range required {
		if _, ok := m[k]; !ok {
			return false
		}
		allowed[k] = true
	}
	for _, k := range optional {
		allowed[k] = true
	}
	for k := range m {
		if !allowed[k] {
			return false
		}
	}
	return true
}
func integer(v any, maximum uint64) (uint64, bool) {
	n, ok := v.(json.Number)
	if !ok {
		return 0, false
	}
	parsed, err := strconv.ParseUint(string(n), 10, 64)
	return parsed, err == nil && parsed <= maximum
}
func fail(code string) map[string]any { return map[string]any{"ok": false, "error": code} }
func (g *game) draw() int {
	g.rng ^= g.rng << 13
	g.rng ^= g.rng >> 17
	g.rng ^= g.rng << 5
	if g.rng%16 == 15 {
		return 5
	}
	return int(g.rng % 5)
}
func (g *game) level() uint64 { return 1 + g.lines/4 }
func (g *game) interval() uint64 {
	reduction := 45 * (g.level() - 1)
	if reduction >= 510 {
		return 90
	}
	return 600 - reduction
}
func (g *game) fits(p *piece) bool {
	for _, c := range p.cells {
		x, y := p.x+c.x, p.y+c.y
		if x < 0 || x >= 10 || y < 0 || y >= 18 || g.board[y][x] {
			return false
		}
	}
	return true
}
func (g *game) spawn(kind int) {
	p := &piece{kind: kind, x: 4, y: 0, cells: append([]cell(nil), shapes[kind]...)}
	if g.fits(p) {
		g.active = p
	} else {
		g.phase = "over"
		g.active = nil
		g.holdAvailable = false
	}
}
func (g *game) nextKind() int {
	if len(g.preview) > 0 {
		kind := g.preview[0]
		g.preview = append(g.preview[1:], g.draw())
		return kind
	}
	return g.draw()
}
func (g *game) start(seed uint32) {
	*g = idle()
	g.phase = "playing"
	g.rng = seed
	if seed == 0 {
		g.rng = 2463534242
	}
	kind := g.draw()
	for range 3 {
		g.preview = append(g.preview, g.draw())
	}
	g.holdAvailable = true
	g.spawn(kind)
}
func (g *game) lock() {
	p := g.active
	g.active = nil
	g.credit = 0
	if p.kind == 5 {
		erased := uint64(0)
		for y := max(0, p.y+1); y <= min(17, p.y+3); y++ {
			for x := max(0, p.x-1); x <= min(9, p.x+1); x++ {
				if g.board[y][x] {
					erased++
				}
				g.board[y][x] = false
			}
		}
		g.score += 11 + 3*erased
	} else {
		for _, c := range p.cells {
			g.board[p.y+c.y][p.x+c.x] = true
		}
		g.score += 7
	}
	oldLevel := g.level()
	cleared := uint64(0)
	dest := 17
	var board [18][10]bool
	for y := 17; y >= 0; y-- {
		full := true
		for _, occupied := range g.board[y] {
			if !occupied {
				full = false
				break
			}
		}
		if full {
			cleared++
		} else {
			board[dest] = g.board[y]
			dest--
		}
	}
	g.board = board
	g.score += 80 * cleared * cleared * oldLevel
	g.lines += cleared
	if g.mode == "rush" && g.lines >= 4 {
		g.phase = "won"
		g.holdAvailable = false
		return
	}
	g.holdAvailable = true
	g.spawn(g.nextKind())
}
func (g *game) translate(dx, dy int) bool {
	p := *g.active
	p.x += dx
	p.y += dy
	if !g.fits(&p) {
		return false
	}
	g.active = &p
	return true
}
func (g *game) rotate() {
	p := *g.active
	if p.kind == 5 {
		return
	}
	h := 0
	for _, c := range p.cells {
		h = max(h, c.y+1)
	}
	p.cells = make([]cell, len(p.cells))
	minX, minY := 100, 100
	for i, c := range g.active.cells {
		p.cells[i] = cell{h - 1 - c.y, c.x}
		minX = min(minX, p.cells[i].x)
		minY = min(minY, p.cells[i].y)
	}
	for i := range p.cells {
		p.cells[i].x -= minX
		p.cells[i].y -= minY
	}
	if g.fits(&p) {
		g.active = &p
	}
}
func (g *game) playable() string {
	switch g.phase {
	case "idle":
		return "not_started"
	case "paused":
		return "paused"
	case "playing":
		return ""
	default:
		return "finished"
	}
}
func (g *game) tick(ms uint64) string {
	if err := g.playable(); err != "" {
		return err
	}
	g.elapsedMS += ms
	g.credit += ms
	for g.phase == "playing" && g.credit >= g.interval() {
		g.credit -= g.interval()
		if !g.translate(0, 1) {
			g.lock()
		}
	}
	return ""
}
func (g *game) pause(resume bool) string {
	if g.phase == "idle" {
		return "not_started"
	}
	if g.phase == "over" || g.phase == "won" {
		return "finished"
	}
	if resume {
		g.phase = "playing"
	} else {
		g.phase = "paused"
	}
	return ""
}
func (g *game) hold() string {
	if !g.holdAvailable {
		return "hold_used"
	}
	outgoing := g.active.kind
	var incoming int
	if g.held == nil {
		incoming = g.nextKind()
	} else {
		incoming = *g.held
	}
	g.held = &outgoing
	g.credit = 0
	g.holdAvailable = false
	g.spawn(incoming)
	return ""
}
func validKey(key string) bool {
	switch key {
	case "left", "right", "rotate", "soft", "hard":
		return true
	case "hold":
		return true
	default:
		return false
	}
}
func (g *game) input(key string) string {
	if err := g.playable(); err != "" {
		return err
	}
	switch key {
	case "left":
		g.translate(-1, 0)
	case "right":
		g.translate(1, 0)
	case "rotate":
		g.rotate()
	case "soft":
		if g.translate(0, 1) {
			g.score++
		} else {
			g.lock()
		}
	case "hard":
		for g.translate(0, 1) {
			g.score += 2
		}
		g.lock()
	case "hold":
		return g.hold()
	}
	return ""
}
func (g *game) snapshot() map[string]any {
	board := make([]string, 18)
	for y, row := range g.board {
		var s strings.Builder
		for _, b := range row {
			if b {
				s.WriteByte('#')
			} else {
				s.WriteByte('.')
			}
		}
		board[y] = s.String()
	}
	var active any
	if g.active != nil {
		p := g.active
		cells := make([][2]int, len(p.cells))
		for i, c := range p.cells {
			cells[i] = [2]int{p.x + c.x, p.y + c.y}
		}
		sort.Slice(cells, func(i, j int) bool {
			if cells[i][1] == cells[j][1] {
				return cells[i][0] < cells[j][0]
			}
			return cells[i][1] < cells[j][1]
		})
		active = map[string]any{"kind": names[p.kind], "cells": cells}
	}
	result := map[string]any{"phase": g.phase, "board": board, "active": active, "score": g.score, "lines": g.lines, "level": g.level()}
	var held any
	if g.held != nil {
		held = names[*g.held]
	}
	preview := make([]string, len(g.preview))
	for i, k := range g.preview {
		preview[i] = names[k]
	}
	result["held"] = held
	result["preview"] = preview
	result["hold_available"] = g.holdAvailable
	result["mode"] = g.mode
	result["elapsed_ms"] = g.elapsedMS
	return result
}
func (g *game) command(value any) map[string]any {
	m := object(value)
	cmd, ok := m["cmd"].(string)
	if !ok {
		return fail("bad_request")
	}
	err := ""
	switch cmd {
	case "state":
		if !members(m, []string{"cmd"}, nil) {
			return fail("bad_request")
		}
		return map[string]any{"ok": true, "state": g.snapshot()}
	case "new":
		optional := []string{
			"mode",
		}
		if !members(m, []string{"cmd", "seed"}, optional) {
			return fail("bad_request")
		}
		seed, ok := integer(m["seed"], 4294967295)
		if !ok {
			return fail("bad_request")
		}
		mode := "endless"
		if raw, exists := m["mode"]; exists {
			mode = text(raw)
			if mode != "endless" && mode != "rush" {
				return fail("bad_request")
			}
		}
		g.start(uint32(seed))
		g.mode = mode
	case "tick":
		if !members(m, []string{"cmd", "ms"}, nil) {
			return fail("bad_request")
		}
		ms, ok := integer(m["ms"], 1000000)
		if !ok {
			return fail("bad_request")
		}
		err = g.tick(ms)
	case "input":
		if !members(m, []string{"cmd", "key"}, nil) {
			return fail("bad_request")
		}
		key := text(m["key"])
		if !validKey(key) {
			return fail("bad_request")
		}
		err = g.input(key)
	case "pause", "resume":
		if !members(m, []string{"cmd"}, nil) {
			return fail("bad_request")
		}
		err = g.pause(cmd == "resume")
	default:
		err = "unknown_command"
	}
	if err != "" {
		return fail(err)
	}
	return map[string]any{"ok": true}
}
func decode(line string) (any, error) {
	d := json.NewDecoder(strings.NewReader(line))
	d.UseNumber()
	var v any
	if err := d.Decode(&v); err != nil {
		return nil, err
	}
	var extra any
	if err := d.Decode(&extra); err != io.EOF {
		if err == nil {
			return nil, io.ErrUnexpectedEOF
		}
		return nil, err
	}
	return v, nil
}
func main() {
	in := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	g := idle()
	for {
		line, err := in.ReadString('\n')
		if len(line) > 0 {
			value, parseErr := decode(line)
			reply := fail("bad_json")
			if parseErr == nil {
				reply = g.command(value)
			}
			if json.NewEncoder(out).Encode(reply) != nil || out.Flush() != nil {
				return
			}
		}
		if err != nil {
			return
		}
	}
}

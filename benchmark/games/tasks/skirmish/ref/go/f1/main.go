package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strconv"
)

var field = []string{".........", "..ss..#..", ".s.#..#..", "...#ss...", ".##...##.", "...ss#...", "..#..#.s.", "..#..ss..", "........."}

type Unit struct {
	ID    int64          `json:"id"`
	Owner int64          `json:"owner"`
	Kind  string         `json:"kind"`
	X     int64          `json:"x"`
	Y     int64          `json:"y"`
	HP    int64          `json:"hp"`
	Order map[string]any `json:"order"`
}
type Game struct {
	Turn   int64   `json:"turn"`
	Phase  string  `json:"phase"`
	Winner *int64  `json:"winner"`
	Ended  []int64 `json:"ended"`
	Units  []Unit  `json:"units"`
}
type Facts struct {
	HP, Attack, Range, Movement int64
}

func facts(kind string) (Facts, bool) {
	var f Facts
	switch kind {
	case "lancer":
		f.HP, f.Attack, f.Range, f.Movement = 8, 3, 1, 3
	case "bolt":
		f.HP, f.Attack, f.Range, f.Movement = 6, 2, 3, 2
	case "glider":
		f.HP, f.Attack, f.Range, f.Movement = 5, 2, 2, 4
	default:
		return f, false
	}
	return f, true
}
func object(v any) map[string]any { m, _ := v.(map[string]any); return m }
func keys(v any, names ...string) bool {
	m := object(v)
	if m == nil || len(m) != len(names) {
		return false
	}
	for _, k := range names {
		if _, ok := m[k]; !ok {
			return false
		}
	}
	return true
}
func number(v any) (int64, bool) {
	n, ok := v.(json.Number)
	if !ok {
		return 0, false
	}
	i, e := strconv.ParseInt(string(n), 10, 64)
	return i, e == nil
}
func integer(v any, lo, hi int64) bool { n, ok := number(v); return ok && n >= lo && n <= hi }
func value(v any) int64                { n, _ := number(v); return n }
func abs(n int64) int64 {
	if n < 0 {
		return -n
	}
	return n
}
func distance(x, y, a, b int64) int64 { return abs(x-a) + abs(y-b) }
func tile(x, y int64) byte            { return field[y][x] }
func stand(kind string, x, y int64) bool {
	if x < 0 || x >= 9 || y < 0 || y >= 9 {
		return false
	}
	return tile(x, y) != '#'
}
func orderShape(v any) bool {
	m := object(v)
	if m == nil {
		return false
	}
	switch m["type"] {
	case "hold":
		return keys(v, "type")
	case "move":
		a, ok := m["to"].([]any)
		return keys(v, "type", "to") && ok && len(a) == 2 && integer(a[0], 0, 8) && integer(a[1], 0, 8)
	case "attack":
		return keys(v, "type", "target") && integer(m["target"], 1, 99)
	}
	return false
}
func idle() Game { return Game{Phase: "idle", Ended: []int64{}, Units: []Unit{}} }
func (g Game) clone() Game {
	g.Units = append([]Unit{}, g.Units...)
	g.Ended = append([]int64{}, g.Ended...)
	return g
}
func (g Game) index(id int64) int {
	for i, u := range g.Units {
		if u.ID == id {
			return i
		}
	}
	return -1
}
func (g Game) visible(p int64, v Unit) bool {
	return true
}
func (g Game) route(u Unit, x, y int64) bool {
	if (u.X == x && u.Y == y) || !stand(u.Kind, x, y) {
		return false
	}
	f, _ := facts(u.Kind)
	return distance(u.X, u.Y, x, y) <= f.Movement
}
func (g Game) moveAllowed(u Unit, x, y int64) bool {
	if !g.route(u, x, y) {
		return false
	}
	for _, v := range g.Units {
		if v.ID != u.ID && v.X == x && v.Y == y && g.visible(u.Owner, v) {
			return false
		}
	}
	return true
}
func (g Game) damage(u, v Unit) int64 {
	f, _ := facts(u.Kind)
	return f.Attack
}
func (g Game) interaction(u Unit, target int64) (string, int64, string) {
	i := g.index(target)
	if i < 0 || !g.visible(u.Owner, g.Units[i]) {
		return "", 0, "unavailable"
	}
	v := g.Units[i]
	f, _ := facts(u.Kind)
	if u.ID == v.ID || u.Owner == v.Owner || distance(u.X, u.Y, v.X, v.Y) > f.Range {
		return "", 0, "invalid_order"
	}
	return "damage", g.damage(u, v), ""
}
func (g Game) validOrder(u Unit, o map[string]any) string {
	switch o["type"] {
	case "move":
		a := o["to"].([]any)
		if !g.moveAllowed(u, value(a[0]), value(a[1])) {
			return "invalid_order"
		}
	case "attack":
		_, _, e := g.interaction(u, value(o["target"]))
		return e
	}
	return ""
}
func (g *Game) resolve() {
	n := len(g.Units)
	dest := make([][2]int64, n)
	moving := make([]bool, n)
	for i, u := range g.Units {
		if u.Order["type"] == "move" {
			a := u.Order["to"].([]any)
			dest[i] = [2]int64{value(a[0]), value(a[1])}
			moving[i] = true
		}
	}
	proposed := append([]bool{}, moving...)
	for i, u := range g.Units {
		if proposed[i] {
			for j, v := range g.Units {
				if i == j || !proposed[j] {
					continue
				}
				if dest[i] == dest[j] || (dest[i] == [2]int64{v.X, v.Y} && dest[j] == [2]int64{u.X, u.Y}) {
					moving[i] = false
				}
			}
		}
	}
	for {
		changed := false
		for i := range g.Units {
			if moving[i] {
				for j, v := range g.Units {
					if dest[i] == [2]int64{v.X, v.Y} && !moving[j] {
						moving[i] = false
						changed = true
						break
					}
				}
			}
		}
		if !changed {
			break
		}
	}
	for i := range g.Units {
		if moving[i] {
			g.Units[i].X = dest[i][0]
			g.Units[i].Y = dest[i][1]
		}
	}
	hits := make([]int64, n)
	for _, u := range g.Units {
		if u.Order["type"] == "attack" {
			j := g.index(value(u.Order["target"]))
			if j < 0 {
				continue
			}
			v := g.Units[j]
			f, _ := facts(u.Kind)
			if u.Owner != v.Owner && distance(u.X, u.Y, v.X, v.Y) <= f.Range {
				hits[j] += g.damage(u, v)
			}
		}
	}
	survivors := []Unit{}
	a, b := false, false
	for i, u := range g.Units {
		u.HP -= hits[i]
		u.Order = nil
		if u.HP > 0 {
			survivors = append(survivors, u)
			a = a || u.Owner == 1
			b = b || u.Owner == 2
		}
	}
	g.Units = survivors
	g.Turn++
	g.Ended = []int64{}
	if !a || !b {
		g.Phase = "finished"
		w := int64(0)
		if a {
			w = 1
		} else if b {
			w = 2
		}
		g.Winner = &w
	}
}
func deployment(v any) ([]Unit, string) {
	a, ok := v.([]any)
	if !ok || len(a) < 2 || len(a) > 20 {
		return nil, "bad_request"
	}
	units := []Unit{}
	one, two := false, false
	for _, raw := range a {
		r := object(raw)
		if !keys(raw, "id", "owner", "kind", "x", "y") || !integer(r["id"], 1, 99) || !integer(r["owner"], 1, 2) || !integer(r["x"], 0, 8) || !integer(r["y"], 0, 8) {
			return nil, "bad_request"
		}
		k, ok := r["kind"].(string)
		f, known := facts(k)
		x, y, id, p := value(r["x"]), value(r["y"]), value(r["id"]), value(r["owner"])
		if !ok || !known || !stand(k, x, y) {
			return nil, "bad_request"
		}
		for _, u := range units {
			if u.ID == id || (u.X == x && u.Y == y) {
				return nil, "bad_request"
			}
		}
		units = append(units, Unit{ID: id, Owner: p, Kind: k, X: x, Y: y, HP: f.HP})
		one = one || p == 1
		two = two || p == 2
	}
	if !one || !two {
		return nil, "bad_request"
	}
	// Small deployments: insertion sort keeps the snapshot's canonical order.
	for i := 1; i < len(units); i++ {
		for j := i; j > 0 && units[j].ID < units[j-1].ID; j-- {
			units[j], units[j-1] = units[j-1], units[j]
		}
	}
	return units, ""
}
func (g *Game) dispatch(r map[string]any) (map[string]any, string) {
	cmd, ok := r["cmd"].(string)
	if !ok {
		return nil, "bad_request"
	}
	shape := false
	switch cmd {
	case "new":
		shape = keys(r, "cmd") || keys(r, "cmd", "units")
	case "state":
		shape = keys(r, "cmd")
	case "order":
		shape = keys(r, "cmd", "player", "unit", "order") && orderShape(r["order"])
	case "end_turn":
		shape = keys(r, "cmd", "player")
	case "reachable":
		shape = keys(r, "cmd", "player", "unit")
	case "forecast":
		shape = keys(r, "cmd", "player", "unit", "target") && integer(r["target"], 1, 99)
	default:
		return nil, "unknown_command"
	}
	if !shape {
		return nil, "bad_request"
	}
	if p, ok := r["player"]; ok && !integer(p, 1, 2) {
		return nil, "bad_request"
	}
	if u, ok := r["unit"]; ok && !integer(u, 1, 99) {
		return nil, "bad_request"
	}
	success := map[string]any{"ok": true}
	switch cmd {
	case "state":
		return map[string]any{"ok": true, "state": g.clone()}, ""
	case "new":
		v, ok := r["units"]
		if !ok {
			defaults := `[{"id":1,"owner":1,"kind":"lancer","x":1,"y":0},{"id":2,"owner":1,"kind":"bolt","x":4,"y":0},{"id":3,"owner":1,"kind":"glider","x":7,"y":0},{"id":11,"owner":2,"kind":"lancer","x":1,"y":8},{"id":12,"owner":2,"kind":"bolt","x":4,"y":8},{"id":13,"owner":2,"kind":"glider","x":7,"y":8}]`
			dec := json.NewDecoder(bytes.NewBufferString(defaults))
			dec.UseNumber()
			_ = dec.Decode(&v)
		}
		us, e := deployment(v)
		if e != "" {
			return nil, e
		}
		*g = Game{Turn: 1, Phase: "planning", Ended: []int64{}, Units: us}
		return success, ""
	}
	if g.Phase == "idle" {
		return nil, "not_started"
	}
	if g.Phase == "finished" {
		return nil, "finished"
	}
	p := value(r["player"])
	if cmd == "order" || cmd == "end_turn" {
		for _, e := range g.Ended {
			if e == p {
				return nil, "turn_ended"
			}
		}
	}
	if cmd == "end_turn" {
		g.Ended = append(g.Ended, p)
		if len(g.Ended) == 2 {
			g.resolve()
		}
		return success, ""
	}
	i := g.index(value(r["unit"]))
	if i < 0 || g.Units[i].Owner != p {
		return nil, "unavailable"
	}
	u := g.Units[i]
	switch cmd {
	case "order":
		o := object(r["order"])
		if e := g.validOrder(u, o); e != "" {
			return nil, e
		}
		g.Units[i].Order = o
		return success, ""
	case "reachable":
		cells := [][2]int64{}
		for y := int64(0); y < 9; y++ {
			for x := int64(0); x < 9; x++ {
				if g.moveAllowed(u, x, y) {
					cells = append(cells, [2]int64{x, y})
				}
			}
		}
		return map[string]any{"ok": true, "cells": cells}, ""
	case "forecast":
		effect, amount, e := g.interaction(u, value(r["target"]))
		if e != "" {
			return nil, e
		}
		return map[string]any{"ok": true, "effect": effect, "amount": amount}, ""
	}
	panic("validated command has no handler")
}
func main() {
	g := idle()
	reader := bufio.NewReader(os.Stdin)
	out := bufio.NewWriter(os.Stdout)
	for {
		line, readErr := reader.ReadBytes('\n')
		if len(line) == 0 && readErr != nil {
			break
		}
		var v any
		dec := json.NewDecoder(bytes.NewReader(line))
		dec.UseNumber()
		e := ""
		var reply map[string]any
		if dec.Decode(&v) != nil {
			e = "bad_json"
		} else {
			var extra any
			if dec.Decode(&extra) != io.EOF {
				e = "bad_json"
			} else if object(v) == nil {
				e = "bad_request"
			} else {
				next := g.clone()
				reply, e = next.dispatch(object(v))
				if e == "" {
					g = next
				}
			}
		}
		if e != "" {
			reply = map[string]any{"ok": false, "error": e}
		}
		b, _ := json.Marshal(reply)
		if _, err := fmt.Fprintln(out, string(b)); err != nil {
			break
		}
		if out.Flush() != nil {
			break
		}
		if readErr != nil {
			break
		}
	}
}

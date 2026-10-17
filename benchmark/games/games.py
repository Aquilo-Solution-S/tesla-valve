"""Game-evolution benchmark: does the code an arm writes carry six steps of a growing game?

A cell is one game, one language, one arm, one model, one run. The language fixture is copied into
a fresh repo; steps f1..f6 run in order, spec.md grows by that step's section first, and each step
is a fresh agent session followed by the language's CI with one fix round (agents.session_with_ci).
After every step the harness builds the binary and runs the hidden tests of ALL steps so far, so a
regression shows in the step that made it.

Arms: `baseline` (no rules), `tesla-valve` (this repository's rules at every step, as the installed
plugin delivers them), or the path of another plugin directory with an AGENTS.md. A suffix `@first`
gives the rules to step 1 only; the later sessions run without them.

  python3 games.py --games driftfall,skirmish --langs rust,go --arms baseline,tesla-valve --models gpt-6-luna
  python3 games.py --report runs/<stamp>
"""
import argparse
import collections
import concurrent.futures
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import agents

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TASKS, RUNS = HERE / "tasks", HERE / "runs"

STEPS = 6
CI = {"rust": [["cargo", "fmt", "--check"], ["cargo", "clippy", "--offline", "--", "-D", "warnings"],
               ["cargo", "test", "--offline"]],
      "go": [["sh", "-c", 'test -z "$(gofmt -l .)" || { echo "gofmt needed:"; gofmt -l .; exit 1; }'],
             ["go", "vet", "./..."], ["go", "test", "./..."]]}
SRC = {"rust": ".rs", "go": ".go"}
# RUSTC_WRAPPER="": a machine-wide sccache cannot start inside the sandbox, and a shared cache would couple cells
TOOLCHAIN_ENV = {"GOCACHE": str(HERE / ".gocache"), "GOTOOLCHAIN": "local", "CARGO_NET_OFFLINE": "true",
                 "RUSTC_WRAPPER": ""}
# the sandboxed author must reach the toolchains' own state, or cargo cannot lock its package cache
WRITABLE = [str(Path.home() / ".cargo"), str(Path.home() / ".rustup"), TOOLCHAIN_ENV["GOCACHE"]]


def ci(lang: str):
    def check(ws: Path) -> tuple[bool, str]:
        out = []
        for cmd in CI[lang]:
            p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=900)
            if p.returncode:
                out.append(f"$ {' '.join(cmd)}\n{(p.stdout + p.stderr)[-agents.CI_CHARS:]}")
        return not out, "\n\n".join(out)
    return check


def rules_for(arm: str, step: int) -> Path | None:
    """The plugin directory whose rules the session of this step receives, or None for none."""
    name, _, scope = arm.partition("@")
    if scope not in ("", "first"):
        sys.exit(f"unknown arm scope in {arm}")
    if name == "baseline" or (scope == "first" and step > 1):
        return None
    return REPO if name == "tesla-valve" else Path(name).resolve()


def label(arm: str) -> str:
    name, _, scope = arm.partition("@")
    return (name if name in ("baseline", "tesla-valve") else Path(name).name) + (f"@{scope}" if scope else "")


def build(ws: Path, lang: str) -> Path | None:
    if lang == "go":
        exe = ws / ".bin" / "game"
        p = subprocess.run(["go", "build", "-o", str(exe), "."], cwd=ws, capture_output=True, text=True, timeout=900)
        return exe if p.returncode == 0 and exe.is_file() else None
    p = subprocess.run(["cargo", "build", "--release", "--offline", "--message-format=json"], cwd=ws,
                       capture_output=True, text=True, timeout=900)
    exes = [m["executable"] for m in map(json.loads, p.stdout.splitlines())
            if m.get("reason") == "compiler-artifact" and m.get("executable")]
    return Path(exes[-1]) if p.returncode == 0 and exes else None


def hidden(game: str, ws: Path, lang: str, upto: int) -> dict:
    """Hidden tests of steps 1..upto against the built binary, counted per step, and the failed ones by
    name. A tree that does not build runs them against a missing binary, so every test fails and the
    totals stay the same."""
    exe = build(ws, lang)
    out, failed = {f"f{k}": {"passed": 0, "total": 0} for k in range(1, upto + 1)}, []
    with tempfile.TemporaryDirectory() as d:
        xml = Path(d) / "r.xml"
        subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}",
                        *[f"test_f{k}.py" for k in range(1, upto + 1)]], cwd=TASKS / game / "hidden",
                       env={**os.environ, "GAME_BIN": str(exe or ws / ".bin" / "missing")},
                       capture_output=True, text=True, timeout=3600)
        for tc in ET.parse(xml).getroot().iter("testcase"):
            step = "f" + re.search(r"test_f(\d)", tc.get("classname", "")).group(1)
            ok = not any(c.tag in ("failure", "error", "skipped") for c in tc)
            out[step]["total"] += 1
            out[step]["passed"] += ok
            if not ok:
                failed.append(f"{tc.get('classname')}::{tc.get('name')}")
    return {"built": exe is not None, **out, "failed": sorted(failed)}


def spec_upto(game: str, k: int) -> str:
    """The spec as the project knows it before step k: the intro and sections 1..k. A requirement
    the agent cannot see yet cannot shape its design, so the steps test what the code carries."""
    text = (TASKS / game / "spec.md").read_text()
    parts = re.split(r"(?m)^(?=## \d+\. )", text)
    sections = {int(re.match(r"## (\d+)\.", s).group(1)): s for s in parts[1:]}
    if sorted(sections) != list(range(1, STEPS + 1)):
        sys.exit(f"{game}/spec.md needs sections 1..{STEPS}, has {sorted(sections)}")
    return parts[0] + "".join(sections[j] for j in range(1, k + 1))


def churn(ws: Path, lang: str) -> dict:
    agents.git(ws, "add", "-A")
    c = {"added": 0, "removed": 0, "files": 0}
    for row in agents.git(ws, "diff", "--cached", "--numstat", "HEAD").stdout.splitlines():
        added, removed, path = row.split("\t")
        if added != "-" and path.endswith(SRC[lang]):
            c["added"] += int(added)
            c["removed"] += int(removed)
            c["files"] += 1
    return c


def run_cell(game: str, lang: str, arm: str, model: str, i: int, out: Path) -> dict:
    ws = out / f"{game}__{lang}__{label(arm).replace('@', '+')}__{model}__{i}"   # as in results/: @first -> +first
    shutil.copytree(TASKS / game / "fixture" / lang, ws)
    agents.git(ws, "init", "-q")
    (ws / ".git" / "info" / "exclude").write_text(f"target/\n.bin/\n/game\n/{game}\n")   # build outputs
    agents.git(ws, "add", "-A")
    agents.git(ws, "commit", "-q", "-m", "fixture")
    rec = {"game": game, "lang": lang, "arm": label(arm), "model": model, "run": i, "steps": []}
    for k in range(1, STEPS + 1):
        (ws / "spec.md").write_text(spec_upto(game, k))
        agents.git(ws, "add", "spec.md")
        agents.git(ws, "commit", "-q", "-m", f"spec section {k}")
        prompt = (TASKS / game / "steps" / f"f{k}.md").read_text()
        rules = rules_for(arm, k)
        author = agents.Author(model, rules, WRITABLE, out / "logs" / ws.name)
        try:
            step = {"step": k, "rules": rules.name if rules else "none",
                    **agents.session_with_ci(author, prompt, ws, ci(lang))}
        finally:
            author.close()
        step["churn"] = churn(ws, lang)
        step["hidden"] = hidden(game, ws, lang, k)
        agents.git(ws, "commit", "-q", "--allow-empty", "-m", f"f{k}")
        rec["steps"].append(step)
        (out / f"{ws.name}.json").write_text(json.dumps(rec, indent=1))
    shutil.rmtree(ws / "target", ignore_errors=True)
    shutil.rmtree(ws / ".bin", ignore_errors=True)
    return rec


def green(h: dict, k: int) -> bool:
    return h[f"f{k}"]["total"] > 0 and h[f"f{k}"]["passed"] == h[f"f{k}"]["total"]


def report(recs: list[dict]):
    """Per arm: hidden pass rate over all steps so far after each step; steps that ended fully green;
    regressions (an earlier step's tests fully green before the step and not after); source churn
    of f2..f6; steps whose CI stayed red after the fix round."""
    by = collections.defaultdict(list)
    for r in recs:
        by[(r["game"], r["lang"], r["model"], r["arm"])].append(r)
    print(f"  {'game':10} {'lang':4} {'model':16} {'arm':14} {'n':>2}  {'pass rate after f1..f6':29} "
          f"{'green':>5} {'regr':>4} {'churn':>6} {'red':>3}")
    for (g, lang, m, a), xs in sorted(by.items()):
        rates = []
        for k in range(STEPS):
            hs = [x["steps"][k]["hidden"] for x in xs if k < len(x["steps"])]
            p = sum(h[f"f{j}"]["passed"] for h in hs for j in range(1, k + 2))
            t = sum(h[f"f{j}"]["total"] for h in hs for j in range(1, k + 2))
            rates.append(f"{p / t:4.0%}" if t else "   -")
        steps = [s for x in xs for s in x["steps"]]
        greens = sum(all(green(s["hidden"], j) for j in range(1, s["step"] + 1)) for s in steps)
        regr = sum(green(x["steps"][k - 1]["hidden"], j) and not green(x["steps"][k]["hidden"], j)
                   for x in xs for k in range(1, len(x["steps"])) for j in range(1, k + 1))
        ch = sum(s["churn"]["added"] + s["churn"]["removed"] for s in steps if s["step"] > 1) // len(xs)
        red = sum(s.get("ci_red_after_fix", False) for s in steps)
        print(f"  {g:10} {lang:4} {m:16} {a:14} {len(xs):>2}  {' '.join(rates):29} "
              f"{greens:>2}/{len(steps):<2} {regr:>4} {ch:>6} {red:>3}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", default="driftfall,skirmish")
    ap.add_argument("--langs", default="rust,go")
    ap.add_argument("--arms", default="baseline,tesla-valve")
    ap.add_argument("--models", default="gpt-6-luna")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.report:
        return report([json.loads(p.read_text()) for p in sorted(Path(a.report).glob("*.json"))])
    os.environ.update(TOOLCHAIN_ENV)
    out = RUNS / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    cells = [(g, lang, arm, m, i) for g in a.games.split(",") for lang in a.langs.split(",")
             for m in a.models.split(",") for arm in a.arms.split(",") for i in range(a.runs)]
    print(f"running {len(cells)} cells x {STEPS} steps, {a.workers} at a time -> {out}", flush=True)
    recs = []
    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        futs = {pool.submit(run_cell, *c, out): c for c in cells}
        for n, f in enumerate(concurrent.futures.as_completed(futs), 1):
            name = "/".join(map(str, futs[f]))
            try:
                recs.append(f.result())
                print(f"  [{n}/{len(cells)}] {name} done", flush=True)
            except Exception as e:                    # a crashed cell is reported, never scored
                print(f"  [{n}/{len(cells)}] {name} ERROR {e!r}", flush=True)
    report(recs)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

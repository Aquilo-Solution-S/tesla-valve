"""Refactoring: does Tesla Valve help an agent refactor game code it did not write? The plan, written before
the run, is refactor-plan.md.

A source is a project a published run grew without rules, as it stood after step 6. Each source is refactored
once per arm by the model that grew it: one fresh session and the project's CI with one fix round
(agents.session_with_ci). The hidden tests of all six steps run before and after, so a refactor that changes
what the program does shows as a test that passed before and fails after.

Arms: `baseline` (no rules), `tesla-valve` (the rules, as in games.py), `reshape` (the rules, and the prompt
asks the agent to follow skills/reshape/SKILL.md, with every row and slice approved in advance, because the
skill waits for the user). A cell's record is written once it is done, so pairwise.py judges the cells as
they are:

  python3 refactor.py results/20261010-1[23]* --arms baseline,tesla-valve,reshape
  python3 pairwise.py runs/refactor-<stamp> --arms baseline,tesla-valve --judge claude-sonnet-5-5
  python3 refactor.py --report runs/refactor-<stamp>
  python3 refactor.py --recheck runs/refactor-<stamp>

The hidden tests give each reply two seconds. On a machine busy with the authors and their builds, a reply can
miss that, so --recheck runs them again before and after each refactor, one cell at a time, and names every
result that differs from the recorded one.
"""
import argparse
import collections
import concurrent.futures
import datetime
import json
import os
import shutil
import tempfile
from pathlib import Path

import agents
import cost
import games

TASK = ("This project will be maintained and extended for years, by engineers who did not write it. Refactor "
        "it so that the next change is easy and safe to make. Do not change what the program does: every "
        "request must get the same reply as before. spec.md describes the game as it is now.")
RESHAPE = ("Follow the skill in {skill} for this refactor. Its scope is the whole project: work through it one "
           "stream at a time, in this session. I agree in advance to every row of your plan and to every "
           "slice, so do not stop to ask me.\n\n")
ARMS = ("baseline", "tesla-valve", "reshape")


def sources(runs: list[Path], scratch: Path) -> list[tuple[str, dict, Path]]:
    """Every baseline project that finished six steps, as (run/cell, record, clone at step 6)."""
    out = []
    for run in runs:
        here = cost.cells(run, scratch)
        for p in sorted(run.glob("*.json")):
            r = json.loads(p.read_text())
            if r["arm"] == "baseline" and len(r["steps"]) == games.STEPS:
                out.append((f"{run.name}/{p.stem}", r, here / p.stem))
    return out


def refactor_cell(src: str, rec: dict, clone: Path, n: int, arm: str, skill: Path, out: Path) -> dict:
    game, lang, model = rec["game"], rec["lang"], rec["model"]
    ws = out / f"{game}__{lang}__{arm}__{model}__{n}"
    agents.git(out, "clone", "-q", str(clone), str(ws))
    agents.git(ws, "remote", "remove", "origin")
    (ws / ".git" / "info" / "exclude").write_text(f"target/\n.bin/\n/game\n/{game}\n")   # as in games.py
    before = games.hidden(game, ws, lang, games.STEPS)
    prompt = (RESHAPE.format(skill=skill) if arm == "reshape" else "") + TASK
    author = agents.Author(model, None if arm == "baseline" else games.REPO, games.WRITABLE, out / "logs" / ws.name)
    try:
        session = agents.session_with_ci(author, prompt, ws, games.ci(lang))
    finally:
        author.close()
    step = {**session, "churn": games.churn(ws, lang), "before": before,
            "after": games.hidden(game, ws, lang, games.STEPS)}
    agents.git(ws, "commit", "-q", "--allow-empty", "-m", f"refactor ({arm})")
    shutil.rmtree(ws / "target", ignore_errors=True)
    shutil.rmtree(ws / ".bin", ignore_errors=True)
    r = {"game": game, "lang": lang, "arm": arm, "model": model, "run": n, "source": src, "refactor": step}
    (out / f"{ws.name}.json").write_text(json.dumps(r, indent=1))
    return r


def broken(step: dict) -> set[str]:
    """Hidden tests that passed before the refactor and fail after it. A tree that does not build fails
    every test, so each test it passed before counts."""
    return set(step["after"]["failed"]) - set(step["before"]["failed"])


def report(run: Path):
    with tempfile.TemporaryDirectory() as scratch:
        _report(run, cost.cells(run, Path(scratch)))


def _report(run: Path, here: Path):
    """The table of report(); `here` holds the cells, which a published run keeps in its code.tar."""
    cells = {p.stem: json.loads(p.read_text()) for p in sorted(run.glob("*.json"))}
    by = collections.defaultdict(dict)                 # source -> arm -> cell
    for name, r in cells.items():
        by[r["source"]][r["arm"]] = name
    print(f"  {'author':18} {'arm':12} {'n':>3}  {'broke':>5} {'tests':>5} {'fixed':>5} {'red':>3}   "
          f"against baseline: {'time':>5} {'tokens':>6} {'$':>5} {'code':>5} {'tests':>5}")
    pad = " " * len("against baseline:")
    for model in sorted({r["model"] for r in cells.values()}):
        for arm in ARMS:
            names = [s[arm] for s in by.values() if arm in s and cells[s[arm]]["model"] == model]
            if not names:
                continue
            steps = [cells[n]["refactor"] for n in names]
            fixed = sum(len(set(s["before"]["failed"]) - set(s["after"]["failed"])) for s in steps)
            red = sum(s.get("ci_red_after_fix", False) for s in steps)
            ratios = collections.defaultdict(list)
            for name in names:
                base = by[cells[name]["source"]].get("baseline")
                if arm == "baseline" or base is None:
                    continue
                for key in ("ms", "out_tokens", "cost"):
                    x, y = (cost.spent([cells[n]["refactor"]], key) for n in (name, base))
                    if x is not None and y:
                        ratios[key].append(x / y)
                (code, tests), (base_code, base_tests) = cost.lines(here / name), cost.lines(here / base)
                ratios["code"].append(code / base_code)
                ratios["tests"].append(tests / base_tests)
            pairs = len(ratios["code"])
            change = " ".join(f"{cost.change(ratios[k], pairs) if pairs else '':>{w}}"
                              for k, w in (("ms", 5), ("out_tokens", 6), ("cost", 5), ("code", 5), ("tests", 5)))
            print(f"  {model:18} {arm:12} {len(names):>3}  {sum(bool(broken(s)) for s in steps):>5} "
                  f"{sum(len(broken(s)) for s in steps):>5} {fixed:>5} {red:>3}   {pad} {change}")
    print("broke: projects with a hidden test that passed before and fails after; tests: such tests; fixed: the "
          "reverse; red: CI red after the fix round.")
    unstable = [src for src, arms in by.items()
                if len({tuple(cells[n]["refactor"]["before"]["failed"]) for n in arms.values()}) > 1]
    if unstable:
        print(f"the hidden tests before the refactor differ between arms for: {', '.join(unstable)}")


def recheck(run: Path):
    os.environ.update(games.TOOLCHAIN_ENV)
    differ = 0
    with tempfile.TemporaryDirectory() as scratch:
        here = cost.cells(run, Path(scratch) / "cells")
        records = sorted(run.glob("*.json"))
        for p in records:
            r = json.loads(p.read_text())
            ws = Path(scratch) / "ws"
            agents.git(Path(scratch), "clone", "-q", str(here / p.stem), str(ws))
            for when, rev in (("before", "HEAD~1"), ("after", "HEAD")):
                agents.git(ws, "checkout", "-q", rev)
                failed = games.hidden(r["game"], ws, r["lang"], games.STEPS)["failed"]
                recorded = r["refactor"][when]["failed"]
                if failed != recorded:
                    differ += 1
                    print(f"  {p.stem} {when}: recorded {len(recorded)} failed, now {len(failed)}; only recorded "
                          f"{sorted(set(recorded) - set(failed))}, only now {sorted(set(failed) - set(recorded))}",
                          flush=True)
            shutil.rmtree(ws)
    print(f"{len(records)} cells, {differ} results before or after differ from the recorded ones")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", help="published runs whose baseline projects are the sources")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--models", help="only the sources grown by these models")
    ap.add_argument("--limit", type=int, help="only the first N sources, for a smoke run")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--report")
    ap.add_argument("--recheck")
    a = ap.parse_args()
    if a.report:
        return report(Path(a.report))
    if a.recheck:
        return recheck(Path(a.recheck))
    arms = a.arms.split(",")
    if unknown := set(arms) - set(ARMS):
        raise SystemExit(f"unknown arms {unknown}; the arms are {', '.join(ARMS)}")
    os.environ.update(games.TOOLCHAIN_ENV)
    out = games.RUNS / f"refactor-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="refactor-") as scratch:
        # the skills as an installed plugin holds them, outside the repository that holds the cells
        shutil.copytree(games.REPO / "skills", Path(scratch) / "skills")
        skill = Path(scratch) / "skills" / "reshape" / "SKILL.md"
        found = [s for s in sources([Path(r) for r in a.runs], Path(scratch) / "sources")
                 if not a.models or s[1]["model"] in a.models.split(",")][:a.limit]
        numbered, seen = [], collections.Counter()
        for src, rec, clone in found:                  # n tells apart sources of the same game, language and model
            key = (rec["game"], rec["lang"], rec["model"])
            numbered.append((src, rec, clone, seen[key]))
            seen[key] += 1
        cells = [(*s, arm) for s in numbered for arm in arms]
        print(f"refactoring {len(numbered)} sources x {len(arms)} arms, {a.workers} at a time -> {out}", flush=True)
        with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
            futs = {pool.submit(refactor_cell, *c, skill, out): c for c in cells}
            for i, f in enumerate(concurrent.futures.as_completed(futs), 1):
                src, arm = futs[f][0], futs[f][-1]
                try:
                    f.result()
                    print(f"  [{i}/{len(cells)}] {src} {arm} done", flush=True)
                except Exception as e:                # a crashed cell writes no record, so it is never judged
                    print(f"  [{i}/{len(cells)}] {src} {arm} ERROR {e!r}", flush=True)
    report(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

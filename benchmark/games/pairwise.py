"""Blind pairwise judgment of two arms' final game code, cell by cell (same game, language, model, run).

The judge sees the game's spec and the two projects' source files labelled A and B, never the arms,
the step history or the hidden test results, and says which project it would rather extend. Every
pair is judged twice with the order swapped; a pair counts for an arm only when both orders agree.
The judge comes from another vendor than the authors, unless --same-vendor asks for a cross-check.

  python3 pairwise.py runs/<stamp> --arms baseline,tesla-valve --judge claude-sonnet-5-5
"""
import argparse
import collections
import concurrent.futures
import json
import re
import subprocess
from pathlib import Path

import agents

MAX_PROJECT = 80000
SOURCE = (".rs", ".go", "Cargo.toml", "go.mod")
RUBRICS = {
# neutral: no criterion in the rules' own words, so a win cannot come from the rubric echoing them
"neutral": """You review two implementations of the same small game, written to the same specification by two
engineers. The game will keep growing: more rules, modes and commands will follow. Decide which project you
would rather receive to implement the next feature, and to maintain for years. Judge as an experienced engineer
would: how easy the code is to understand, how safely it can be changed, how well its tests protect its
behaviour, and whether its complexity fits the problem. Do not reward length or brevity for its own sake.
Do not guess which project passes more tests.
Reply with one JSON object: {"better": "A" | "B" | "tie", "overbuilt_A": true|false, "overbuilt_B": true|false,
"why": "<one sentence>"}""",
# v1: the criteria in the rules' own terms; a cross-check that the rubric is not what decides
"v1": """You review two implementations of the same small game, written to the same specification by two
engineers. The game will keep growing: more rules, modes and commands will follow. Decide which project
you would rather receive to implement the next feature, and to maintain for years. Weigh:
- a rule of the game lives in one place, so changing it touches one place;
- the game's states and transitions are easy to follow from the code's structure;
- input from outside is validated where it enters;
- it adds no abstraction or machinery the game does not need;
- its tests state the intended behaviour.
Do not reward length or brevity for its own sake. Do not guess which project passes more tests.
Reply with one JSON object: {"better": "A" | "B" | "tie", "overbuilt_A": true|false, "overbuilt_B": true|false,
"why": "<one sentence>"}"""}


def vendor(model: str) -> str:
    return "openai" if model.startswith("gpt-") else "anthropic"


def project(cell: Path) -> str:
    files = subprocess.run(["git", "ls-files"], cwd=cell, capture_output=True, text=True).stdout.split()
    text = "".join(f"--- {f}\n{(cell / f).read_text(errors='replace')}\n" for f in sorted(files) if f.endswith(SOURCE))
    return text[:MAX_PROJECT]


def verdict(spec: str, a: str, b: str, judge: str, rubric: str) -> dict:
    user = f"SPECIFICATION:\n{spec}\n\nPROJECT A:\n{a}\n\nPROJECT B:\n{b}"
    for _ in range(3):
        m = re.search(r"\{.*\}", agents.judge(RUBRICS[rubric], user, judge), re.S)
        if m:
            try:
                v = json.loads(m.group(0))
                if v.get("better") in ("A", "B", "tie"):
                    return v
            except ValueError:
                pass
    return {"better": "error"}


def judge_pair(cells: dict, arms: tuple[str, str], judge: str, rubric: str) -> dict:
    x, y = arms
    spec = (cells[x] / "spec.md").read_text()
    src = {arm: project(c) for arm, c in cells.items()}
    first = verdict(spec, src[x], src[y], judge, rubric)     # x is A
    second = verdict(spec, src[y], src[x], judge, rubric)    # y is A
    pick = lambda v, a_arm, b_arm: {"A": a_arm, "B": b_arm}.get(v["better"], "tie")
    p1, p2 = pick(first, x, y), pick(second, y, x)
    return {"pair": cells[x].name, "orders": [p1, p2], "winner": p1 if p1 == p2 else "tie",
            "why": [first.get("why"), second.get("why")],
            f"overbuilt_{x}": [first.get("overbuilt_A"), second.get("overbuilt_B")],
            f"overbuilt_{y}": [first.get("overbuilt_B"), second.get("overbuilt_A")]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--arms", default="baseline,tesla-valve")
    ap.add_argument("--judge", required=True)
    ap.add_argument("--rubric", choices=sorted(RUBRICS), default="neutral")
    ap.add_argument("--same-vendor", action="store_true", help="allow a judge from the authors' vendor")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    run, arms = Path(a.run), tuple(a.arms.split(","))
    by = collections.defaultdict(dict)
    for p in run.glob("*.json"):
        r = json.loads(p.read_text())
        if "refactor" in r or len(r["steps"]) == 6:    # finished cells; refactor.py writes a record only then
            if vendor(r["model"]) == vendor(a.judge) and not a.same_vendor:
                raise SystemExit(f"{a.judge} would judge code by {r['model']}, its own vendor's; pass --same-vendor "
                                 "only for a cross-check")
            by[(r["game"], r["lang"], r["model"], r["run"])][r["arm"]] = run / p.stem
    pairs = [cells for _, cells in sorted(by.items()) if all(arm in cells for arm in arms)]
    print(f"judging {len(pairs)} pairs {arms[0]} vs {arms[1]} with {a.judge}, rubric {a.rubric}", flush=True)
    out = []
    with concurrent.futures.ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(lambda c: judge_pair({arm: c[arm] for arm in arms}, arms, a.judge, a.rubric), pairs):
            out.append(r)
            print(f"  {r['pair']:60} {r['orders']} -> {r['winner']}", flush=True)
    judged = run / "judged"                            # outside the cell records that report() globs
    judged.mkdir(exist_ok=True)
    (judged / f"pairwise-{arms[0]}-{arms[1]}-{a.judge}-{a.rubric}.json").write_text(json.dumps(out, indent=1))
    print("winner counts:", dict(collections.Counter(r["winner"] for r in out)))
    for arm in arms:
        print(f"  {arm}: over-built flagged in {sum(any(r[f'overbuilt_{arm}']) for r in out)}/{len(out)}")


if __name__ == "__main__":
    main()

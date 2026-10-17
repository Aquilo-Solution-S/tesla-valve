"""What an arm costs against baseline, per author model: the authors' session time, output tokens and
dollars, and the size of the final code. Each figure is the median over the pairs of arm / baseline.

  python3 cost.py results/* --arm tv-v7a
"""
import argparse
import collections
import json
import re
import statistics
import subprocess
import tarfile
import tempfile
from pathlib import Path

import agents

SESSION = {"ms": "time", "out_tokens": "output tokens", "cost": "dollars"}


def change(ratios: list[float], pairs: int) -> str:
    """The median change, or '-' unless every pair reported it."""
    return f"{round((statistics.median(ratios) - 1) * 100):+d}%" if len(ratios) == pairs else "-"


def spent(steps: list[dict], key: str) -> float | None:
    """The sum over the steps' sessions and fix rounds, or None where the author's CLI did not report it."""
    values = [s[key] for step in steps for s in (step["session"], step.get("fix") or {}) if s.get(key) is not None]
    return sum(values) if values else None


def lines(cell: Path) -> tuple[int, int]:
    """Non-empty lines of Rust and Go, as (code, tests). A file named for tests, or under tests/, is tests;
    in a Rust file, so is everything from its first #[cfg(test)], where Rust puts its unit tests."""
    code = tests = 0
    for name in agents.git(cell, "ls-files").stdout.split():
        if not name.endswith((".rs", ".go")):
            continue
        text = (cell / name).read_text(errors="replace")
        if "test" in Path(name).name or name.startswith("tests/") or "/tests/" in name:
            tests += sum(1 for line in text.splitlines() if line.strip())
            continue
        cut = re.search(r"#\[cfg\(test\)\]", text) if name.endswith(".rs") else None
        head, tail = (text[:cut.start()], text[cut.start():]) if cut else (text, "")
        code += sum(1 for line in head.splitlines() if line.strip())
        tests += sum(1 for line in tail.splitlines() if line.strip())
    return code, tests


def cells(run: Path, scratch: Path) -> Path:
    """The run's cell directories: the run itself after games.py, or its code.tar cloned once published."""
    if not (run / "code.tar").exists():
        return run
    out = scratch / run.name
    with tarfile.open(run / "code.tar") as tar:
        tar.extractall(out, filter="data")
    for bundle in out.glob("*.bundle"):
        subprocess.run(["git", "clone", "-q", str(bundle), str(out / bundle.stem)], check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--arm", default="tesla-valve")
    a = ap.parse_args()
    ratios = collections.defaultdict(lambda: collections.defaultdict(list))
    with tempfile.TemporaryDirectory() as scratch:
        for run in map(Path, a.runs):
            recs = {}
            for p in run.glob("*.json"):
                r = json.loads(p.read_text())
                if "refactor" not in r and len(r["steps"]) == 6:   # refactor.py reports its own cost
                    recs[(r["game"], r["lang"], r["model"], r["run"], r["arm"])] = (r, p.stem)
            if not recs:
                continue
            here = cells(run, Path(scratch))
            for (game, lang, model, i, arm), (rec, stem) in recs.items():
                base = recs.get((game, lang, model, i, "baseline"))
                if arm != a.arm or base is None:
                    continue
                for key in SESSION:
                    x, y = spent(rec["steps"], key), spent(base[0]["steps"], key)
                    if x is not None and y:
                        ratios[model][key].append(x / y)
                (code, tests), (base_code, base_tests) = lines(here / stem), lines(here / base[1])
                ratios[model]["code"].append(code / base_code)
                ratios[model]["tests"].append(tests / base_tests)
    columns = {**SESSION, "code": "code lines", "tests": "test lines"}
    print(f"{a.arm} against baseline, median change per pair")
    print(f"{'author':18} {'pairs':>5}  " + "  ".join(f"{c:>13}" for c in columns.values()))
    every = {k: [x for r in ratios.values() for x in r[k]] for k in columns}
    for model, r in [*sorted(ratios.items()), ("all", every)]:
        pairs = len(r["code"])
        print(f"{model:18} {pairs:>5}  " + "  ".join(f"{change(r[k], pairs):>13}" for k in columns))
    print("Time is the authors' session time, without CI and hidden tests. '-': not every pair's CLI reported it.")


if __name__ == "__main__":
    main()

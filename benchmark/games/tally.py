"""The pairwise verdicts of one or more runs, counted per comparison, judge, rubric, author model and game.

  python3 tally.py results/*
"""
import collections
import json
import re
import sys
from pathlib import Path

import pairwise

# pairwise-<first arm>-<second arm>-<judge>-<rubric>.json; the arms are read from the verdicts themselves
NAME = re.compile(rf"pairwise-.+?-(?P<judge>(?:gpt|claude)-.+)-(?P<rubric>{'|'.join(pairwise.RUBRICS)})\.json")


def main():
    wins, overbuilt = collections.defaultdict(collections.Counter), collections.Counter()
    for f in sorted(p for run in sys.argv[1:] for p in Path(run, "judged").glob("pairwise-*.json")):
        m = NAME.fullmatch(f.name)
        if not m:
            sys.exit(f"{f}: not named pairwise-<arm>-<arm>-<judge>-<rubric>.json")
        for v in json.loads(f.read_text()):
            first, second = [k.removeprefix("overbuilt_") for k in v if k.startswith("overbuilt_")]
            game, _, _, model, _ = v["pair"].split("__")
            key = (first, second, m["judge"], m["rubric"], model, game)
            wins[key][v["winner"]] += 1
            overbuilt[key] += any(v[f"overbuilt_{first}"]) + any(v[f"overbuilt_{second}"])
    print(f"{'second arm vs first arm':30} {'judge':18} {'rubric':7} {'author':17} {'game':10} pairs  "
          "second:first:tie  over-built")
    for key, c in sorted(wins.items()):
        first, second, judge, rubric, model, game = key
        print(f"{second + ' vs ' + first:30} {judge:18} {rubric:7} {model:17} {game:10} {c.total():>5}  "
              f"{c[second]:>6}:{c[first]}:{c['tie']}  {overbuilt[key]:>10}")
    print("A pair counts for an arm only when both orders agree. Over-built: projects the judge flagged in either "
          "order.")


if __name__ == "__main__":
    main()

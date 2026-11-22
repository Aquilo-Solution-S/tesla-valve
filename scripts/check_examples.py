"""Checks that every example passes its own checks, and that every enforcer the
references name refuses what they say it refuses.

    python3 scripts/check_examples.py [rust] [go] [python] [typescript] [lean]

Each example under examples/<language>/ must pass clean. Then each file in
examples/bad/<language>/ goes into a fresh copy of that example, one at a time.
The checks must fail, and their output must contain every `expect:` line the
file names, so a bad file cannot pass on an unrelated error. A bad file that
belongs somewhere else in the copy names the place in a `slot:` line.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

root = Path(__file__).resolve().parent.parent
examples = root / "examples"


@dataclass(frozen=True)
class Language:
    checks: list[list[str]]  # must all pass on the example
    lints: list[list[str]]  # run on each copy that carries a bad file
    slot: str  # where a bad file goes in the copy, unless it names its own slot
    register: tuple[str, str] | None = None  # a file and the line it needs to see the bad file
    linked: tuple[str, ...] = ()  # directories the copy links instead of copying
    beside: tuple[str, ...] = ()  # examples the checks read, copied next to the copy


CLIPPY = ["cargo", "clippy", "--all-targets", "--locked", "--", "-D", "warnings"]
PYTHON_LINTS = [["pyright"], ["mypy", "."], ["ruff", "check"]]
TYPESCRIPT_LINTS = [["npx", "tsc", "--noEmit"], ["npx", "eslint", "."]]
LEAN_GATE = [["lake", "build", "--wfail"], ["lake", "exe", "shop", "check"]]

LANGUAGES = {
    "rust": Language(
        checks=[CLIPPY, ["cargo", "test", "--locked"]],
        lints=[CLIPPY],
        slot="src/bad.rs",
        register=("src/lib.rs", "\nmod bad;\n"),
    ),
    "go": Language(
        checks=[["go", "vet", "./..."], ["go", "test", "./..."], ["golangci-lint", "run", "./..."]],
        lints=[["golangci-lint", "run", "./..."]],
        slot="bad/bad.go",
    ),
    "python": Language(
        checks=[*PYTHON_LINTS, ["python", "-m", "pytest", "-q"]],
        lints=PYTHON_LINTS,
        slot="shop/bad.py",
    ),
    "typescript": Language(
        checks=[*TYPESCRIPT_LINTS, ["npm", "test"]],
        lints=TYPESCRIPT_LINTS,
        slot="src/bad.ts",
        linked=("node_modules",),
    ),
    "lean": Language(
        checks=[*LEAN_GATE, ["lake", "exe", "shop", "view"], ["lake", "exe", "shop", "emit", "vectors"]],
        lints=LEAN_GATE,
        slot="Spec/Stock/Unheld.lean",
        beside=("go", "python", "rust", "typescript"),
    ),
}

NOT_COPIED = shutil.ignore_patterns("target", "node_modules", "dist", "__pycache__", ".*_cache", ".lake")
EXPECT = re.compile(r"^(?://|#|--) expect: (.+)$", re.MULTILINE)
SLOT = re.compile(r"^(?://|#|--) slot: (.+)$", re.MULTILINE)

# Every copy of the Rust example builds into one target directory, so the
# dependencies compile once.
os.environ.setdefault("CARGO_TARGET_DIR", str(examples / "rust" / "target"))


def run(commands: list[list[str]], cwd: Path) -> tuple[bool, str]:
    passed, output = True, ""
    for command in commands:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
        output += f"$ {' '.join(command)}\n{result.stdout}{result.stderr}"
        passed = passed and result.returncode == 0
    return passed, output


def refuses(name: str, language: Language, bad: Path) -> tuple[bool, str]:
    source = bad.read_text()
    expected = EXPECT.findall(source)
    if not expected:
        return False, f"{bad} names no `expect:` line"
    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp)
        example_root = sandbox / "examples" if name == "lean" else sandbox
        copy = example_root / name
        shutil.copytree(examples / name, copy, ignore=NOT_COPIED)
        for directory in language.linked:
            (copy / directory).symlink_to(examples / name / directory)
        for other in language.beside:
            shutil.copytree(examples / other, example_root / other, ignore=NOT_COPIED)
        named = SLOT.search(source)
        slot = copy / (named[1] if named else language.slot)
        slot.parent.mkdir(parents=True, exist_ok=True)
        # Blank the expect lines, so a tool that quotes the source cannot match them.
        slot.write_text(SLOT.sub("", EXPECT.sub("", source)))
        if language.register:
            path, line = language.register
            with (copy / path).open("a") as file:
                file.write(line)
        if name == "lean":
            # Lake resolves the dependency from examples/lean, and the check scans tracked files.
            (sandbox / "lean").symlink_to(root / "lean", target_is_directory=True)
            ready, output = run([["git", "init", "--quiet"], ["git", "add", "--", "examples"]], sandbox)
            if not ready:
                return False, output
        passed, output = run(language.lints, copy)
    missing = [line for line in expected if line not in output]
    if passed:
        return False, f"the checks passed\n{output}"
    if missing:
        return False, f"the checks failed, but without {missing}\n{output}"
    return True, output


def check_lean_artifacts() -> tuple[bool, str]:
    lean = examples / "lean"
    passed, output = run([["lake", "exe", "vectors"]], lean)
    if not passed:
        return False, output

    command = ["lake", "exe", "shop", "emit", "rust"]
    emitted = subprocess.run(command, cwd=lean, capture_output=True, check=False)
    output += f"$ {' '.join(command)}\n{emitted.stderr.decode()}"
    if emitted.returncode != 0:
        return False, output
    ledger = "examples/rust/src/ledger.rs"
    (root / ledger).write_bytes(emitted.stdout)

    paths = [ledger, ":(glob)examples/**/delivery_days.json"]
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--", *paths], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    if untracked:
        return False, output + f"Generated files missing from Git:\n{untracked}"
    passed, diff = run([["git", "diff", "--exit-code", "HEAD", "--", *paths]], root)
    return passed, output + diff


def report(title: str, passed: bool, output: str) -> bool:
    print(("ok    " if passed else "FAIL  ") + title, flush=True)
    if not passed:
        print(output[-4000:], flush=True)
    return passed


def main() -> None:
    results = []
    for name in sys.argv[1:] or LANGUAGES:
        language = LANGUAGES[name]
        passed = report(f"{name}: the example passes", *run(language.checks, examples / name))
        results.append(passed)
        if name == "lean" and passed:
            results.append(report("lean: regenerated Rust and vectors match the commit", *check_lean_artifacts()))
        for bad in sorted((examples / "bad" / name).iterdir()):
            results.append(report(f"{name}: {bad.name} is refused", *refuses(name, language, bad)))
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()

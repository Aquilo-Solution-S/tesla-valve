"""Checks that every example passes its own checks, and that every enforcer the
references name refuses what they say it refuses.

    python3 scripts/check_examples.py [rust] [go] [python] [typescript]

Each example under examples/<language>/ must pass clean. Then each file in
examples/bad/<language>/ goes into a fresh copy of that example, one at a time.
The checks must fail, and their output must contain every `expect:` line the
file names, so a bad file cannot pass on an unrelated error.
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
    slot: str  # where the bad file goes in the copy
    register: tuple[str, str] | None = None  # a file and the line it needs to see the bad file
    linked: tuple[str, ...] = ()  # directories the copy links instead of copying


CLIPPY = ["cargo", "clippy", "--all-targets", "--locked", "--", "-D", "warnings"]
PYTHON_LINTS = [["pyright"], ["mypy", "."], ["ruff", "check"]]
TYPESCRIPT_LINTS = [["npx", "tsc", "--noEmit"], ["npx", "eslint", "."]]

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
}

NOT_COPIED = shutil.ignore_patterns("target", "node_modules", "dist", "__pycache__", ".*_cache")
EXPECT = re.compile(r"^(?://|#) expect: (.+)$", re.MULTILINE)

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
        copy = Path(tmp) / name
        shutil.copytree(examples / name, copy, ignore=NOT_COPIED)
        for directory in language.linked:
            (copy / directory).symlink_to(examples / name / directory)
        (copy / language.slot).parent.mkdir(parents=True, exist_ok=True)
        # Blank the expect lines, so a tool that quotes the source cannot match them.
        (copy / language.slot).write_text(EXPECT.sub("", source))
        if language.register:
            path, line = language.register
            with (copy / path).open("a") as file:
                file.write(line)
        passed, output = run(language.lints, copy)
    missing = [line for line in expected if line not in output]
    if passed:
        return False, f"the checks passed\n{output}"
    if missing:
        return False, f"the checks failed, but without {missing}\n{output}"
    return True, output


def report(title: str, passed: bool, output: str) -> bool:
    print(("ok    " if passed else "FAIL  ") + title, flush=True)
    if not passed:
        print(output[-4000:], flush=True)
    return passed


def main() -> None:
    results = []
    for name in sys.argv[1:] or LANGUAGES:
        language = LANGUAGES[name]
        results.append(report(f"{name}: the example passes", *run(language.checks, examples / name)))
        for bad in sorted((examples / "bad" / name).iterdir()):
            results.append(report(f"{name}: {bad.name} is refused", *refuses(name, language, bad)))
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()

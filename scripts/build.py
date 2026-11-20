"""Builds the copy of AGENTS.md that Cursor loads, copies the plugin's version
into every manifest, writes every quoted code block from the example it quotes,
and checks that SKILL.md and AGENTS.md still say the same thing and that every
relative link in the Markdown resolves.

    python3 scripts/build.py

CI runs it and fails if a check fails or a generated file differs from the
commit.
"""

import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

root = Path(__file__).parent.parent
rules = (root / "AGENTS.md").read_text()

(root / "rules" / "tesla-valve.mdc").write_text(f"""---
description: Tesla Valve. Shape over checks, check once at the spring, test the intent.
alwaysApply: true
---

<!-- Generated from AGENTS.md by scripts/build.py. Edit that and run this. -->

{rules}""")

# The version is named once, in the Claude manifest. Codex and Cursor read
# their own manifests, so they get a copy.
version = json.loads((root / ".claude-plugin" / "plugin.json").read_text())["version"]
for path in (root / ".codex-plugin" / "plugin.json", root / ".cursor-plugin" / "plugin.json"):
    manifest = json.loads(path.read_text())
    manifest.pop("version", None)
    manifest = {"name": manifest.pop("name"), "version": version, **manifest}
    path.write_text(json.dumps(manifest, indent=2) + "\n")

# A code block under `<!-- code: examples/<file>#<region> -->` is the region of
# that file between `region: <name>` and `endregion`, or the whole file when no
# region is named. The docs show the code CI runs, and never a copy of it.
QUOTE = re.compile(
    r"^(?P<marker><!-- code: (?P<path>[^ #]+)(?:#(?P<region>[\w-]+))? -->)\n"
    r"(?P<fence>`{3,})(?P<lang>[\w-]*)\n.*?^(?P=fence)$",
    re.MULTILINE | re.DOTALL,
)
REGION = re.compile(r"^\s*(?://|#|--) (?:region: (?P<name>[\w-]+)|endregion)\s*$")
problems = []


def quoted(path: str, region: str | None) -> str:
    lines = (root / path).read_text().splitlines()
    if region:
        starts = [i for i, line in enumerate(lines) if (m := REGION.match(line)) and m["name"] == region]
        if len(starts) != 1:
            problems.append(f"{path} has {len(starts)} regions named {region!r}")
            return ""
        end = next((i for i in range(starts[0] + 1, len(lines)) if REGION.match(lines[i])), None)
        if end is None:
            problems.append(f"{path} never ends region {region!r}")
            return ""
        lines = lines[starts[0] + 1 : end]
    code = "\n".join(line for line in lines if not REGION.match(line))
    return textwrap.dedent(code).strip("\n")


def quote(match: re.Match[str]) -> str:
    code = quoted(match["path"], match["region"])
    fence = match["fence"]
    return f"{match['marker']}\n{fence}{match['lang']}\n{code}\n{fence}"


docs = [root / "MANIFESTO.md", *sorted((root / "skills").rglob("*.md"))]
for doc in docs:
    text = doc.read_text()
    if (generated := QUOTE.sub(quote, text)) != text:
        doc.write_text(generated)
skill = (root / "skills" / "tesla-valve" / "SKILL.md").read_text()

# Prepare proves each enforcer with a bad file, so the reference for a language
# quotes every bad file CI feeds that language.
for bad in sorted((root / "examples" / "bad").glob("*/*")):
    reference = root / "skills" / "prepare" / "references" / f"{bad.parent.name}.md"
    if f"<!-- code: {bad.relative_to(root)} -->" not in reference.read_text():
        problems.append(f"{reference.relative_to(root)} does not quote {bad.relative_to(root)}")

# SKILL.md is longer than AGENTS.md, so the two cannot be compared whole. These
# lines carry the rules and must appear in both, word for word. Rewording one
# in either file fails here, which is the reminder to change the other.
SHARED = [
    "Which streams already flow?",
    "Contain instead of compare.",
    "without a catch-all",
    "the value or the reason it could not",
    "Read the clock at the spring and pass it in.",
    "where the operation commits",
    "shape attempt per finding",
    "A test goes when the behaviour it pins goes, in the same commit, or when the compiler or a linter this project runs now catches what it caught: then name the shape that does.",
    "A channel you replace goes, with its tests and its guards, in the commit that adds the new one.",
    "Your own repository is not a spring",
    "Derive it from the tree or delete it.",
    "A test double is not a spring: its checks get no tests.",
    "one test constructor beside its type",
    "A new required field changes that constructor and the tests that care about the field, nothing else.",
    "The line is the proof, not a snapshot of the compiler's message",
    "A list each change must extend by hand is not an enforcer.",
    "is load, not safety.",
    "a Rust binary crate or a crate with doctests turned off",
    "A read and a later write is a race.",
    "a reservation is released when the order is cancelled",
    "A value with no invariant stays a primitive.",
    "Every way in counts: a default, a conversion from the raw value, a mutable accessor.",
    "so no module has to be trusted to keep it valid.",
    "A shape counts only where this project's compiler or CI enforces it.",
    "Keep the runtime check wherever types are erased",
    "never a silent default",
    "loses to a plain\ncheck at the spring",
    "Whatever has to be remembered will be forgotten.",
    "Search the project before you build one: its logger beats a bare `print`.",
    "a unit converter needs no Meter, Foot and Conversion types for one multiplication.",
    "A shape costs its fixtures and proofs, and pays where a mistake can travel: into another module, across a boundary, into a later change.",
    "A script that prunes old backups needs no Backup type around a file name",
]

problems += [
    f"{name} lacks: {line!r}"
    for line in SHARED
    for name, text in (("AGENTS.md", rules), ("SKILL.md", skill))
    if " ".join(line.split()) not in " ".join(text.split())
]

# A relative link is a pointer, and it is only right while its target is there.
# Every one in the Markdown of this tree resolves, whether Markdown or an HTML
# tag writes it: to a file, and to a heading in it where the link names one.
# Git lists the tree, so .gitignore is the one place that says what is not
# part of it.
FENCE = re.compile(r"^(?P<fence>`{3,}).*?^(?P=fence)$", re.MULTILINE | re.DOTALL)
INLINE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r'\[[^\]]*\]\((?P<markdown>[^)\s]+)(?:\s+"[^"]*")?\)|\b(?:src|href)="(?P<html>[^"]+)"')
HEADING = re.compile(r"^#+ (.+)$", re.MULTILINE)


def anchors(doc: Path) -> set[str]:
    headings = HEADING.findall(FENCE.sub("", doc.read_text()))
    return {re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings}


listed = subprocess.run(
    ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "*.md"],
    cwd=root, capture_output=True, text=True, check=True,
).stdout.split("\0")
for doc in (root / name for name in listed if name and (root / name).is_file()):
    for link in LINK.finditer(INLINE.sub("", FENCE.sub("", doc.read_text()))):
        target = link["markdown"] or link["html"]
        if re.match(r"[a-z][a-z0-9+.-]*:", target):
            continue
        path, _, anchor = target.partition("#")
        dest = doc.parent / path if path else doc
        if not dest.exists():
            problems.append(f"{doc.relative_to(root)} links to {target}, which is not there")
        elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
            problems.append(f"{doc.relative_to(root)} links to {target}, and {path or doc.name} has no such heading")

if problems:
    sys.exit("\n".join(problems))

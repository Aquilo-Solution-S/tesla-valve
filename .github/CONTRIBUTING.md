# Contributing

Thanks for helping. Each rule here names what holds it, and CI runs all of it
on every pull request and every push to `main`.

## Before you open a pull request

```sh
python3 scripts/build.py
python3 scripts/check_examples.py
```

`build.py` writes every quoted code block from the example it quotes,
`rules/tesla-valve.mdc` from `AGENTS.md`, and the version in
`.claude-plugin/plugin.json` into the Codex and Cursor manifests. CI fails when
a generated file differs from the commit: edit the source, never the quote.

`check_examples.py` needs each language's pinned tools on the `PATH`, installed
the way [the workflow](workflows/test.yml) installs them. Name a language to
check only that one: `python3 scripts/check_examples.py rust`.

## Changing a rule

The rules live in `AGENTS.md` and `skills/tesla-valve/SKILL.md`. `build.py`
fails when a line both carry differs between them, so change it in both.

## Adding an enforcer

An enforcer counts once a bad file proves it fires. Add one under
`examples/bad/<language>/` with an `expect:` line for each message it must
cause. `check_examples.py` fails when the checks pass on it, or fail without
that message. `build.py` fails until `skills/prepare/references/<language>.md`
quotes it.

## Judgment calls

Write in English, so every reader can follow every file. Keep a pull request to
one change, so it can be reverted on its own: a new rule and its enforcer are
one change, a new rule and a fixed typo are two.

Security reports go through [SECURITY.md](SECURITY.md), not an issue. Everyone
here follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Maintainers

Maintainers push to `main` directly, without a pull request. Before the push,
the checks above pass, and a model from another vendor than the one that wrote
the change reviews it: nothing else reads a change before it lands. `main`
refuses force pushes and deletions, and keeps a linear history.

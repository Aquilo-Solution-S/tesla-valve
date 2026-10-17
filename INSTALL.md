# Install

Tesla Valve has four parts: the rules in [`AGENTS.md`](AGENTS.md), which every
session should carry; the skill in [`skills/tesla-valve/`](skills/tesla-valve/),
the full method the agent loads when it plans, writes or reviews code; and two
skills you start yourself. [`prepare`](skills/prepare/) sets up a project's
compiler settings, linters and CI so its shapes count, and
[`reshape`](skills/reshape/) brings existing code into those shapes. Each host
below gets all four, as far as the host allows.

Prepare changes a project's configs and CI, and reshape changes code beyond any
one task, so the agent never starts either on its own. Start prepare once per
project, and reshape for each scope you choose, with the commands each host
lists below.

## Claude Code

```
/plugin marketplace add Aquilo-Solution-S/tesla-valve
```
```
/plugin install tesla-valve@tesla-valve
```

Send them as two separate prompts. A `SessionStart` hook hands `AGENTS.md` to
every session and every subagent, and the skill shows up as
`tesla-valve:tesla-valve`. Start the other two with `/tesla-valve:prepare` and
`/tesla-valve:reshape`. The hook runs `node`, so Node.js must be on your
`PATH`.

## Codex

```bash
codex plugin marketplace add Aquilo-Solution-S/tesla-valve
codex plugin add tesla-valve@tesla-valve
```

Then run `codex`, open `/hooks`, review and trust the plugin's two hooks, and
start a new thread. It is the same hook as in Claude Code, so it needs `node`
too. Start the other two with `$tesla-valve:prepare` and
`$tesla-valve:reshape`.

## Grok

```bash
grok plugin install Aquilo-Solution-S/tesla-valve
grok plugin enable tesla-valve
```

Grok asks you to confirm that you trust the plugin. It then loads the skill and
picks it for coding tasks from its description; type `/tesla-valve` to load it
yourself, and `/prepare` or `/reshape` to start the other two. Grok takes no
instructions from lifecycle hooks, so for the rules in every session, copy
[`AGENTS.md`](AGENTS.md) into your project.

## Cursor

For the rules in every conversation, copy
[`rules/tesla-valve.mdc`](rules/tesla-valve.mdc) into your project's
`.cursor/rules/`. Cursor and Cursor Agent apply it in that project.

For the skill as well, run Cursor Agent with the plugin from a checkout:

```bash
git clone https://github.com/Aquilo-Solution-S/tesla-valve
cursor-agent --plugin-dir tesla-valve
```

Cursor Agent loads a plugin's skills but not its rules, which is why the rule
is copied. Start the other two with `/prepare` and `/reshape`.

## Any other agent

Copy [`AGENTS.md`](AGENTS.md) into your project, or ask your agent to install
[`skills/tesla-valve/SKILL.md`](skills/tesla-valve/SKILL.md) as a skill. To
prepare a project or reshape its code, point the agent at
[`skills/prepare/SKILL.md`](skills/prepare/SKILL.md) or
[`skills/reshape/SKILL.md`](skills/reshape/SKILL.md) and ask it to follow it.

## Uninstall

| Host | Command |
| --- | --- |
| Claude Code | `/plugin uninstall tesla-valve` |
| Codex | `codex plugin remove tesla-valve` |
| Grok | `grok plugin uninstall tesla-valve` |
| Cursor | delete `.cursor/rules/tesla-valve.mdc` |

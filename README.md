<p align="center">
  <img src="assets/tesla-valve.svg" alt="A Tesla valve. Water flows freely from left to right. Flowing back, every loop turns it against itself.">
</p>

<h1 align="center">Tesla Valve</h1>

<p align="center">
  <em>No moving parts. The right path flows, and the wrong one works against itself.</em>
</p>

---

Most advice for AI-written code counts lines: fewer is better, and the shortest
diff wins. Tesla Valve counts something else: how much you have to hold in your
head to trust the code.

A Tesla valve is a channel with no moving parts. Water passes through it freely
in one direction, and flowing back, the shape of the channel turns it against
itself. Tesla Valve asks your AI agent to build code like that. Wrong use is
impossible to write instead of caught when it runs, data from outside is
checked once where it enters, and the tests say what the code is for.

It is made for software that has to last: code that grows, that other people
change, and that passes data between modules, services and teams. It is not a
kit for prototypes. It still keeps small parts small: a shape goes where a
mistake can travel, and a one-off script inside your project stays plain.

The thinking behind it is in **[MANIFESTO.md](MANIFESTO.md)**. Start there.

## The rules

1. **Only parts that do not move can be trusted.**
2. **Shape over checks.**
3. **If it exists, it is valid.**
4. **Check once, at the spring.**
5. **Test the intent, not the code.**
6. **Mental load, not lines of code.**
7. **A rule names its enforcer, or carries its why, or goes.**

Each one with its why and an example: [the rules](MANIFESTO.md#the-rules).

## How it works

<p align="center">
  <img src="assets/streams.svg" alt="Three streams for one feature. A postcode from the checkout form is checked once and becomes a Postcode; what fails the check goes back to the form. The warehouse's stock already flows through stock_of and is joined, not dug again. The clock gives today's date. All three meet in delivery_date, which gives the checkout a Date.">
</p>

Before the first line, the agent maps the feature as streams: the path each
piece of information takes from where it enters the code to where it is used.
It asks three questions. Which streams does the feature need? Which already
flow, so it can join them instead of digging a second channel? And what does
the language guarantee, so each stream rides on what the compiler enforces?

Then plan, implement, critique. The critique is the valve. A finding that says
"add a check" is first asked whether a shape can make the mistake impossible.
If it can, the shape changes and the check is never written. If it cannot, the
check goes to the spring, with a test that feeds it the bad data.

The tests follow the same line. What the code computes keeps its test. Every
check at a spring is fed the bad data it must refuse. Where the toolchain can
check it, one line per shape proves that the wrong use still does not compile.
Where it cannot, as in Go, the compiler alone holds the shape. A test goes when
the behaviour it pins goes, or when the compiler catches what it caught.

The whole method, traced through one feature down to the code:
[before the first line](MANIFESTO.md#before-the-first-line).

## Hard and soft languages

Rust holds what it promises, so the agent leans on the compiler and clippy.
Go is firm ground with holes: its compiler checks every type, and golangci-lint
closes the choices the language leaves open. TypeScript and Python are softer
ground, where types are erased or only hints. There the agent lines the channel
with a strict checker and lint rules, and keeps the runtime check wherever the
types are gone. The enforcers for each rule:
[hard and soft languages](MANIFESTO.md#hard-and-soft-languages).

Each language has a [working example](examples) that CI runs. It must pass
clean, and every enforcer the docs name is fed a file it must refuse, so the
docs cannot promise what the tools do not do.

## The prompt

Tesla Valve is one prompt: [`skills/tesla-valve/SKILL.md`](skills/tesla-valve/SKILL.md),
with a reference for each language. The compact version, for agents that read
a rules file, is [`AGENTS.md`](AGENTS.md).

A shape counts only where the project's compiler or CI enforces it. The second
skill, [`prepare`](skills/prepare/SKILL.md), sets that up, once per project
and only when you start it. It shows what is missing, proposes the compiler
settings, lint rules and CI steps as a diff, and once you agree, proves that
each one refuses the file it must refuse. Until then, the agent keeps the
runtime checks a missing enforcer would replace.

The third, [`reshape`](skills/reshape/SKILL.md), brings existing code into those
shapes, in a scope you name and one stream at a time. Checks become shapes or
move to the spring, and the tests the compiler now covers go, each naming what
holds it now. How to start both in each host is in [INSTALL.md](INSTALL.md).

## Does it work?

We let AI agents grow two small games over six steps, with Tesla Valve and
without. A blind judge, always from a different vendor than the model that
wrote the code, preferred the Tesla Valve code in 28 of 32 comparisons. The
other code won 2, and 2 were ties. The judge found none of the 64 projects
over-built, on either side. The agents took a median 12% longer with Tesla
Valve, and wrote 4% more code.

When agents refactored code that had grown without it, the judge preferred the
Tesla Valve result 22 to 8. But the strongest model over-built half of its
refactors, so by the criteria we set beforehand, it does not count as a win.

It did not make the code measurably more correct, and on bug fixes in mature
open-source projects it made no difference. The method, the numbers and the
limits: **[RESULTS.md](RESULTS.md)**. The benchmark itself, to run yourself:
[`benchmark/`](benchmark).

## Install

**Claude Code**, as two separate prompts:

```
/plugin marketplace add Aquilo-Solution-S/tesla-valve
```
```
/plugin install tesla-valve@tesla-valve
```

**Codex:**

```bash
codex plugin marketplace add Aquilo-Solution-S/tesla-valve
codex plugin add tesla-valve@tesla-valve
```

Then open `/hooks` in Codex, trust the plugin's two hooks, and start a new
thread.

**Grok, Cursor and any other agent:** step by step in **[INSTALL.md](INSTALL.md)**.
Most agents also read [`AGENTS.md`](AGENTS.md): copy it into your project.

## FAQ

**Does it mean fewer tests?**
Fewer tests of shape, and not one fewer of meaning. Whether a backorder carries
its restock days is the compiler's job. Whether an order placed on Tuesday
arrives on Thursday is a test's job, and that test stays.

**Is it about writing less code?**
No. The measure is whether someone who did not write the code understands it
at first glance. A shape often makes code shorter, because the checks go away.
But a type that needs a paragraph of comment loses to a plain check.

**Is it for quick projects?**
No. A prototype that is thrown away next week gains little from shapes. Tesla
Valve pays where code lives on: where the next change comes from someone who
did not write it, and where a mistake can travel into another module. There,
the shape that made it impossible is cheaper than the bug it would have been.

**My language is soft. Is it still worth it?**
Yes, with the channel lined. In TypeScript, `strict` and a handful of lint rules
close most of the leaks; in Python, pyright in strict mode and ruff do. Where
the types are gone, at JSON and at public APIs that untyped code can call, the
runtime check stays.

**Why "Tesla valve"?**
In 1920 Nikola Tesla patented a valvular conduit: a channel that lets fluid
through in one direction and, flowing back, turns it against itself, without a
single moving part. That is what we want from code.

## License

[MIT No Attribution](LICENSE): use, copy and change it, also without
naming us.

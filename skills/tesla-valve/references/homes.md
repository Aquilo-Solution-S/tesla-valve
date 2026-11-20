# Homes

A rule's home is chosen by what can check it. Every home is checked by a tool,
or is the input a tool acts on. A rule no tool can check is a judgment: one
short prose rule, with its why and one example.

| kind of rule | home | what checks it |
| --- | --- | --- |
| a shape, an invariant, a protocol | the type that carries it in the code; where more than one codebase must keep it, the rule is ahead of the code, or no type can state it, declarations in a spec language the compiler checks: [Lean](lean.md) | the compiler; and the code, by what it emits, replays or names |
| vocabulary | the type or the constructor that carries the word, in the code or in the spec: its docstring defines it | the compiler; emitters carry the names into the code |
| a worked example, a case | an `example` or a `#guard` in the spec; in the code, the test that runs the case: beside the type, or end to end for a use case | the compiler; the test run |
| what a screen shows and does | an implemented mockup: the product's own components in a mock mode, fed fixtures typed by the generated contract | the type checker on the fixtures; a browser spec that walks the mockup |
| a UX law a shape can hold | that shape: one token file, a name type where ids must not show | the compiler or the build |
| a process flow: states, steps, who | what takes the steps: where the code does, the type or the spec, as the protocol in the first row; where a process tool does, its config. A Mermaid state diagram is that home only where the tool reads it as its transitions, or a test compares the two; otherwise it is a map, below | the compiler, the tool, or that test |
| a process constraint | the tool or gate that refuses the wrong version | that tool |
| operations | the declarative config its tool applies (units, manifests, infrastructure as code), and scripts for procedures | the tool's apply; its status shows drift |
| a map: what runs where, how a call flows, any diagram no tool reads | a picture of its home (the config, the transitions), generated from it where it can be. Drawn by hand, it is a judgment: it stays in one place and names what it is drawn from, so a reader can check the picture against it | the generator; judgment where nothing generates it |
| the structure of a file | one template per file type, used by a scaffold command | the scaffold; the compiler or a lint for the required parts |
| where a file goes | a check in the gate, derived from the tree | the gate |
| a pointer | a reference by the target's name, or a relative link | the compiler in the spec; a link check in the gate for docs; a check that every name the code cites resolves |
| a deferral: "later", "next" | a gap issue | the tracker |

**Where the project does not run a row's checker,** the rule does not move
there yet. A checker counts where this project runs it: in its compiler, in
its CI, or as the tool that acts on the input. Open those to find out: a
spec, a lint table or a test in the tree that none of them runs does not
count. Until one does, the rule stays what a judgment is: one short prose
rule in one place. A new home nothing checks, as a spec no gate builds or a
mockup no browser spec walks, is one more document that drifts.

The missing checker is a gap: one gap issue per checker, not per rule. It
names the checker, what the project runs today, the rules that wait for it,
and done-when: a file the checker refuses. A rule that newly waits is added
to it. Search the closed issues too, as:

```sh
gh issue list --label gap --state all --search "link check" --json number,title,stateReason
```

One closed as not planned is the project's decision not to build the
checker, and it is not filed again. Any other closed one is no answer: file
a new one. The enforcers the prepare skill lists for a language, its
compiler settings and lints, are one checker: one issue per language names
those that are missing or off, and a run of prepare that reports each one on
and proven closes it. Building a checker, or extending one that runs, is the
user's decision, not a part of another task.

So is changing a gate that enforces what the tesla-valve skill removes, as a
lint that asks for a doc comment on every function, also where the comment
restates the code. Until the user decides, the gate holds. It gets one issue
in the same way, which names the gate and the rule it works against. Closed
as not planned, the project keeps its gate.

A pointer and a deferral do not wait for their checker: point to the home,
and file what was deferred as a gap issue, also where no link check runs and
no label exists yet. The link check that is missing is a gap of its own, as
above.

**A judgment has a home too:** one prose file, the one that those who must
follow the rule read first (the agents' rules file, the project's guide, a
runbook, a skill). It states the rule, its why and one example. Where two
files state it, that file keeps it and the other points to it. The steps a
person or an agent takes by hand are such a rule, until a script takes them.

**A record of a decision is not in the table, and not in the tree.** Nothing
checks it, and what it adds to its rules is timeline: who decided, when, and
the discussion. The decision is the change to the home. Its record is the
commit that makes the change and the issue that discussed it, or a decision
ledger the project keeps outside the tree. So a change that decides a rule
writes no record file.

A record file that is already in the tree gives up its rules, in a reshape
the user starts: each rule a checker of this project holds moves to its home
above, with its why, and every other one, a judgment, to the prose file just
named, written as the rule and not as the record. "On 3 March we agreed that
a review runs in a fresh session" becomes "a review runs in a fresh session:
the author's reasoning hides its own gaps". A design the record rejected
stays with the rule, as what the next change must not undo. Then the file
goes, and git keeps it.

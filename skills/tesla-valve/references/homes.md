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
mockup no browser spec walks, is one more document that drifts. Name the
gate to build in your reply. Building it, or extending one that runs, is the
user's decision, not a part of another task.

A missing checker is not a gap, and gets no issue. A gap issue is for a rule
the code does not hold yet: "the receiver gets vectors", and no provider is
wired. For a rule that is held and unchecked, naming the gate to build is
all.

The pointer row and the deferral row need no checker to be right: point to
the home, and file what was deferred as a gap issue, whether or not a link
check or a label is there.

**A judgment has a home too:** one prose file, the one that those who must
follow the rule read first (the agents' rules file, the project's guide, a
runbook, a skill). It states the rule, its why and one example. Where two
files state it, that file keeps it and the other points to it. The steps a
person or an agent takes by hand are such a rule, until a script takes them.

**A record of a decision is not in the table:** nothing checks it. Its rules
move, in the change that makes the decision or in a reshape the user starts:
each rule a checker of this project holds to its home above, with its why,
and every other one, a judgment, to the prose file just named, written as
the rule and not as the record. "On 3 March we agreed that a review runs in
a fresh session" becomes "a review runs in a fresh session: the author's
reasoning hides its own gaps". Who decided, when, and the discussion are the
issue and the commit. A record whose rules have all moved, or that a later
one replaced, has nothing left to say: it goes with the last of them, and
git keeps it.

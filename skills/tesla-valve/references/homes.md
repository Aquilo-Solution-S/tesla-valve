# Homes

A rule's home is chosen by what can check it. Every home is checked by a tool,
or is the input a tool acts on. A rule no tool can check is a judgment: one
short prose rule, with its why and one example.

| kind of rule | home | what checks it |
| --- | --- | --- |
| a shape, an invariant, a protocol | the type that carries it in the code; where more than one codebase must keep it, the rule is ahead of the code, or no type can state it, declarations in a spec language the compiler checks: [Lean](lean.md) | the compiler; and the code, by what it emits, replays or names |
| vocabulary | the same declarations: a word is a type or a constructor the model uses, and its docstring defines it | the compiler; emitters carry the names into the code |
| a worked example, a case | an `example` or a `#guard` in the spec; where the rule's home is a type in the code, a test beside it | the compiler; the test run |
| what a screen shows and does | an implemented mockup: the product's own components in a mock mode, fed fixtures typed by the generated contract | the type checker on the fixtures; a browser spec that walks the mockup |
| a UX law a shape can hold | that shape: one token file, a name type where ids must not show | the compiler or the build |
| a process flow: states, steps, who | a Mermaid state diagram that the process tool reads as its transitions, or that a test compares with them | the tool, or that test |
| a process constraint | the tool or gate that refuses the wrong version | that tool |
| operations | the declarative config its tool applies (units, manifests, infrastructure as code), and scripts for procedures | the tool's apply; its status shows drift |
| a map of what runs where | Mermaid, generated from the config where it can be | the generator; judgment where nothing generates it |
| the structure of a file | one template per file type, used by a scaffold command | the scaffold; the compiler or a lint for the required parts |
| where a file goes | a check in the gate, derived from the tree | the gate |
| a pointer | a reference by the target's name, or a relative link | the compiler in the spec; a link check in the gate for docs; a check that every name the code cites resolves |
| a deferral: "later", "next" | a gap issue | the tracker |

A prose record of a decision is not in the table: nothing checks it. Its rules
move to the homes above, and what is left of it (who, when, the discussion)
is the issue and the commit.

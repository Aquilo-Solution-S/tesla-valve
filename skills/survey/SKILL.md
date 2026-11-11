---
name: survey
description: >
  Survey a part of a codebase the Tesla Valve way: a deep architecture review
  that follows each stream from spring to goal and reports where the flow is
  not natural, such as second channels, layers that only carry, streams that
  touch outside a contract, moving parts, uneven quality, and docs that say
  what the code does not do. It reads and reports, and changes nothing. Run it
  only when the user asks for it, on a topic the user names: it reads far
  beyond any one task.
argument-hint: "<topic>[, <focus>]"
disable-model-invocation: true
---

# Survey

The tesla-valve skill looks at the code one task touches, and the reshape
skill at the checks in one scope. Neither asks whether the landscape still
flows after fifty tasks have each dug where they stood. This skill asks that.
It reads and it reports. It changes no code, no config and no document.

It holds no rules of its own: every finding follows from the
[tesla-valve skill](../tesla-valve/SKILL.md). Read it first, and its reference
for each language in the scope. What this skill adds is the method, and the
same view from further away: module depth, coupling and scale are not other
subjects, they are what a stream looks like from above.

## 1. Topic and focus

The user names a topic and, after it, a focus:
`checkout, where the delivery date is decided`.

- **The topic says where to look:** a module, a subsystem, or a stream such as
  "how a price reaches the invoice". Resolve it to paths.
- **The focus says what the user wants to know.** It orders the survey and does
  not blind it: a severe finding outside the focus is still reported. Without a
  focus, every dimension in step 4 counts the same.
- **Without a topic**, ask for one before you gather anything, and offer the
  two or three areas that changed most in the recent history as candidates: a
  fault there is paid again with every change. A survey of a topic nobody
  named spends a deep review on a guess.

With a topic, tell the user in one line which paths and which question you
took from it before you read further, and do not wait for an answer.

## 2. Gather cheap, judge here

Most of a survey is gathering: which files, who calls what, where a name is
spelled, what CI runs. The judging is the smaller part, and the one that needs
the strongest model.

- Where the host has subagents, give them the gathering, on a cheaper model
  where the host lets you choose one: one bounded question each, with a cap on
  the length of the answer. The map, the findings and the ranking stay with
  you. A topic you can read in one sitting needs no helpers: a brief longer
  than the reading it saves is load.
- A gathered answer is a claim. Open the lines it cites before a finding rests
  on them.
- Nothing is written into the project, by you or by anyone you hand work to.
  A helper does not know that unless its brief says so: say it in every brief,
  and give the helper read-only tools where the host has them. Notes you keep
  on the way go into the system's temporary directory.

## 3. Map

Read three things, in this order.

1. **What the project says about itself:** its architecture docs, its decision
   records, the instructions it gives its agents. These are claims the survey
   tests, and decisions it does not reopen without a cost to show.
2. **What holds:** the enforcers in its config and its CI. A rule that nothing
   enforces is a convention, whatever the docs call it.
3. **The streams:** map each stream of the topic the way the tesla-valve skill
   maps a feature: spring, check, refusal, confluence, goal. Add what a task
   never needs to write down: every layer the stream crosses on its way, and
   every place that keeps a copy of its fact.

Findings attach to streams, not to files. "The postcode is checked in three
places" is a finding. "`checkout.rs` is long" is not.

## 4. Read the map along each dimension

Every dimension asks the same question from another side: is the right path
the path of least resistance here, and does the wrong path work against
itself? Each is a judgment call, so each carries its why and one example.

The dimensions are ways to look, not a form to fill in. Most of a healthy
topic is clean along most of them, and a finding kept so that a dimension has
one is load. A dimension with nothing to report is left out of the report.

- **Springs.** Does each stream from outside have one check, where it enters,
  and does every refusal go somewhere that says why? A value used before it is
  parsed can be anything. A value checked again downstream has two checks that
  drift apart. A refusal turned into a default hides the bad data from the one
  who could fix it: an unknown stock status that becomes `in_stock`.
- **Second channels.** Is each fact decided in one place? Two sources of truth
  drift, and no type catches it: `delivery_date` reads the warehouse itself
  while `stock_of` already does.
- **Depth.** How many layers does a stream cross, and how many of them change
  it? A layer that only carries is one more place every reader visits and
  every change touches. Delete it in thought: if nothing has to be written
  anywhere else, it carried nothing. A `StockService` that forwards each call
  to `StockRepository` is such a layer. The opposite counts too: one function
  where five streams meet and nobody can name the confluence.
- **Coupling.** Streams meet at a confluence, through a contract. Where else do
  they touch? A change to one stream that forces edits in modules that never
  use it will be made wrong or not at all. Look for a module that reaches into
  the fields of another, a mutable value two streams share, and a context that
  carries ten values to a function that reads one. And look at the direction:
  water flows one way. The postcode parser that imports the checkout page to
  word its error flows back upstream, and neither can change alone.
- **Moving parts.** What is only right if someone remembers it, chooses it or
  times it? A flag that picks the behaviour, an `init()` that must run first, a
  list of handlers every new handler must be added to by hand.
- **Stale facts.** Where is a fact about the world read in one place and acted
  on in another? Between the two the world moves: stock is read when the page
  loads and decremented, unconditionally, when the order is placed.
- **Volume.** What happens to the channel when the stream carries a thousand
  times more, or when the tenth variant arrives? Find where it narrows: a
  whole table read into memory, one round trip per order line, one lock around
  every order. Count the places a new variant must edit. Ask this only for
  growth that a feature or the project's own goals name: a channel dug for
  water that never comes is load.
- **Even ground.** Is the same thing done the same way across the scope? Each
  further way is a convention the reader must learn, and a place where the
  stricter rule does not reach: orders parse into types and returns pass
  strings, or a lint is on in one package and off in the next. Name the
  difference, and which way the project's enforcers favour.
- **Said and built.** Where does a doc, a decision record, a comment or a name
  say what the code does not do? The words are a second channel, and the next
  change will trust them: `// validated upstream` above a value that nothing
  upstream validates.
- **Tests.** Which intent has no test, above all across parts: a protocol,
  atomicity, recovery from a failure? Which check at a spring is never fed bad
  data? Which tests pin only a shape the compiler already holds?
- **Load.** What does no feature need? A guard for a case that cannot occur, an
  option nobody sets, an interface with one implementation and no second in
  sight, a channel no stream flows through any more.

## 5. Verify

A finding is a claim until it is checked. Each one that reaches the report:

- **cites `file:line`** that you opened yourself;
- **names its cost:** the wrong change it invites, or the wrong conclusion a
  reader draws. "This could be cleaner" names neither, and goes;
- **holds where the shape stops:** it does not ask for a shape that nothing in
  this project would enforce, or for types around a one-file script;
- **respects a decision:** what the project decided on purpose is a finding
  only where the code shows the cost. Then name the decision it reopens.

Then have each one attacked, by the most independent reader at hand:

1. A model from another vendor, where the user or the project already works
   with one: a second CLI, a review tool. A model from the same vendor shares
   your blind spots.
2. Otherwise a subagent with a fresh context.
3. Otherwise you, arguing the other side.

Give that reader the code and the bare claim, not your argument, and ask it to
refute the claim. It reads and writes nothing, like every helper in step 2: a
reader that cannot be held to that is not used, and you argue the other side
yourself. Run a second CLI read-only and with its input closed: one that waits
for a prompt never answers. A refuted finding goes. One you still hold against an
objection is reported with the objection. One round: a round of critique that
only rephrases is the last round.

## 6. Report

In the chat. Write a file only when the user asks for one.

1. **The answer to the focus**, in a sentence or two.
2. **The findings, ranked by what they cost**, and among equals by how far the
   mistake travels: out of the repository (a public API, stored data, another
   system), then across modules, then inside one. A race that loses an order
   inside one module comes before a stale sentence in a public README. For
   each:
   - the stream and what is wrong with it, with `file:line`;
   - what it costs;
   - what would hold it (a join, a shape, the spring, the commit, a deletion)
     and what enforces that. Where the enforcer is a compiler setting or a
     lint the project does not run yet, say that the prepare skill sets it up.

   Give the few worth acting on first in full, and the rest one line each. A
   report nobody reads to the end changes nothing. Where the topic is clean,
   say so, and name what you checked to know it.
3. **Rows for reshape:** the findings that are checks, in the plan table of the
   [reshape skill](../reshape/SKILL.md), with its columns (check, kind,
   becomes, held by, tests), so the user can hand them over as they are. A
   finding that is not a check gets no row.
4. **What the survey did not read**, so no silence is taken for a clean result.

The survey ends there. The user picks what happens next: reshape for the rows,
prepare for the enforcers, a task of its own for the rest.

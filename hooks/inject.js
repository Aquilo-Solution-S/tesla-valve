// Hands AGENTS.md to Claude Code and Codex at session start and to every
// subagent, so the rules hold without a copy in each project. The hook file
// passes the event name, so nothing here depends on what arrives on stdin.
const fs = require("node:fs");
const path = require("node:path");

const event = process.argv.at(-1);
const rules = fs.readFileSync(path.join(__dirname, "..", "AGENTS.md"), "utf8");

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: event,
    additionalContext: rules,
  },
}));

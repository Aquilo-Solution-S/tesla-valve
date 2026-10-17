"""The agents of the game benchmark: authors that write code in a sandbox, and judges that only read.

An author is an arm on a model. The arm decides the rules: `baseline` loads none, any other arm names a
plugin directory whose AGENTS.md the author receives as its global instructions. Codex models (gpt-*)
run through `codex exec`, every other model through `claude -p`. Both get the same sandbox: write the
workspace and the toolchains' own state, reach no network.

A cell lives inside this repository, below its AGENTS.md, and a baseline author must not read it: Codex reads
AGENTS.md only up to the cell's own git root, and Claude loads no CLAUDE.md (a canary file in a parent
directory reached neither, and reached both once loaded). Claude Code also refuses the Write tool inside a
loaded plugin's directory, which this repository is, so a Claude author loads a copy of the plugin, as an
installed plugin is one.
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

SESSION_TIMEOUT = 2700          # step 1 builds a whole game
CI_CHARS = 4000                 # CI output handed back to the author is cut to its tail
WRITE_ONLY = ("Write the implementation and its tests. Do not install dependencies or start "
              "servers. Only the code you leave in the project is kept.")


def git(workdir: Path, *args) -> subprocess.CompletedProcess:
    """Harness git. It never signs: a contributor's signing key is not for throwaway commits, and its
    agent can stop answering mid-run. A failed call stops the cell, because a commit that silently fails
    shifts every later diff."""
    return subprocess.run(["git", "-c", "user.email=bench@local", "-c", "user.name=bench",
                           "-c", "commit.gpgsign=false", *args], cwd=workdir, capture_output=True, text=True,
                          check=True)


class Author:
    """One author for one session and its CI fix round. `rules` is the plugin directory of the arm, or
    None for baseline; `writable` lists the paths outside the workspace its sandbox may write. A Codex
    author keeps its session logs in its own home, so `logs` names where they go when it closes; Claude
    Code keeps them in ~/.claude/projects anyway."""

    def __init__(self, model: str, rules: Path | None, writable: list[str], logs: Path | None = None):
        if rules is not None and not (rules / "AGENTS.md").is_file():
            raise SystemExit(f"{rules} holds no AGENTS.md, so the arm would run without rules")
        self.model, self.rules, self.writable, self.logs = model, rules, writable, logs
        self.codex = model.startswith("gpt-")
        self.home = self._codex_home() if self.codex else self._claude_home()

    def _codex_home(self) -> Path:
        """A CODEX_HOME holding only a link to the user's login, so none of the user's own instructions,
        hooks, skills or MCP servers load. The arm's AGENTS.md becomes the global instructions."""
        home = Path(tempfile.mkdtemp(prefix="author-"))
        (home / "auth.json").symlink_to(Path.home() / ".codex" / "auth.json")
        roots = ", ".join(json.dumps(r) for r in self.writable)
        (home / "config.toml").write_text('approval_policy = "never"\nsandbox_mode = "workspace-write"\n'
                                          f"\n[sandbox_workspace_write]\nwritable_roots = [{roots}]\n")
        if self.rules is not None:
            shutil.copy(self.rules / "AGENTS.md", home / "AGENTS.md")
        return home

    def _claude_home(self) -> Path | None:
        """A directory holding a copy of the arm's plugin: the files its repository would commit, as an
        installed plugin is a clone, and not the benchmark, which holds the cells. None for baseline."""
        if self.rules is None:
            return None
        home = Path(tempfile.mkdtemp(prefix="author-"))
        listed = git(self.rules, "ls-files", "-z", "--cached", "--others", "--exclude-standard").stdout
        for name in listed.split("\0"):
            if name and not name.startswith("benchmark/") and (self.rules / name).is_file():
                (home / "plugin" / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.rules / name, home / "plugin" / name)
        return home

    def run(self, prompt: str, workdir: Path, resume: str | None = None) -> dict:
        if self.codex:
            return self._codex(prompt, workdir, resume)
        return self._claude(prompt, workdir, resume)

    def _codex(self, prompt: str, workdir: Path, resume: str | None) -> dict:
        cmd = [shutil.which("codex") or "codex", "exec"] + (["resume", resume] if resume else [])
        cmd += ["-m", self.model, "--skip-git-repo-check", "--json"] + ([] if resume else ["-C", str(workdir)])
        cmd.append(prompt + "\n\n" + WRITE_ONLY)
        start = time.monotonic()                       # codex reports no duration of its own
        r = subprocess.run(cmd, cwd=workdir, env={**os.environ, "CODEX_HOME": str(self.home)},
                           capture_output=True, text=True, timeout=SESSION_TIMEOUT, stdin=subprocess.DEVNULL)
        thread, usage = resume, {}
        for line in r.stdout.splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("type") == "thread.started":
                thread = e.get("thread_id")
            elif e.get("type") == "turn.completed":
                usage = e.get("usage") or usage
        return {"id": thread, "cost": None, "out_tokens": usage.get("output_tokens"),
                "ms": round((time.monotonic() - start) * 1000)}

    def _claude(self, prompt: str, workdir: Path, resume: str | None) -> dict:
        """dontAsk refuses whatever is not listed; bypassPermissions would let a sandboxed command reach
        any host. Edit and Write stay inside the workspace; Bash runs in Claude Code's sandbox."""
        sandbox = {"enabled": True, "autoAllowBashIfSandboxed": True, "allowUnsandboxedCommands": False,
                   "failIfUnavailable": True, "filesystem": {"allowWrite": self.writable}}
        cmd = [shutil.which("claude") or "claude", "-p", prompt, "--model", self.model,
               "--permission-mode", "dontAsk", "--allowedTools", "Read,Glob,Grep,Bash,Edit(./**),Write(./**)",
               "--settings", json.dumps({"sandbox": sandbox}), "--output-format", "json",
               "--setting-sources", "project,local", "--strict-mcp-config", "--append-system-prompt", WRITE_ONLY]
        if self.home:
            cmd += ["--plugin-dir", str(self.home / "plugin")]
        if resume:
            cmd += ["--resume", resume]
        env = {**os.environ, "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
        r = subprocess.run(cmd, cwd=workdir, env=env, capture_output=True, text=True, timeout=SESSION_TIMEOUT,
                           stdin=subprocess.DEVNULL)
        try:
            j = json.loads(r.stdout)
        except json.JSONDecodeError:
            return {"id": None, "cost": None, "error": (r.stderr or r.stdout)[-300:]}
        return {"id": j.get("session_id"), "cost": j.get("total_cost_usd"), "turns": j.get("num_turns"),
                "ms": j.get("duration_ms")}

    def close(self):
        if self.logs and self.codex and (self.home / "sessions").is_dir():
            shutil.copytree(self.home / "sessions", self.logs, dirs_exist_ok=True)
        if self.home:
            shutil.rmtree(self.home, ignore_errors=True)   # removes a login link, never the login


def session_with_ci(author: Author, prompt: str, workdir: Path, check) -> dict:
    """One session, the project's CI, and one fix round in the same session if CI is red."""
    s = author.run(prompt, workdir)
    green, output = check(workdir)
    rec = {"session": s, "ci_red": not green}
    if not green and s.get("id"):
        rec["fix"] = author.run(f"CI failed on your change. Fix the cause, not the check.\n\n{output}",
                                workdir, resume=s["id"])
        rec["ci_red_after_fix"] = not check(workdir)[0]
    return rec


def judge(system: str, user: str, model: str) -> str:
    """One verdict from a judge that can only read: a Codex model in a read-only sandbox, or Claude with
    no tools. Neither loads the user's instructions, plugins or MCP servers."""
    with tempfile.TemporaryDirectory(prefix="judge-") as d:
        cwd = Path(d) / "cwd"
        cwd.mkdir()
        if model.startswith("gpt-"):
            home, out = Path(d) / "home", Path(d) / "verdict.txt"
            home.mkdir()
            (home / "auth.json").symlink_to(Path.home() / ".codex" / "auth.json")
            (home / "config.toml").write_text('approval_policy = "never"\nsandbox_mode = "read-only"\n')
            prompt = f"{system}\n\nJudge only from the text below. Run no commands. Reply with the JSON object alone.\n\n{user}"
            subprocess.run([shutil.which("codex") or "codex", "exec", "-m", model, "-c", "model_reasoning_effort=medium",
                            "--skip-git-repo-check", "--ephemeral", "--sandbox", "read-only", "-o", str(out), "-"],
                           input=prompt, cwd=cwd, env={**os.environ, "CODEX_HOME": str(home)},
                           capture_output=True, text=True, timeout=600)
            return out.read_text() if out.exists() else ""
        env = {**os.environ, "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
        r = subprocess.run([shutil.which("claude") or "claude", "-p", "--model", model, "--system-prompt", system,
                            "--output-format", "json", "--tools", "", "--setting-sources", "project,local",
                            "--strict-mcp-config"], input=user, cwd=cwd, env=env,
                           capture_output=True, text=True, timeout=600)
        try:
            return json.loads(r.stdout)["result"]
        except (json.JSONDecodeError, KeyError):
            return ""

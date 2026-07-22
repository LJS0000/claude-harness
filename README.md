# claude-harness

Personal Claude Code safety harness packaged as a plugin. Ships safety hooks and a full multi-agent engineering workflow.

## What's included

### Safety hooks

- **`block_dangerous.py`** — blocks destructive Bash commands (`rm`, `git reset --hard`, `git push --force`, `DROP TABLE`, etc.)
- **`protect_sensitive.py`** — blocks reads/writes of `.env`, `credentials`, `*.pem`, and sensitive Bash patterns (`printenv`, `curl | sh`, etc.)
- **`check_updates.py`** — daily auto-update check against the upstream plugin (once per 24 h)

### Multi-agent workflow (`/harness`)

Invoke with a natural language problem description:

```
/harness Intermittent 500 error occurs during login
```

The orchestrator estimates difficulty and runs a mode-appropriate subset of these agents:

| Agent | Role |
|---|---|
| `investigator` | Explores the codebase and identifies root cause |
| `architect` | Produces a minimal, safe implementation plan |
| `challenger` | Proposes 2–3 alternative approaches with trade-off analysis (complex only) |
| `implementer` | Executes the chosen plan (codex CLI if available, else Claude) |
| `reviewer` | Checks the implementation against the approved plan |
| `retrospective` | Saves lessons learned for future sessions (complex only) |

Models are not pinned per agent. The orchestrator decides each agent's model right before invoking it, based on the difficulty mode, the problem scope, and what the previous stage's artifacts revealed. Two rules bound that judgment:

- Pipeline agents (investigator through reviewer) never go below `opus` — if the problem is trivial enough for a smaller model, it wouldn't be going through the harness in the first place.
- Omitting the model makes the agent inherit the session model, so when the session runs on something above opus, judgment-heavy stages (design, review, complex implementation) get that model automatically.

The only exception is `retrospective`, a mechanical summarization role that always runs on `haiku`. Model aliases resolve to the latest generation, so the harness picks up new releases without config changes.

Modes drop steps to match scope: `simple` runs architect → implementer only; `medium` adds investigator + reviewer + PR; `complex` runs everything including challenger and retrospective.

Two principles guard output quality regardless of which models run the pipeline:

- **Evidence gates** — every stage produces runnable evidence, not claims. The investigator reproduces the problem with a command, the architect ends every plan with verification commands, the implementer actually runs them (`verification.txt`), and the reviewer re-runs them independently instead of trusting the implementer's transcript.
- **Cross-model review** — implementation and review are done by different model families whenever possible. When codex implements, Claude reviews; when Claude implements directly, the reviewer runs an additional read-only codex counter-review and triages its findings as taken/rejected.

At session end the orchestrator reports total token usage and suggests `/compact` when cumulative `cache_read` exceeds 1M tokens.

**Design always uses Claude.** codex CLI (when available) implements the plan and serves as a second pair of eyes during review.

### Pipeline UX

- **Task list** — Step 1.6 registers mode-appropriate tasks (2/6/8 depending on mode) via `TaskCreate`; each step toggles `in_progress`/`completed` so the progress is visible in real time.
- **Structured choices** — direction selection (Step 5), removal approval (Step 6.3), PR creation (Step 11-B) and difficulty confirmation (Step 1.5) use `AskUserQuestion` instead of free-text input. `Other` always falls back to free-form.
- **Plan mode handoff** — if the session is already in plan mode when `/harness` runs, Step 6.3 calls `ExitPlanMode` to formalize approval of `chosen-plan.md`. Outside plan mode, the usual `AskUserQuestion` gate runs.
- **Walk-away notifications** — `PushNotification` fires before Step 5 (direction wait), Step 11-B (PR review wait), and at session-terminal events (PR created, PR cancelled, pipeline aborted before PR).
- **Plain-language summary** — Step 12 always outputs a "쉽게 말하면" block at the end of every session (regardless of mode or PR outcome). Three fixed bullets — *what changed*, *what to be aware of*, *cautions* — written without file paths, function names, or domain jargon, so important side effects aren't missed when you skim the output.

### codex integration

If `codex` CLI is installed and authenticated, the implementer delegates to it for code changes via the stable config-override interface:

```bash
codex exec -c sandbox_mode=danger-full-access -c approval_policy=never \
  -C "<worktree-dir>" --skip-git-repo-check --json - < chosen-plan.md
```

Session start (Step 1) probes codex (`--version`, `login status`, `exec --help`) and caches the result in `<session-dir>/codex-status.txt`. The implementer reuses that cache and falls back to Claude direct editing when codex is missing, unauthenticated, rate-limited, or fails. If codex modifies files outside the plan's "영향 파일" allowlist, the run aborts immediately (no automatic fallback) so the scope violation is visible.

If codex is not found on the first run, the implementer pauses with the install URL once (marker `.codex-prompted`); subsequent runs silently fall back. Set `HARNESS_USE_CODEX=0` to skip codex entirely.

Install codex: https://github.com/openai/codex

## Install

```
/plugin marketplace add LJS0000/claude-harness
/plugin install harness@jisu-harness
```

After installing, **remove any duplicate hook entries** from `~/.claude/settings.json` (`PreToolUse` / `PostToolUse`) — plugin hooks stack additively on top of user hooks, so leaving them causes double-firing.

## Update

```
/plugin update harness@jisu-harness
```

## What's blocked

| Hook | Event | Blocks |
|---|---|---|
| `block_dangerous` | `PreToolUse:Bash` | `rm`, `unlink`, `git reset --hard`, `git push --force`/`-f`, `git clean -f`, `git checkout .`, `git stash drop`, `git branch -D`, `DROP DATABASE/TABLE`, `TRUNCATE TABLE` |
| `protect_sensitive` | `PreToolUse:Bash` | `cat ... .env`, `printenv`, bare `env`, `curl \| bash`, `wget \| bash`, `echo $SECRET` |
| `protect_sensitive` | `PreToolUse:Edit\|Write\|MultiEdit\|Read` | `.env*`, `secret*`, `credential*`, `private_key*`, `*.pem`, `*.p12`, `*.pfx` |

## Local development

```
claude --plugin-dir ~/dev/claude-harness/plugins/harness
```

Then `/reload-plugins` after edits.

## License

MIT

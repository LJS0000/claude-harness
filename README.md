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

| Agent | Role | Model |
|---|---|---|
| `investigator` | Explores the codebase and identifies root cause | `claude-sonnet-4-6` |
| `architect` | Produces a minimal, safe implementation plan | `claude-sonnet-4-6` |
| `challenger` | Proposes 2–3 alternative approaches with trade-off analysis (complex only) | `claude-sonnet-4-6` |
| `implementer` | Executes the chosen plan (codex CLI if available, else Claude) | auto-selected |
| `reviewer` | Checks the implementation against the approved plan | `claude-sonnet-4-6` |
| `retrospective` | Saves lessons learned for future sessions (complex only) | `claude-sonnet-4-6` |

The orchestrator runs in the user's session model and selects the implementer model based on difficulty:

| Difficulty | Criteria | Model |
|---|---|---|
| Simple | 1–2 files, config/text/style changes | `claude-haiku-4-5` |
| Moderate | 2–5 files, general feature work | `claude-sonnet-4-6` |
| Complex | 5+ files, architecture/algorithm/concurrency | `claude-opus-4-6` |

Modes drop steps to match scope: `simple` runs architect → implementer only; `medium` adds investigator + reviewer + PR; `complex` runs everything including challenger and retrospective.

At session end the orchestrator reports total token usage and suggests `/compact` when cumulative `cache_read` exceeds 1M tokens.

**Design and review always use Claude.** Only the implementer uses codex CLI (when available).

### Pipeline UX

- **Task list** — Step 1.6 registers mode-appropriate tasks (2/6/8 depending on mode) via `TaskCreate`; each step toggles `in_progress`/`completed` so the progress is visible in real time.
- **Structured choices** — direction selection (Step 5), removal approval (Step 6.3), PR creation (Step 11-B) and difficulty confirmation (Step 1.5) use `AskUserQuestion` instead of free-text input. `Other` always falls back to free-form.
- **Plan mode handoff** — if the session is already in plan mode when `/harness` runs, Step 6.3 calls `ExitPlanMode` to formalize approval of `chosen-plan.md`. Outside plan mode, the usual `AskUserQuestion` gate runs.
- **Walk-away notifications** — `PushNotification` fires before Step 5 (direction wait), Step 11-B (PR review wait), and at session-terminal events (PR created, PR cancelled, pipeline aborted before PR).

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

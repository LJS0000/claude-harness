# claude-harness

Personal Claude Code safety harness packaged as a plugin. Ships safety hooks and a full multi-agent engineering workflow.

## What's included

### Safety hooks

- **`block_dangerous.py`** — blocks destructive Bash commands (`rm`, `git reset --hard`, `git push --force`, `DROP TABLE`, etc.)
- **`protect_sensitive.py`** — blocks reads/writes of `.env`, `credentials`, `*.pem`, and sensitive Bash patterns (`printenv`, `curl | sh`, etc.)
- **`log_file_changes.py`** — audit log of all `Edit`/`Write`/`MultiEdit` operations to `~/.claude/logs/file-changes.jsonl`

### Multi-agent workflow (`/agent:harness`)

Invoke with a natural language problem description:

```
/agent:harness Intermittent 500 error occurs during login
```

The orchestrator runs 5 agents in sequence:

| Agent | Role | Model |
|---|---|---|
| `investigator` | Explores the codebase and identifies root cause | `claude-sonnet-4-6` |
| `architect` | Produces a minimal, safe implementation plan | `claude-sonnet-4-6` |
| `challenger` | Proposes 2–3 alternative approaches with trade-off analysis | `claude-sonnet-4-6` |
| `implementer` | Executes the chosen plan (codex CLI if available, else Claude) | auto-selected |
| `reviewer` | Checks the implementation against the approved plan | `claude-sonnet-4-6` |

The orchestrator (`harness`) runs on `claude-opus-4-6` and selects the implementer model based on difficulty:

| Difficulty | Criteria | Model |
|---|---|---|
| Simple | 1–2 files, config/text/style changes | `claude-haiku-4-5` |
| Moderate | 2–5 files, general feature work | `claude-sonnet-4-6` |
| Complex | 5+ files, architecture/algorithm/concurrency | `claude-opus-4-6` |

After investigation and after challenger complete, the orchestrator runs `/compact` to keep context lean before proceeding.

**Design and review always use Claude.** Only the implementer uses codex CLI (when available).

### codex integration

If `codex` CLI is installed, the implementer delegates to it for code changes:

```bash
codex exec --full-auto -C "<project-dir>" "$(cat chosen-plan.md)"
```

If codex is not found on the first run, the implementer pauses and guides you through installation. On subsequent runs it falls back to direct Claude editing silently.

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

## Audit log

File change log lives at `~/.claude/logs/file-changes.jsonl`. Each line is a JSON record:

```json
{"ts":"2026-04-09T09:12:34Z","session":"...","tool":"Edit","file":"/path/to/file","project":"repo-name","ok":true}
```

Tail it during development:
```
tail -f ~/.claude/logs/file-changes.jsonl
```

## Local development

```
claude --plugin-dir ~/dev/claude-harness/plugins/harness
```

Then `/reload-plugins` after edits.

## License

MIT

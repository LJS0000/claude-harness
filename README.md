# claude-harness

Personal Claude Code safety harness packaged as a plugin. Ships:

- **`block_dangerous.py`** — blocks destructive Bash commands (`rm`, `git reset --hard`, `git push --force`, `DROP TABLE`, etc.)
- **`protect_sensitive.py`** — blocks reads/writes of `.env`, `credentials`, `*.pem`, and sensitive-info Bash patterns (`printenv`, `curl | sh`, etc.)
- **`log_file_changes.py`** — audit log of all `Edit`/`Write`/`MultiEdit` operations to `~/.claude/logs/file-changes.jsonl`
- **`reviewer` subagent** — checks implementations against the approved plan and applies small safe fixes

## Install

```
/plugin marketplace add LJS0000/claude-harness
/plugin install harness@jisu-harness
```

After installing, **remove the duplicate hook entries** from `~/.claude/settings.json` (`PreToolUse` and `PostToolUse`) — plugin hooks stack additively on top of user hooks, so leaving them in causes double-firing.

## Update

```
/plugin update harness@jisu-harness
```

Or bump `version` in `plugins/harness/.claude-plugin/plugin.json`, push, tag, and users pull on next update check.

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

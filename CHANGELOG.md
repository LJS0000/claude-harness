# Changelog

## 0.1.2

- Remove `hooks` field from `plugin.json`. The `hooks/hooks.json` path is auto-discovered like `agents/`; declaring it explicitly caused `/doctor` to report `Duplicate hooks file detected` and the entire hook chain failed to load.

## 0.1.1

- Remove invalid `agents` field from `plugin.json` — the `agents/` directory is auto-discovered by Claude Code. The explicit field caused manifest validation to fail on install.

## 0.1.0

- Initial release. Ported from `~/.claude/setup-harness.sh`.
- Hooks: `block_dangerous.py`, `protect_sensitive.py`, `log_file_changes.py`.
- Agent: `reviewer`.

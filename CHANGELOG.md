# Changelog

## 0.2.1

- Migrate `harness` orchestrator from agent to skill (`plugins/harness/skills/harness/SKILL.md`). Users can now invoke the full workflow via `/harness <문제>` — the previous `/agent:harness` syntax was invalid in Claude Code.
- Add `auto-update` hook (`check_updates.py`) that checks for new plugin versions on startup.
- Add `CLAUDE.md` with commit conventions (Conventional Commits) and release/tag procedures.

## 0.2.0

- Add multi-agent engineering workflow: `investigator → architect → challenger → implementer → reviewer`.
- Add `harness` orchestrator agent (`claude-opus-4-6`) that coordinates the full pipeline.
- Add `investigator` agent — explores the codebase, identifies root cause, writes `investigation.md`.
- Add `architect` agent — produces a minimal, safe implementation plan in `architecture.md`.
- Add `challenger` agent — proposes 2–3 alternative approaches with trade-off analysis in `alternatives.md`.
- Add `implementer` agent — executes the chosen plan via codex CLI if available, otherwise direct Claude editing.
- Orchestrator selects implementer model based on difficulty: `claude-haiku-4-5` / `claude-sonnet-4-6` / `claude-opus-4-6`.
- Orchestrator runs `/compact` after investigator and after challenger to keep context lean.
- First codex-not-found occurrence pauses and guides the user through installation; subsequent runs fall back silently.
- Add `"agents": "./agents/"` to `plugin.json` — required for all agents to appear in the agents dialog.
- Session state persisted to `~/.claude/harness-sessions/<session-id>/` for auditability.

## 0.1.2

- Remove `hooks` field from `plugin.json`. The `hooks/hooks.json` path is auto-discovered like `agents/`; declaring it explicitly caused `/doctor` to report `Duplicate hooks file detected` and the entire hook chain failed to load.

## 0.1.1

- Remove invalid `agents` field from `plugin.json` — the `agents/` directory is auto-discovered by Claude Code. The explicit field caused manifest validation to fail on install.

## 0.1.0

- Initial release. Ported from `~/.claude/setup-harness.sh`.
- Hooks: `block_dangerous.py`, `protect_sensitive.py`, `log_file_changes.py`.
- Agent: `reviewer`.

#!/usr/bin/env python3
"""Auto-update harness plugin from GitHub on session start (once per day)."""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

PLUGIN_KEY = "harness@jisu-harness"
REPO = "LJS0000/claude-harness"
PLUGIN_PATH_IN_REPO = "plugins/harness"
CHECK_INTERVAL = 86400  # 24 hours


def fetch_json(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "claude-harness-updater/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def main():
    cooldown_file = Path.home() / ".claude" / "plugins" / ".harness_update_check"
    now = time.time()

    if cooldown_file.exists():
        try:
            last_check = float(cooldown_file.read_text().strip())
            if now - last_check < CHECK_INTERVAL:
                return
        except (ValueError, OSError):
            pass

    installed_plugins_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    if not installed_plugins_path.exists():
        return

    try:
        installed = json.loads(installed_plugins_path.read_text())
    except (json.JSONDecodeError, OSError):
        return

    plugin_installs = installed.get("plugins", {}).get(PLUGIN_KEY, [])
    if not plugin_installs:
        return

    install_info = plugin_installs[0]
    installed_version = install_info.get("version", "0.0.0")
    install_path = install_info.get("installPath", "")

    if not install_path:
        return

    # Fetch latest version from GitHub
    try:
        plugin_json_url = f"https://raw.githubusercontent.com/{REPO}/main/{PLUGIN_PATH_IN_REPO}/.claude-plugin/plugin.json"
        latest_info = fetch_json(plugin_json_url)
        latest_version = latest_info.get("version", "0.0.0")
    except Exception:
        cooldown_file.write_text(str(now))
        return

    cooldown_file.write_text(str(now))

    if _version_tuple(latest_version) <= _version_tuple(installed_version):
        return

    # New version — auto-update agents and hooks in cache
    print(f"\n[harness] Update available: {installed_version} → {latest_version}. Updating...", file=sys.stderr)

    try:
        _update_dir(PLUGIN_PATH_IN_REPO + "/agents", Path(install_path) / "agents")
        _update_dir(PLUGIN_PATH_IN_REPO + "/hooks", Path(install_path) / "hooks")
        _update_dir(PLUGIN_PATH_IN_REPO + "/skills", Path(install_path) / "skills")

        # Update installed_plugins.json
        install_info["version"] = latest_version
        install_info["lastUpdated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        installed_plugins_path.write_text(json.dumps(installed, indent=2))

        print(f"[harness] Updated to {latest_version}. New agents/hooks are active.\n", file=sys.stderr)
    except Exception as e:
        print(f"[harness] Auto-update failed: {e}. Run `/plugin update harness` to update manually.\n", file=sys.stderr)


def _update_dir(repo_path, local_dir):
    """Download all files in a GitHub directory recursively."""
    api_url = f"https://api.github.com/repos/{REPO}/contents/{repo_path}"
    entries = fetch_json(api_url)
    local_dir.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        if entry.get("type") == "dir":
            _update_dir(entry["path"], local_dir / entry["name"])
        elif entry.get("type") == "file":
            download_url = entry["download_url"]
            req = urllib.request.Request(download_url, headers={"User-Agent": "claude-harness-updater/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
            (local_dir / entry["name"]).write_bytes(content)


def _version_tuple(version_str):
    try:
        return tuple(int(x) for x in version_str.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


if __name__ == "__main__":
    main()

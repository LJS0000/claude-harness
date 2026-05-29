#!/usr/bin/env python3
"""ultraharness task 큐 자동 sync — Stop 훅에서 Popen으로 실행된다."""
import json
import os
import re
import subprocess
import sys
import time

UH_DIR = os.path.expanduser("~/.claude/ultraharness")
TASKS_FILE = os.path.join(UH_DIR, "tasks.jsonl")
LEARNINGS_DIR = os.path.expanduser("~/.claude/harness-learnings")
SYNC_STAMP_FILE = os.path.join(UH_DIR, "last_sync.txt")
SYNC_THROTTLE_SECS = 1800  # 30분

TODO_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".java", ".sh", ".md"}
TODO_MAX_COUNT = 50         # source=todo_comment 최대 수집 건수


def _log_skip(reason: str) -> None:
    """UH_DIR 내 uh_skip.log에 타임스탬프와 함께 기록한다 (디버깅용)."""
    try:
        log_path = os.path.join(UH_DIR, "uh_skip.log")
        with open(log_path, "a", encoding="utf-8") as f:
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            f.write(f"{ts} {reason}\n")
    except Exception:
        pass


def _should_run() -> bool:
    if not os.path.isdir(UH_DIR):
        # DEVNULL 환경이므로 stderr 불가 — 로그 파일도 쓸 수 없음(UH_DIR 없음)
        # 그냥 False 반환 (부모 hook report_uh_on_stop이 경고를 담당)
        return False
    if os.path.exists(SYNC_STAMP_FILE):
        try:
            mtime = os.path.getmtime(SYNC_STAMP_FILE)
            if time.time() - mtime < SYNC_THROTTLE_SECS:
                # throttle로 인한 skip은 로그에 기록 (디버깅용)
                _log_skip("sync_uh_tasks: throttled, skipping")
                return False
        except Exception:
            pass
    return True


def _update_stamp() -> None:
    try:
        with open(SYNC_STAMP_FILE, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass


def collect_github_issues(project_dir: str) -> list:
    """gh CLI로 open issues를 수집한다. gh 미설치 또는 오프라인이면 빈 리스트 반환."""
    import shutil
    if not shutil.which("gh"):
        return []

    # 프로젝트 디렉토리에서 remote URL 추론
    try:
        remote = subprocess.run(
            ["git", "-C", project_dir, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except Exception:
        return []

    # "github.com/owner/repo" 패턴 추출
    m = re.search(r'github\.com[:/]([^/]+/[^/.]+)', remote)
    if not m:
        return []
    repo = m.group(1)

    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", repo, "--state", "open",
             "--json", "number,title,labels,body", "--limit", "50"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        issues = json.loads(result.stdout)
    except Exception:
        return []

    label_priority = {"P0": "P0", "P1": "P1", "P2": "P2",
                      "critical": "P0", "high": "P1", "low": "P2"}
    items = []
    for issue in issues:
        number = issue.get("number")
        labels = [l.get("name", "") for l in issue.get("labels", [])]
        priority = "P1"
        for lbl in labels:
            if lbl in label_priority:
                priority = label_priority[lbl]
                break
        items.append({
            "source_id": f"gh#{number}",
            "title":     f"[GH#{number}] {issue.get('title', '')}",
            "description": (issue.get("body") or "")[:300],
            "priority":  priority,
            "tags":      ["github"],
        })
    return items


def collect_retrospective_tasks() -> list:
    """harness-learnings/*.json 에서 follow_up_tasks 배열을 수집한다."""
    if not os.path.isdir(LEARNINGS_DIR):
        return []
    items = []
    for fname in sorted(os.listdir(LEARNINGS_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(LEARNINGS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        session_id = data.get("session_id", fname.replace(".json", ""))
        for idx, task in enumerate(data.get("follow_up_tasks", [])):
            if not isinstance(task, dict):
                continue
            title = task.get("title", "")
            if not title:
                continue
            items.append({
                "source_id":   f"retro:{session_id}:{idx}",
                "title":       title,
                "description": task.get("description", ""),
                "priority":    task.get("priority", "P2"),
                "tags":        ["retrospective"],
            })
    return items


def collect_todo_comments(project_dir: str) -> list:
    """.gitignore를 존중하여 git ls-files 범위 내 TODO/FIXME를 수집한다."""
    if not project_dir or not os.path.isdir(project_dir):
        return []
    try:
        ls = subprocess.run(
            ["git", "-C", project_dir, "ls-files"],
            capture_output=True, text=True, timeout=10
        )
        if ls.returncode != 0:
            return []
        tracked = ls.stdout.splitlines()
    except Exception:
        return []

    import hashlib
    pattern = re.compile(r'#\s*(TODO|FIXME)[:\s](.+)', re.IGNORECASE)
    items = []
    seen_ids: set = set()
    for rel_path in tracked:
        if len(items) >= TODO_MAX_COUNT:
            break
        ext = os.path.splitext(rel_path)[1].lower()
        if ext not in TODO_EXTENSIONS:
            continue
        abs_path = os.path.join(project_dir, rel_path)
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    m = pattern.search(line)
                    if not m:
                        continue
                    text = m.group(2).strip()
                    # source_id = "file:<rel_path>:<lineno>:<content_hash5>"
                    content_hash = hashlib.sha1(f"{rel_path}:{lineno}:{text}".encode()).hexdigest()[:5]
                    sid = f"file:{rel_path}:{lineno}:{content_hash}"
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    items.append({
                        "source_id":   sid,
                        "title":       f"[TODO] {text[:80]}",
                        "description": f"{rel_path}:{lineno}",
                        "priority":    "P2",
                        "tags":        ["todo"],
                    })
                    if len(items) >= TODO_MAX_COUNT:
                        break
        except Exception:
            continue
    return items


def main():
    if not _should_run():
        sys.exit(0)
    _update_stamp()

    project_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    tasks_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manage_uh_tasks.py")

    def _run_sync(source: str, items: list) -> None:
        if not items:
            return
        try:
            subprocess.run(
                ["python3", tasks_py, "sync",
                 "--source", source,
                 "--items-json", json.dumps(items, ensure_ascii=False)],
                timeout=15
            )
        except Exception:
            pass

    _run_sync("github_issue",  collect_github_issues(project_dir))
    _run_sync("retrospective", collect_retrospective_tasks())
    _run_sync("todo_comment",  collect_todo_comments(project_dir))


if __name__ == "__main__":
    main()

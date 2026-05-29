#!/usr/bin/env python3
"""태스크 큐 CRUD: add / list / top / done / skip 서브커맨드."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

UH_DIR = os.path.expanduser("~/.claude/ultraharness")
TASKS_FILE = os.path.join(UH_DIR, "tasks.jsonl")
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

WARN_THRESHOLD = 1000

# noop 가드
if not os.path.isdir(UH_DIR):
    sys.exit(0)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_tasks() -> list:
    if not os.path.exists(TASKS_FILE):
        return []
    tasks = []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                tasks.append(json.loads(line))
            except Exception:
                continue
    if len(tasks) > WARN_THRESHOLD:
        print(
            f"경고: tasks.jsonl이 {len(tasks)}개 레코드를 초과했습니다. 오래된 done/skipped 레코드 정리를 고려하세요.",
            file=sys.stderr,
        )
    # 기존 jsonl 호환: 누락 필드를 기본값으로 채운다
    for t in tasks:
        t.setdefault("source", "manual")
        t.setdefault("source_id", "")
        t.setdefault("auto_managed", False)
    return tasks


def _save_tasks(tasks: list) -> None:
    tmp = TASKS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    os.replace(tmp, TASKS_FILE)


def _next_task_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    tasks = _load_tasks()
    today_prefix = f"task-{today}-"
    seq = sum(1 for t in tasks if t.get("task_id", "").startswith(today_prefix)) + 1
    return f"{today_prefix}{seq:03d}"


def _pending_sorted(tasks: list) -> list:
    pending = [t for t in tasks if t.get("status") == "pending"]
    return sorted(
        pending,
        key=lambda t: (PRIORITY_ORDER.get(t.get("priority", "P2"), 99), t.get("created_at", "")),
    )


def cmd_add(args) -> None:
    os.makedirs(UH_DIR, exist_ok=True)
    task_id = _next_task_id()
    now = _now_iso()
    session_id = os.environ.get("SESSION_ID", "")
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    record = {
        "task_id": task_id,
        "title": args.title,
        "description": args.desc or "",
        "priority": args.priority,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "created_by_session": session_id,
        "tags": tags,
        "source":       args.source or "manual",
        "source_id":    args.source_id or "",
        "auto_managed": args.source not in (None, "", "manual"),
    }
    with open(TASKS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False))


def cmd_sync(args) -> None:
    """외부 소스에서 수집한 항목을 tasks.jsonl에 upsert하고, 사라진 항목을 자동 done 처리한다."""
    source = args.source
    incoming = json.loads(args.items_json)  # list[dict]
    incoming_ids = {item["source_id"] for item in incoming}

    tasks = _load_tasks()
    by_source_id = {
        t["source_id"]: t
        for t in tasks
        if t.get("source") == source and t.get("source_id")
    }

    now = _now_iso()
    changed = False

    # 1) 사라진 항목 → done (pending인 것만)
    for sid, t in by_source_id.items():
        if sid not in incoming_ids and t.get("status") == "pending":
            t["status"] = "done"
            t["updated_at"] = now
            changed = True

    # 2) 신규 항목 → append; 기존 항목 → 제목/설명 업데이트만 (상태 변경 없음)
    existing_ids = set(by_source_id.keys())
    new_records = []
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    today_prefix = f"task-{today}-"
    seq = sum(1 for t in tasks if t.get("task_id", "").startswith(today_prefix)) + 1
    for item in incoming:
        sid = item["source_id"]
        if sid in existing_ids:
            # 제목·설명·우선순위가 변경된 경우만 업데이트 (status 보존)
            t = by_source_id[sid]
            if (t.get("title") != item.get("title") or
                    t.get("description", "") != item.get("description", "") or
                    t.get("priority") != item.get("priority", "P1")):
                t["title"] = item.get("title", t["title"])
                t["description"] = item.get("description", t.get("description", ""))
                t["priority"] = item.get("priority", "P1")
                t["updated_at"] = now
                changed = True
        else:
            task_id = f"{today_prefix}{seq:03d}"
            seq += 1
            new_records.append({
                "task_id": task_id,
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "priority": item.get("priority", "P1"),
                "status": "pending",
                "created_at": now,
                "updated_at": now,
                "created_by_session": "",
                "tags": item.get("tags", []),
                "source": source,
                "source_id": sid,
                "auto_managed": True,
            })
            changed = True

    auto_done_ids = set(by_source_id.keys()) - incoming_ids
    auto_done_count = sum(
        1 for t in tasks
        if t.get("source") == source and t.get("source_id") in auto_done_ids and t.get("status") == "done"
    )

    if changed or new_records:
        _save_tasks(tasks + new_records)
    print(json.dumps({"upserted": len(new_records), "auto_done": auto_done_count}, ensure_ascii=False))


def cmd_list(args) -> None:
    tasks = _load_tasks()
    status_filter = args.status if args.status else "pending"
    if status_filter == "all":
        result = tasks
    else:
        result = [t for t in tasks if t.get("status") == status_filter]
    if status_filter == "pending":
        result = _pending_sorted(tasks)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_top(_args) -> None:
    tasks = _load_tasks()
    sorted_pending = _pending_sorted(tasks)
    if sorted_pending:
        print(json.dumps(sorted_pending[0], ensure_ascii=False))


def _update_status(task_id: str, new_status: str) -> None:
    tasks = _load_tasks()
    found = False
    for t in tasks:
        if t.get("task_id") == task_id:
            t["status"] = new_status
            t["updated_at"] = _now_iso()
            found = True
            break
    if not found:
        print(f"오류: task_id '{task_id}'를 찾을 수 없습니다.", file=sys.stderr)
        sys.exit(1)
    _save_tasks(tasks)


def cmd_done(args) -> None:
    _update_status(args.id, "done")


def cmd_skip(args) -> None:
    _update_status(args.id, "skipped")


def main() -> None:
    parser = argparse.ArgumentParser(description="ultraharness 태스크 큐 관리")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="태스크 추가")
    p_add.add_argument("--title", required=True, help="태스크 제목")
    p_add.add_argument("--priority", default="P1", choices=["P0", "P1", "P2"], help="우선순위 (기본값: P1)")
    p_add.add_argument("--desc", default="", help="상세 설명 (선택)")
    p_add.add_argument("--tags", default="", help="쉼표 구분 태그 (선택)")
    p_add.add_argument("--source", default="manual", help="소스 유형")
    p_add.add_argument("--source-id", dest="source_id", default="", help="stable source key")

    p_sync = sub.add_parser("sync", help="외부 소스 항목 upsert 및 자동 done 처리")
    p_sync.add_argument("--source", required=True, help="소스 유형")
    p_sync.add_argument("--items-json", dest="items_json", required=True, help="항목 JSON 배열 문자열")

    p_list = sub.add_parser("list", help="태스크 목록 조회")
    p_list.add_argument("--status", default="pending", choices=["pending", "done", "all"], help="필터 (기본값: pending)")

    sub.add_parser("top", help="최우선 pending 태스크 1건 조회")

    p_done = sub.add_parser("done", help="태스크를 완료 처리")
    p_done.add_argument("--id", required=True, help="task_id")

    p_skip = sub.add_parser("skip", help="태스크를 스킵 처리")
    p_skip.add_argument("--id", required=True, help="task_id")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "add": cmd_add,
        "sync": cmd_sync,
        "list": cmd_list,
        "top": cmd_top,
        "done": cmd_done,
        "skip": cmd_skip,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()

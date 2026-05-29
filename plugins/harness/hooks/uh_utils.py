#!/usr/bin/env python3
"""ultraharness 공통 헬퍼 — UH_DIR 부재 감지 및 throttled 경고 출력."""
import os
import sys
import time
from datetime import datetime, timezone

UH_DIR = os.path.expanduser("~/.claude/ultraharness")
_WARN_STAMP = os.path.expanduser("~/.claude/ultraharness.warn_stamp")  # UH_DIR 밖에 위치
_WARN_THROTTLE_SECS = 86400  # 24시간


def warn_if_missing(label: str = "") -> bool:
    """UH_DIR이 없으면 하루 1회 stderr 경고를 출력하고 True를 반환한다.
    UH_DIR이 존재하면 False를 반환한다.
    label: 호출 출처 (예: "inject_uh_on_prompt") — 디버깅용."""
    if os.path.isdir(UH_DIR):
        return False
    # throttle: 마지막 경고로부터 24시간 미경과 시 silent skip
    try:
        if os.path.exists(_WARN_STAMP):
            if time.time() - os.path.getmtime(_WARN_STAMP) < _WARN_THROTTLE_SECS:
                return True
        # stamp 갱신
        with open(_WARN_STAMP, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass
    tag = f" [{label}]" if label else ""
    print(
        f"[ultraharness]{tag} ~/.claude/ultraharness 디렉터리가 없습니다. "
        "ultraharness 기능이 비활성화됩니다. "
        "활성화하려면 디렉터리를 생성하세요: mkdir -p ~/.claude/ultraharness",
        file=sys.stderr
    )
    return True


def log_skip_reason(reason: str) -> None:
    """UH_DIR 내 uh_skip.log에 타임스탬프와 함께 기록한다 (DEVNULL 환경용)."""
    try:
        log_path = os.path.join(UH_DIR, "uh_skip.log")
        with open(log_path, "a", encoding="utf-8") as f:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"{ts} {reason}\n")
    except Exception:
        pass

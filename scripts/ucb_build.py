#!/usr/bin/env python3
"""
scripts/ucb_build.py

Unity Build Automation (Cloud Build) 빌드 트리거 → 폴링 → 아티팩트 다운로드.
Python 3.8+, 외부 패키지 불필요.

사용법:
    python scripts/ucb_build.py
    (또는 환경변수를 직접 지정)
    UCB_ORG_ID=... UCB_PROJECT_ID=... UCB_AUTH_HEADER=... UCB_BUILD_TARGET_ID=... python scripts/ucb_build.py
"""

import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── 설정 ─────────────────────────────────────────────────────────────────────

API_BASE = "https://build-api.cloud.unity3d.com/api/v1"
POLL_INTERVAL_SECONDS = 30
MAX_WAIT_MINUTES = 90
TERMINAL_STATUSES = {"success", "failure", "canceled", "unknown"}

# ── .env 로더 (stdlib 전용) ───────────────────────────────────────────────────

def _load_dotenv(path: Path) -> None:
    """이미 설정된 환경변수를 덮어쓰지 않고 .env 파일을 os.environ에 추가."""
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

# ── HTTP 헬퍼 ─────────────────────────────────────────────────────────────────

def _make_headers(api_key: str) -> dict:
    """Build Automation Settings의 API Key로 Basic auth 헤더 생성."""
    import base64
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def _api_request(method: str, url: str, headers: dict, body: Optional[dict] = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        msg = exc.read().decode(errors="replace")
        print(f"HTTP {exc.code} {exc.reason}\nURL: {url}\n{msg}", file=sys.stderr)
        raise

# ── 핵심 워크플로우 ───────────────────────────────────────────────────────────

def _trigger_build(org: str, project: str, target: str, headers: dict) -> int:
    url = f"{API_BASE}/orgs/{org}/projects/{project}/buildtargets/{target}/builds"
    resp = _api_request("POST", url, headers, body={"clean": False})
    build_num: int = resp[0]["build"]
    print(f"[UCB] Build #{build_num} triggered  (target: {target})")
    return build_num

def _poll_build(org: str, project: str, target: str, build_num: int, headers: dict) -> dict:
    url = f"{API_BASE}/orgs/{org}/projects/{project}/buildtargets/{target}/builds/{build_num}"
    deadline = time.monotonic() + MAX_WAIT_MINUTES * 60
    while True:
        resp = _api_request("GET", url, headers)
        # API 버전에 따라 buildStatus 또는 status 사용
        status: str = resp.get("buildStatus") or resp.get("status") or "unknown"
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[UCB] {ts}  status={status}")
        if status in TERMINAL_STATUSES:
            return resp
        if time.monotonic() > deadline:
            print(f"[UCB] Timeout: {MAX_WAIT_MINUTES}분 내에 완료되지 않았습니다.", file=sys.stderr)
            sys.exit(1)
        time.sleep(POLL_INTERVAL_SECONDS)

def _download_artifact(build_resp: dict, target: str, build_num: int, repo_root: Path) -> Path:
    try:
        url: str = build_resp["links"]["download_primary"]["href"]
    except KeyError:
        print("[UCB] 빌드 응답에 download_primary 링크가 없습니다.", file=sys.stderr)
        sys.exit(1)

    artifact_dir = repo_root / "artifacts"
    artifact_dir.mkdir(exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    dest = artifact_dir / f"{target}-build{build_num}-{ts}.zip"

    print(f"[UCB] 다운로드 중 → {dest}")
    with urllib.request.urlopen(url) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)

    size_mb = dest.stat().st_size / 1_048_576
    print(f"[UCB] 다운로드 완료 ({size_mb:.1f} MB)")
    return dest

# ── 진입점 ────────────────────────────────────────────────────────────────────

def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    _load_dotenv(repo_root / ".env")

    def require(name: str) -> str:
        val = os.environ.get(name, "").strip()
        if not val:
            print(
                f"오류: 환경변수 {name!r}가 설정되지 않았습니다.\n"
                ".env.example을 .env로 복사한 뒤 값을 채워주세요.",
                file=sys.stderr,
            )
            sys.exit(1)
        return val

    org     = require("UCB_ORG_ID")
    project = require("UCB_PROJECT_ID")
    api_key = require("UCB_API_KEY")
    target  = require("UCB_BUILD_TARGET_ID")

    headers = _make_headers(api_key)

    build_num  = _trigger_build(org, project, target, headers)
    build_resp = _poll_build(org, project, target, build_num, headers)

    status: str = build_resp.get("buildStatus") or build_resp.get("status") or "unknown"

    if status == "success":
        dest = _download_artifact(build_resp, target, build_num, repo_root)
        print(f"[UCB] 완료. 아티팩트: {dest}")
        sys.exit(0)
    else:
        print(
            f"[UCB] 빌드 종료 status={status!r}\n"
            f"로그 확인: https://cloud.unity.com/build-automation/orgs/{org}/projects/{project}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

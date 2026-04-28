#!/usr/bin/env python3
"""빌드 타겟 목록과 ID 출력. UCB_BUILD_TARGET_ID 확인용."""

import base64, json, os, sys, urllib.request
from pathlib import Path

def load_dotenv(path):
    if not path.exists(): return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, _, v = line.partition("=")
        if k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_dotenv(Path(__file__).parent.parent / ".env")

org     = os.environ.get("UCB_ORG_ID", "")
project = os.environ.get("UCB_PROJECT_ID", "")
api_key = os.environ.get("UCB_API_KEY", "")

if not all([org, project, api_key]):
    print("UCB_ORG_ID / UCB_PROJECT_ID / UCB_API_KEY 를 .env에 설정하세요.")
    sys.exit(1)

url = f"https://build-api.cloud.unity3d.com/api/v1/orgs/{org}/projects/{project}/buildtargets"
token = base64.b64encode(f"{api_key}:".encode()).decode()
auth_value = f"Basic {token}"
print(f"[DEBUG] URL: {url}")
req = urllib.request.Request(url, headers={"Authorization": auth_value, "Accept": "application/json"})

try:
    with urllib.request.urlopen(req) as resp:
        targets = json.loads(resp.read())
except urllib.error.HTTPError as e:
    body = e.read().decode(errors="replace")
    print(f"HTTP {e.code}: {e.reason}")
    print(f"Response body: {body}")
    sys.exit(1)

print(f"{'ID (UCB_BUILD_TARGET_ID)':<40}  {'Name'}")
print("-" * 70)
for t in targets:
    print(f"{t['buildtargetid']:<40}  {t['name']}")

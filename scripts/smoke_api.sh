#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${RAST_API_BASE_URL:-http://127.0.0.1:8000}"

echo "Smoke testing RAST API at ${BASE_URL}"
curl -fsS "${BASE_URL}/health" >/dev/null
curl -fsS "${BASE_URL}/api/scenarios" >/dev/null
curl -fsS "${BASE_URL}/api/policies" >/dev/null

python - "${BASE_URL}" <<'PY'
import json
import sys
import urllib.request

base_url = sys.argv[1].rstrip("/")
payload = json.dumps({
    "scenario": "clear_path",
    "apply_policy": "rast",
    "max_steps": 3,
    "update_mode": "full_recompute",
}).encode("utf-8")
request = urllib.request.Request(
    f"{base_url}/api/run-scenario",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=15) as response:
    result = json.loads(response.read().decode("utf-8"))
if not result.get("selected_action"):
    raise SystemExit("Scenario result has no selected_action.")
if "token_counts" not in result:
    raise SystemExit("Scenario result has no token_counts.")
print("RAST API smoke test passed.")
PY

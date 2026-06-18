"""캡스톤 최종 제출 직전 필수 산출물과 API 동작을 점검합니다."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "LICENSE",
    "Dockerfile",
    ".github/workflows/ci.yml",
    ".github/dependabot.yml",
    "RUNBOOK.md",
    "CHANGELOG.md",
    "MODEL_CARD.md",
    "RETROSPECTIVE.md",
    "docs/submission_checklist.md",
    "docs/deployment_guide.md",
    "docs/release_guide.md",
    "docs/demo_script_3min.md",
)

MANUAL_PLACEHOLDERS = (
    "GitHub public URL",
    "deployment URL",
    "release URL",
    "demo video URL",
)


def run_checks() -> list[str]:
    """실패한 readiness check 메시지를 반환합니다."""

    failures: list[str] = []
    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).exists():
            failures.append(f"Missing required file: {relative_path}")

    readme = _read_text("README.md")
    for needle in ("docker build -t rast-mvp0 .", "/health", "/metrics"):
        if needle not in readme:
            failures.append(f"README.md does not contain required text: {needle}")

    checklist = _read_text("docs/submission_checklist.md")
    for placeholder in MANUAL_PLACEHOLDERS:
        if placeholder not in checklist:
            failures.append(f"submission_checklist.md missing Manual placeholder: {placeholder}")

    failures.extend(_check_fastapi_app())
    return failures


def _check_fastapi_app() -> list[str]:
    failures: list[str] = []
    try:
        from fastapi.testclient import TestClient

        from apps.api.main import app

        client = TestClient(app)
        health = client.get("/health")
        if health.status_code != 200 or health.json().get("status") != "ok":
            failures.append("/health did not return ok.")

        result = client.post(
            "/api/run-scenario",
            json={
                "scenario": "clear_path",
                "apply_policy": "rast",
                "max_steps": 3,
                "update_mode": "full_recompute",
            },
        )
        if result.status_code != 200:
            failures.append("/api/run-scenario did not return 200.")
        else:
            payload = result.json()
            if not payload.get("selected_action"):
                failures.append("/api/run-scenario response missing selected_action.")
            if not payload.get("reason_code"):
                failures.append("/api/run-scenario response missing reason_code.")
    except Exception as exc:  # pragma: no cover - CLI guardrail로 상세 메시지를 남깁니다.
        failures.append(f"FastAPI readiness check failed: {exc}")
    return failures


def _read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def main() -> int:
    failures = run_checks()
    if failures:
        print("submission_readiness: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("submission_readiness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""캡스톤 OSS 제출 hardening 산출물 존재 여부를 확인합니다."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_submission_files_exist() -> None:
    required_paths = [
        "Dockerfile",
        ".dockerignore",
        "scripts/run_api.ps1",
        "scripts/run_api.sh",
        "scripts/smoke_api.ps1",
        "scripts/smoke_api.sh",
        ".github/workflows/ci.yml",
        ".github/dependabot.yml",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "LICENSE",
        "RUNBOOK.md",
        "RETROSPECTIVE.md",
        "CHANGELOG.md",
        "docs/submission_checklist.md",
    ]

    for relative_path in required_paths:
        assert (ROOT / relative_path).exists(), relative_path


def test_model_or_data_card_exists() -> None:
    assert (ROOT / "MODEL_CARD.md").exists() or (ROOT / "DATA_CARD.md").exists()


def test_readme_mentions_docker_and_healthcheck() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "docker build -t rast-mvp0 ." in readme
    assert "docker run --rm -p 8000:8000 rast-mvp0" in readme
    assert "/health" in readme
    assert "Capstone OSS Submission" in readme


def test_pyproject_uses_httpx_for_fastapi_test_client() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"fastapi' in pyproject
    assert '"uvicorn' in pyproject
    assert '"httpx>=' in pyproject
    assert "httpx2" not in pyproject

"""최종 제출 readiness checker와 문서 산출물을 검증합니다."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from experiments.check_submission_readiness import run_checks


ROOT = Path(__file__).resolve().parents[1]


def test_submission_readiness_checks_pass() -> None:
    assert run_checks() == []


def test_submission_readiness_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "experiments/check_submission_readiness.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "submission_readiness: PASS" in result.stdout


def test_final_submission_docs_exist() -> None:
    for relative_path in (
        "docs/deployment_guide.md",
        "docs/release_guide.md",
        "docs/demo_script_3min.md",
        "render.yaml",
    ):
        assert (ROOT / relative_path).exists(), relative_path


def test_release_guide_does_not_auto_create_tag() -> None:
    release_guide = (ROOT / "docs/release_guide.md").read_text(encoding="utf-8")

    assert "자동으로 수행하지 않습니다" in release_guide
    assert "git tag v1.0.0" in release_guide

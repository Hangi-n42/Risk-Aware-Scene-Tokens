import subprocess
import sys
from pathlib import Path

from rast.evaluation.docs_consistency import check_document_texts, load_document_texts


def test_readme_and_project_summary_exist() -> None:
    assert Path("README.md").exists()
    assert Path("docs/project_summary.md").exists()


def test_readme_contains_key_document_links() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "docs/artifact_manifest.md" in readme
    assert "docs/reproducibility_guide.md" in readme
    assert "docs/technical_report.md" in readme
    assert "docs/result_report.md" in readme


def test_project_summary_keeps_scope_warning() -> None:
    summary = Path("docs/project_summary.md").read_text(encoding="utf-8")

    assert "real-world performance claim" in summary
    assert "not an exhaustive extended grid result" in summary
    assert "not visual replay" in summary


def test_docs_consistency_script_passes_current_docs() -> None:
    result = subprocess.run(
        [sys.executable, "experiments/check_docs_consistency.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "docs_consistency: PASS" in result.stdout


def test_docs_consistency_detects_forbidden_stale_phrase() -> None:
    texts = load_document_texts(".")
    texts["README.md"] = texts["README.md"] + "\nEvidenceToken 미구현\n"

    result = check_document_texts(texts)

    assert not result.passed
    assert any("EvidenceToken 미구현" in failure for failure in result.failures)

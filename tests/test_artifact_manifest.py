import json
from pathlib import Path


def test_artifact_manifest_files_exist() -> None:
    assert Path("docs/artifact_manifest.md").exists()
    assert Path("docs/artifact_manifest.json").exists()
    assert Path("docs/reproducibility_guide.md").exists()


def test_artifact_manifest_json_schema() -> None:
    manifest = json.loads(Path("docs/artifact_manifest.json").read_text(encoding="utf-8"))

    assert "canonical_reports" in manifest
    assert "canonical_runs" in manifest
    assert "configs" in manifest

    report_paths = {entry["path"] for entry in manifest["canonical_reports"]}
    assert "docs/result_report.md" in report_paths
    assert "docs/technical_report.md" in report_paths
    assert "docs/eval_comparison_report.md" in report_paths


def test_reproducibility_guide_contains_verification_and_large_grid_warning() -> None:
    guide = Path("docs/reproducibility_guide.md").read_text(encoding="utf-8")

    assert "python -m pytest" in guide
    assert "전체 조합을 실행하지 말고" in guide
    assert "8,294,400 planned runs" in guide

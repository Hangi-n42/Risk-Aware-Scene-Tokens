"""문서 링크와 해석 경계를 가볍게 점검하는 유틸리티입니다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DOC_PATHS: tuple[str, ...] = (
    "README.md",
    "docs/artifact_manifest.md",
    "docs/reproducibility_guide.md",
    "docs/technical_report.md",
    "docs/result_report.md",
    "docs/eval_comparison_report.md",
)

README_REQUIRED_LINKS: tuple[str, ...] = (
    "docs/artifact_manifest.md",
    "docs/reproducibility_guide.md",
    "docs/technical_report.md",
    "docs/result_report.md",
)

MANIFEST_REQUIRED_REPORTS: tuple[str, ...] = (
    "docs/eval_comparison_report.md",
    "docs/sampling_coverage_report.md",
    "docs/seed_stability_report.md",
    "docs/sample_size_convergence_report.md",
)

WARNING_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("WindowsMetadataSim", ("WindowsMetadataSim",)),
    (
        "not real robot",
        (
            "not real robot",
            "real robot 결과가 아닙니다",
            "real robot safety claim",
            "real robot performance",
            "실제 로봇",
            "real robot action feasibility를 검증하지 않습니다",
        ),
    ),
    (
        "not real-world performance",
        (
            "not real-world performance",
            "real-world performance claim",
            "real-world performance claims",
            "real-world 성능",
            "성능 우수성",
        ),
    ),
    (
        "not exhaustive sampled result",
        (
            "sampled extended result는 exhaustive",
            "exhaustive extended grid result가 아닙니다",
            "full extended grid exhaustive result가 아닙니다",
            "full extended grid exhaustive result가 아니며",
            "not the full extended grid",
        ),
    ),
    (
        "not visual replay",
        (
            "visual replay가 아닙니다",
            "visual replay 아님",
            "not visual replay",
            "metadata/action/evidence trace",
            "metadata/action trace",
        ),
    ),
)

FORBIDDEN_STALE_PHRASES: tuple[str, ...] = (
    "EvidenceToken 미구현",
    "AffordanceToken 미구현",
    "UncertaintyToken 미구현",
    "sampled extended result is the full extended grid result",
    "sampled extended result is full extended grid result",
    "sampled extended result는 full extended grid result입니다",
    "sampled result는 full extended grid exhaustive result입니다",
    "real robot performance를 지원",
    "supports real robot performance",
    "visual replay를 제공",
    "provides visual replay",
)


@dataclass(frozen=True)
class DocsConsistencyResult:
    passed: bool
    failures: list[str]


def load_document_texts(root: Path | str = ".") -> dict[str, str]:
    """검사 대상 문서를 UTF-8로 읽습니다."""

    root_path = Path(root)
    texts: dict[str, str] = {}
    for relative_path in DOC_PATHS:
        path = root_path / relative_path
        if path.exists():
            texts[relative_path] = path.read_text(encoding="utf-8")
        else:
            texts[relative_path] = ""
    return texts


def check_document_texts(texts: Mapping[str, str]) -> DocsConsistencyResult:
    """문서 링크, 필수 warning, 오래된 금지 문구를 점검합니다."""

    failures: list[str] = []
    for path in DOC_PATHS:
        if not texts.get(path, ""):
            failures.append(f"missing or empty document: {path}")

    readme = texts.get("README.md", "")
    for link in README_REQUIRED_LINKS:
        if link not in readme:
            failures.append(f"README missing required link: {link}")

    manifest = texts.get("docs/artifact_manifest.md", "")
    for report_path in MANIFEST_REQUIRED_REPORTS:
        if report_path not in manifest:
            failures.append(f"artifact manifest missing report reference: {report_path}")

    for doc_path in ("README.md", "docs/technical_report.md", "docs/result_report.md"):
        text = texts.get(doc_path, "")
        for warning_name, alternatives in WARNING_GROUPS:
            if not any(candidate in text for candidate in alternatives):
                failures.append(f"{doc_path} missing warning: {warning_name}")

    for doc_path, text in texts.items():
        for phrase in FORBIDDEN_STALE_PHRASES:
            if phrase in text:
                failures.append(f"{doc_path} contains forbidden stale phrase: {phrase}")

    return DocsConsistencyResult(passed=not failures, failures=failures)


def check_docs_consistency(root: Path | str = ".") -> DocsConsistencyResult:
    """현재 작업 디렉토리 기준 문서 정합성을 검사합니다."""

    return check_document_texts(load_document_texts(root))

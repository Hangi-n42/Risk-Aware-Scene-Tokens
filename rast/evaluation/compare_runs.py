"""두 evaluation run의 aggregate 결과를 비교하는 Markdown report 유틸리티입니다."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rast.evaluation.report import compute_report_stats, read_table


METRIC_SPECS: tuple[tuple[str, str], ...] = (
    ("success_rate", "success rate"),
    ("near_miss_count_avg", "avg near-miss"),
    ("latency_avg_ms", "avg latency ms"),
    ("token_generation_latency_avg_ms", "avg token generation latency ms"),
    ("planning_latency_avg_ms", "avg planning latency ms"),
    ("rast_vs_object_list_disagreement_avg", "RAST vs Object List disagreement"),
    ("rast_vs_flat_feature_disagreement_avg", "RAST vs Flat Feature disagreement"),
    ("rast_vs_scene_graph_disagreement_avg", "RAST vs Scene Graph disagreement"),
    ("rast_vs_event_aware_disagreement_avg", "RAST vs Event-aware disagreement"),
    ("rast_vs_uncertainty_aware_disagreement_avg", "RAST vs Uncertainty-aware disagreement"),
    ("rast_vs_affordance_aware_disagreement_avg", "RAST vs Affordance-aware disagreement"),
    ("event_triggered_action_count_avg", "event-triggered actions"),
    ("uncertainty_triggered_action_count_avg", "uncertainty-triggered actions"),
    ("affordance_triggered_action_count_avg", "affordance-triggered actions"),
    ("evidence_token_count_avg", "EvidenceToken avg"),
)


def generate_eval_comparison_report(
    *,
    baseline_results: str | Path,
    candidate_results: str | Path,
    baseline_summary: str | Path | None = None,
    candidate_summary: str | Path | None = None,
    baseline_metadata: str | Path | None = None,
    candidate_metadata: str | Path | None = None,
    candidate_coverage: str | Path | None = None,
    candidate_seed_stability: str | Path | None = None,
    candidate_sample_size_convergence: str | Path | None = None,
) -> str:
    """baseline과 candidate aggregate를 비교하는 Markdown 문자열을 생성합니다."""

    baseline_rows = read_table(baseline_results)
    candidate_rows = read_table(candidate_results)
    baseline_stats = compute_report_stats(baseline_rows)
    candidate_stats = compute_report_stats(candidate_rows)
    baseline_meta = _read_metadata(baseline_metadata)
    candidate_meta = _read_metadata(candidate_metadata)
    baseline_id = _run_id(baseline_rows, baseline_meta)
    candidate_id = _run_id(candidate_rows, candidate_meta)

    lines: list[str] = [
        "# RAST Evaluation Comparison Report",
        "",
        "이 문서는 baseline evaluation run과 sampled extended evaluation run을 비교합니다.",
        "비교 목적은 성능 우수성 판단이 아니라 sensitivity exploration과 coverage 확인입니다.",
        "",
        "## Evaluation Comparison Summary",
        "",
        f"- baseline run id: `{baseline_id}`",
        f"- candidate run id: `{candidate_id}`",
        f"- baseline total runs: {baseline_stats['total_runs']}",
        f"- candidate total runs: {candidate_stats['total_runs']}",
        f"- baseline failed runs: {baseline_stats['failed_runs']}",
        f"- candidate failed runs: {candidate_stats['failed_runs']}",
        f"- candidate sampling mode: `{candidate_meta.get('sampling_mode', 'not provided')}`",
        f"- candidate sample size: `{candidate_meta.get('sample_size', 'not provided')}`",
        f"- candidate sample seed: `{candidate_meta.get('sample_seed', 'not provided')}`",
        "- candidate가 full extended grid가 아니라 sampled extended result라는 전제로 해석합니다.",
        "",
        "## Metric Comparison",
        "",
        "| Metric | Baseline | Candidate | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key, label in METRIC_SPECS:
        baseline_value = float(baseline_stats["overall"].get(key, 0.0) or 0.0)
        candidate_value = float(candidate_stats["overall"].get(key, 0.0) or 0.0)
        lines.append(
            f"| {label} | {_fmt(baseline_value)} | {_fmt(candidate_value)} | {_fmt(candidate_value - baseline_value)} |"
        )

    lines.extend(_replay_comparison_lines(baseline_meta, candidate_meta))
    lines.extend(_scenario_coverage_lines(baseline_stats, candidate_stats))
    lines.extend(
        [
            "## Interpretation",
            "",
            "- sampled extended result는 exhaustive grid result가 아닙니다.",
            "- sampling 결과는 sample seed와 sample size에 의존합니다.",
            "- observed metric difference는 성능 개선/악화 증거가 아니라 sensitivity exploration입니다.",
            "- 모든 결과는 WindowsMetadataSim metadata simulator 기반입니다.",
            "- 실제 perception-bound extractor, real robot, 또는 real simulator 성능을 대변하지 않습니다.",
            f"- candidate coverage artifact: `{candidate_coverage or 'not provided'}`",
            f"- candidate seed stability artifact: `{candidate_seed_stability or 'not provided'}`",
            f"- candidate sample-size convergence artifact: `{candidate_sample_size_convergence or 'not provided'}`",
            "",
            "## Inputs",
            "",
            f"- baseline_results: `{baseline_results}`",
            f"- baseline_summary: `{baseline_summary or 'not provided'}`",
            f"- candidate_results: `{candidate_results}`",
            f"- candidate_summary: `{candidate_summary or 'not provided'}`",
            f"- baseline_metadata: `{baseline_metadata or 'not provided'}`",
            f"- candidate_metadata: `{candidate_metadata or 'not provided'}`",
            f"- candidate_coverage: `{candidate_coverage or 'not provided'}`",
            f"- candidate_seed_stability: `{candidate_seed_stability or 'not provided'}`",
            f"- candidate_sample_size_convergence: `{candidate_sample_size_convergence or 'not provided'}`",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_eval_comparison_report(*, output: str | Path, **kwargs: Any) -> str:
    markdown = generate_eval_comparison_report(**kwargs)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return markdown


def _replay_comparison_lines(baseline_meta: dict[str, Any], candidate_meta: dict[str, Any]) -> list[str]:
    return [
        "",
        "| Replay Metric | Baseline | Candidate |",
        "|---|---:|---:|",
        f"| replay count | {_replay_count(baseline_meta)} | {_replay_count(candidate_meta)} |",
        "",
    ]


def _scenario_coverage_lines(baseline_stats: dict[str, Any], candidate_stats: dict[str, Any]) -> list[str]:
    baseline_scenarios = set(baseline_stats["scenarios"])
    candidate_scenarios = set(candidate_stats["scenarios"])
    missing = sorted(baseline_scenarios - candidate_scenarios)
    return [
        "## Scenario Coverage Comparison",
        "",
        f"- baseline scenario count: {len(baseline_scenarios)}",
        f"- candidate scenario count: {len(candidate_scenarios)}",
        f"- candidate scenarios: `{', '.join(sorted(candidate_scenarios))}`",
        f"- missing baseline scenarios in candidate: `{', '.join(missing) if missing else 'none'}`",
        "",
    ]


def _read_metadata(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    metadata_path = Path(path)
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _run_id(rows: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    if metadata.get("suite_run_id"):
        return str(metadata["suite_run_id"])
    if rows:
        return str(rows[0].get("suite_run_id", ""))
    return ""


def _replay_count(metadata: dict[str, Any]) -> int:
    replay_path = metadata.get("replay_index_path")
    if not replay_path:
        return 0
    path = Path(str(replay_path))
    if not path.exists():
        return 0
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    return int(index.get("replay_count", 0) or 0)


def _fmt(value: float) -> str:
    return f"{value:.3f}"

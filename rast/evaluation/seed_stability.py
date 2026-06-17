"""Seed-to-seed stability report utilities for sampled evaluation runs."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

from rast.evaluation.report import compute_report_stats, read_table


STABILITY_METRICS: tuple[tuple[str, str], ...] = (
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
    ("affordance_token_count_avg", "AffordanceToken avg"),
    ("replay_count", "replay count"),
)


def load_seed_sweep_index(path: str | Path) -> dict[str, Any]:
    index_path = Path(path)
    return json.loads(index_path.read_text(encoding="utf-8"))


def generate_seed_stability_report(*, seed_sweep_index_path: str | Path) -> str:
    """seed sweep index를 읽어 stability Markdown을 생성합니다."""

    index = load_seed_sweep_index(seed_sweep_index_path)
    rows = compute_seed_stability(index)
    metric_stats = metric_stability(rows)
    scenario_coverage = scenario_coverage_stability(rows)
    high_variance = sorted(
        metric_stats,
        key=lambda item: (item["coefficient_of_variation"], item["range"]),
        reverse=True,
    )[:5]

    lines = [
        "# RAST Seed Stability Report",
        "",
        "이 문서는 sampled extended evaluation의 sample seed 변화에 따른 metric 변동을 점검합니다.",
        "metric variation은 성능 변화가 아니라 sample composition 차이일 수 있습니다.",
        "",
        "## Seed Stability Summary",
        "",
        f"- seed_sweep_index: `{seed_sweep_index_path}`",
        f"- config_path: `{index.get('config_path', '')}`",
        f"- sample_size: `{index.get('sample_size', '')}`",
        f"- sampling_mode: `{index.get('sampling_mode', '')}`",
        f"- seeds: `{', '.join(str(seed) for seed in index.get('seeds', []))}`",
        "",
        "| Seed | Run Directory | Run Count | Failed Runs | Replay Count |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['seed']} | `{row['run_dir']}` | {row['run_count']} | "
            f"{row['failed_runs']} | {row['metrics'].get('replay_count', 0):.0f} |"
        )

    lines.extend(
        [
            "",
            "## Metric Stability Table",
            "",
            "| Metric | Mean | Min | Max | Range | Std | Coefficient of Variation |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in metric_stats:
        lines.append(
            f"| {item['label']} | {_fmt(item['mean'])} | {_fmt(item['min'])} | {_fmt(item['max'])} | "
            f"{_fmt(item['range'])} | {_fmt(item['std'])} | {_fmt(item['coefficient_of_variation'])} |"
        )

    lines.extend(
        [
            "",
            "## High-Variance Metrics",
            "",
            "| Metric | Range | Coefficient of Variation | Interpretation |",
            "|---|---:|---:|---|",
        ]
    )
    for item in high_variance:
        lines.append(
            f"| {item['label']} | {_fmt(item['range'])} | {_fmt(item['coefficient_of_variation'])} | "
            "sample seed에 따른 subset 구성이 metric에 영향을 준 후보입니다. |"
        )

    lines.extend(
        [
            "",
            "## Scenario Coverage Stability",
            "",
            f"- all-seed scenario intersection: `{', '.join(scenario_coverage['all_seed_scenarios']) or 'none'}`",
            f"- partial scenarios: `{', '.join(scenario_coverage['partial_scenarios']) or 'none'}`",
            "",
            "| Seed | Scenario Count | Scenarios |",
            "|---:|---:|---|",
        ]
    )
    for row in rows:
        scenarios = row["scenarios"]
        lines.append(f"| {row['seed']} | {len(scenarios)} | `{', '.join(scenarios)}` |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- seed-to-seed stability는 sampled extended evaluation의 신뢰도를 보기 위한 보조 분석입니다.",
            "- metric variation은 성능 개선/악화가 아니라 sample composition 차이일 수 있습니다.",
            "- 이 결과는 full extended grid exhaustive result가 아닙니다.",
            "- 모든 결과는 WindowsMetadataSim metadata simulator 기반이며 real-world performance claim을 지원하지 않습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_seed_stability_report(*, seed_sweep_index_path: str | Path, output_path: str | Path) -> str:
    markdown = generate_seed_stability_report(seed_sweep_index_path=seed_sweep_index_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    return markdown


def compute_seed_stability(index: dict[str, Any]) -> list[dict[str, Any]]:
    """seed별 aggregate metric과 scenario coverage를 계산합니다."""

    rows: list[dict[str, Any]] = []
    for run in index.get("runs", []):
        results_path = Path(str(run.get("aggregate_results", "")))
        aggregate_rows = read_table(results_path)
        stats = compute_report_stats(aggregate_rows)
        metrics = dict(stats["overall"])
        metrics["replay_count"] = float(_replay_count(run.get("replay_index")))
        rows.append(
            {
                "seed": int(run.get("seed", 0)),
                "run_dir": str(run.get("run_dir", "")),
                "run_count": int(stats["total_runs"]),
                "failed_runs": int(run.get("failed_runs", stats["failed_runs"])),
                "scenarios": stats["scenarios"],
                "metrics": metrics,
            }
        )
    return rows


def metric_stability(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """주요 metric의 seed별 mean/min/max/range/std/CV를 계산합니다."""

    summaries: list[dict[str, Any]] = []
    for key, label in STABILITY_METRICS:
        values = [float(row["metrics"].get(key, 0.0) or 0.0) for row in rows]
        if not values:
            values = [0.0]
        mean = statistics.fmean(values)
        minimum = min(values)
        maximum = max(values)
        value_range = maximum - minimum
        std = statistics.pstdev(values) if len(values) > 1 else 0.0
        coefficient = std / abs(mean) if not math.isclose(mean, 0.0) else 0.0
        summaries.append(
            {
                "key": key,
                "label": label,
                "mean": mean,
                "min": minimum,
                "max": maximum,
                "range": value_range,
                "std": std,
                "coefficient_of_variation": coefficient,
            }
        )
    return summaries


def scenario_coverage_stability(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    scenario_sets = [set(row["scenarios"]) for row in rows]
    if not scenario_sets:
        return {"all_seed_scenarios": [], "partial_scenarios": []}
    intersection = set.intersection(*scenario_sets)
    union = set.union(*scenario_sets)
    return {
        "all_seed_scenarios": sorted(intersection),
        "partial_scenarios": sorted(union - intersection),
    }


def _replay_count(path: Any) -> int:
    if not path:
        return 0
    replay_path = Path(str(path))
    if not replay_path.exists():
        return 0
    payload = json.loads(replay_path.read_text(encoding="utf-8"))
    return int(payload.get("replay_count", 0) or 0)


def _fmt(value: float) -> str:
    return f"{value:.3f}"

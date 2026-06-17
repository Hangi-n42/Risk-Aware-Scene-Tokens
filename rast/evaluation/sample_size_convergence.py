"""Sample-size convergence and sampling quality utilities."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

from rast.evaluation.report import compute_report_stats, read_table
from rast.evaluation.sampling_coverage import analyze_sampling_coverage


CONVERGENCE_METRICS: tuple[tuple[str, str], ...] = (
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
    ("decision_trace_coverage", "decision trace coverage"),
    ("replay_count", "replay count"),
)


def load_sample_size_sweep_index(path: str | Path) -> dict[str, Any]:
    """sample_size_sweep_index.json을 읽습니다."""

    index_path = Path(path)
    return json.loads(index_path.read_text(encoding="utf-8"))


def compute_sample_size_convergence(index: dict[str, Any]) -> dict[str, Any]:
    """sample-size별 metric 안정성과 sampling quality score를 계산합니다."""

    run_rows = [_run_summary(run) for run in index.get("runs", [])]
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in run_rows:
        grouped.setdefault(int(row.get("sample_size", 0)), []).append(row)

    sample_size_summaries: dict[str, Any] = {}
    for sample_size, rows in sorted(grouped.items()):
        metric_stats = _metric_stats(rows)
        coverage_by_axis = _coverage_by_axis(rows)
        quality_scores = _sampling_quality_scores(rows, metric_stats)
        sample_size_summaries[str(sample_size)] = {
            "sample_size": sample_size,
            "seed_count": len({row.get("seed") for row in rows}),
            "run_count": sum(int(row.get("run_count", 0) or 0) for row in rows),
            "failed_runs": sum(int(row.get("failed_runs", 0) or 0) for row in rows),
            "metric_stats": metric_stats,
            "coverage_by_axis": coverage_by_axis,
            "quality_scores": quality_scores,
            "high_variance_metrics": _high_variance_metrics(metric_stats),
        }

    return {
        "sample_size_sweep_id": index.get("sample_size_sweep_id", ""),
        "config_path": index.get("config_path", ""),
        "sampling_mode": index.get("sampling_mode", ""),
        "sample_sizes": index.get("sample_sizes", []),
        "seeds": index.get("seeds", []),
        "total_sampled_runs": sum(int(row.get("run_count", 0) or 0) for row in run_rows),
        "failed_runs": sum(int(row.get("failed_runs", 0) or 0) for row in run_rows),
        "run_summaries": run_rows,
        "sample_size_summaries": sample_size_summaries,
        "interpretation_note": (
            "Sampling quality score is a heuristic coverage/balance/stability score, "
            "not a RAST performance score."
        ),
    }


def generate_sample_size_convergence_markdown(summary: dict[str, Any]) -> str:
    """계산된 convergence summary를 Markdown 보고서로 변환합니다."""

    lines = [
        "# RAST Sample-size Convergence Report",
        "",
        "이 문서는 sampled extended evaluation에서 sample-size 변화에 따른 metric 안정성과 coverage 품질을 점검합니다.",
        "전체 extended grid exhaustive result가 아니며, sampling reliability check로만 해석해야 합니다.",
        "",
        "## Sample-size Sweep Summary",
        "",
        f"- sweep id: `{summary.get('sample_size_sweep_id', '')}`",
        f"- config path: `{summary.get('config_path', '')}`",
        f"- sampling mode: `{summary.get('sampling_mode', '')}`",
        f"- sample sizes: `{', '.join(str(item) for item in summary.get('sample_sizes', []))}`",
        f"- seeds: `{', '.join(str(item) for item in summary.get('seeds', []))}`",
        f"- total sampled runs: {summary.get('total_sampled_runs', 0)}",
        f"- failed runs: {summary.get('failed_runs', 0)}",
        "",
        "## Metric Convergence Table",
        "",
        "| Sample Size | Metric | Seed Count | Mean | Std | Min | Max | Range | CV | Relative Range |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for sample_size, item in summary["sample_size_summaries"].items():
        for key, label in CONVERGENCE_METRICS:
            stats = item["metric_stats"].get(key, {})
            lines.append(
                f"| {sample_size} | {label} | {item['seed_count']} | {_fmt(stats.get('mean'))} | "
                f"{_fmt(stats.get('std'))} | {_fmt(stats.get('min'))} | {_fmt(stats.get('max'))} | "
                f"{_fmt(stats.get('range'))} | {_fmt(stats.get('coefficient_of_variation'))} | "
                f"{_fmt(stats.get('relative_range'))} |"
            )

    lines.extend(
        [
            "",
            "## Sampling Quality Score",
            "",
            "| Sample Size | Coverage Score | Balance Score | Stability Score | Overall Sampling Quality Score |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for sample_size, item in summary["sample_size_summaries"].items():
        scores = item["quality_scores"]
        lines.append(
            f"| {sample_size} | {_fmt(scores.get('coverage_score'))} | {_fmt(scores.get('balance_score'))} | "
            f"{_fmt(scores.get('stability_score'))} | {_fmt(scores.get('overall_sampling_quality_score'))} |"
        )

    lines.extend(
        [
            "",
            "## Coverage by Sample Size",
            "",
            "| Sample Size | Axis | Avg Coverage Rate | Avg Balance |",
            "|---:|---|---:|---:|",
        ]
    )
    for sample_size, item in summary["sample_size_summaries"].items():
        for axis, axis_stats in sorted(item["coverage_by_axis"].items()):
            lines.append(
                f"| {sample_size} | `{axis}` | {_fmt(axis_stats.get('coverage_rate_avg'))} | "
                f"{_fmt(axis_stats.get('balance_avg'))} |"
            )

    lines.extend(
        [
            "",
            "## High-Variance Metrics by Sample Size",
            "",
            "| Sample Size | Metric | Range | CV | Interpretation |",
            "|---:|---|---:|---:|---|",
        ]
    )
    for sample_size, item in summary["sample_size_summaries"].items():
        for metric in item["high_variance_metrics"]:
            lines.append(
                f"| {sample_size} | {metric['label']} | {_fmt(metric['range'])} | "
                f"{_fmt(metric['coefficient_of_variation'])} | "
                "sample composition에 민감한 후보 metric입니다. 성능 개선/악화로 해석하지 않습니다. |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- sample-size convergence는 sampled extended evaluation의 대표성/안정성을 보기 위한 보조 분석입니다.",
            "- full extended grid exhaustive result가 아닙니다.",
            "- sampling quality score는 coverage, balance, seed stability를 요약하는 heuristic score입니다.",
            "- score가 높다고 RAST 또는 특정 planner의 task performance가 좋다는 뜻은 아닙니다.",
            "- metric stability가 높아도 real-world 성능 주장을 지원하지 않습니다.",
            "- 모든 결과는 WindowsMetadataSim metadata simulator 기반입니다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_sample_size_convergence_report(
    *,
    sample_size_sweep_index_path: str | Path,
    output_path: str | Path,
    json_output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Markdown 보고서와 선택적 JSON summary를 저장합니다."""

    index = load_sample_size_sweep_index(sample_size_sweep_index_path)
    summary = compute_sample_size_convergence(index)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate_sample_size_convergence_markdown(summary), encoding="utf-8")
    if json_output_path is not None:
        json_output = Path(json_output_path)
    else:
        json_output = output.with_suffix(".json")
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def _run_summary(run: dict[str, Any]) -> dict[str, Any]:
    results_path = Path(str(run.get("aggregate_results") or ""))
    metadata_path = Path(str(run.get("suite_metadata") or ""))
    metrics: dict[str, float] = {key: 0.0 for key, _ in CONVERGENCE_METRICS}
    run_count = 0
    failed_runs = int(run.get("failed_runs", 0) or 0)
    coverage: dict[str, Any] = {"axes": {}}
    if results_path.exists():
        rows = read_table(results_path)
        stats = compute_report_stats(rows)
        run_count = int(stats.get("total_runs", 0) or 0)
        failed_runs = int(run.get("failed_runs", stats.get("failed_runs", 0)) or 0)
        overall = stats.get("overall", {})
        for key, _ in CONVERGENCE_METRICS:
            metrics[key] = float(overall.get(key, 0.0) or 0.0)
        coverage = analyze_sampling_coverage(
            results_path=results_path,
            metadata_path=metadata_path if metadata_path.exists() else None,
        )
    metrics["replay_count"] = float(_replay_count(run.get("replay_index")))
    return {
        "sample_size": int(run.get("sample_size", 0) or 0),
        "seed": int(run.get("seed", 0) or 0),
        "run_dir": str(run.get("run_dir", "")),
        "run_count": run_count,
        "failed_runs": failed_runs,
        "metrics": metrics,
        "coverage": coverage,
    }


def _metric_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for key, label in CONVERGENCE_METRICS:
        values = [float(row["metrics"].get(key, 0.0) or 0.0) for row in rows]
        summary[key] = _number_stats(values) | {"label": label}
    return summary


def _number_stats(values: list[float]) -> dict[str, float]:
    if not values:
        values = [0.0]
    mean = statistics.fmean(values)
    minimum = min(values)
    maximum = max(values)
    value_range = maximum - minimum
    std = statistics.pstdev(values) if len(values) > 1 else 0.0
    coefficient = std / abs(mean) if not math.isclose(mean, 0.0) else 0.0
    relative_range = value_range / abs(mean) if not math.isclose(mean, 0.0) else 0.0
    return {
        "mean": mean,
        "min": minimum,
        "max": maximum,
        "range": value_range,
        "std": std,
        "coefficient_of_variation": coefficient,
        "relative_range": relative_range,
    }


def _coverage_by_axis(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    axes: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        for axis, axis_payload in row.get("coverage", {}).get("axes", {}).items():
            axes.setdefault(axis, []).append(axis_payload)
    result: dict[str, dict[str, float]] = {}
    for axis, payloads in axes.items():
        coverage_values = [
            float(item["coverage_rate"])
            for item in payloads
            if item.get("coverage_rate") is not None
        ]
        balance_values = [_axis_balance(item) for item in payloads]
        result[axis] = {
            "coverage_rate_avg": statistics.fmean(coverage_values) if coverage_values else 0.0,
            "balance_avg": statistics.fmean(balance_values) if balance_values else 0.0,
        }
    return result


def _sampling_quality_scores(rows: list[dict[str, Any]], metric_stats: dict[str, dict[str, float]]) -> dict[str, float]:
    coverage_values: list[float] = []
    balance_values: list[float] = []
    for row in rows:
        axes = row.get("coverage", {}).get("axes", {})
        for axis_payload in axes.values():
            if axis_payload.get("coverage_rate") is not None:
                coverage_values.append(float(axis_payload["coverage_rate"]))
            balance_values.append(_axis_balance(axis_payload))
    coverage_score = statistics.fmean(coverage_values) if coverage_values else 0.0
    balance_score = statistics.fmean(balance_values) if balance_values else 0.0
    cv_values = [
        float(metric_stats[key].get("coefficient_of_variation", 0.0) or 0.0)
        for key, _ in CONVERGENCE_METRICS
        if key != "replay_count"
    ]
    avg_cv = statistics.fmean(cv_values) if cv_values else 0.0
    stability_score = max(0.0, 1.0 - avg_cv)
    overall = 0.4 * coverage_score + 0.3 * balance_score + 0.3 * stability_score
    return {
        "coverage_score": coverage_score,
        "balance_score": balance_score,
        "stability_score": stability_score,
        "overall_sampling_quality_score": overall,
    }


def _axis_balance(axis_payload: dict[str, Any]) -> float:
    counts = axis_payload.get("observed_counts", {})
    if not isinstance(counts, dict) or not counts:
        return 0.0
    expected_values = axis_payload.get("expected_values", [])
    if expected_values:
        values = [float(counts.get(str(value), 0) or 0) for value in expected_values]
    else:
        values = [float(value or 0) for value in counts.values()]
    maximum = max(values) if values else 0.0
    if math.isclose(maximum, 0.0):
        return 0.0
    return max(0.0, min(values) / maximum)


def _high_variance_metrics(metric_stats: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    items = [
        {
            "key": key,
            "label": payload.get("label", key),
            "range": float(payload.get("range", 0.0) or 0.0),
            "coefficient_of_variation": float(payload.get("coefficient_of_variation", 0.0) or 0.0),
        }
        for key, payload in metric_stats.items()
    ]
    items.sort(key=lambda item: (item["coefficient_of_variation"], item["range"]), reverse=True)
    return items[:5]


def _replay_count(path: Any) -> int:
    if not path:
        return 0
    replay_path = Path(str(path))
    if not replay_path.exists():
        return 0
    payload = json.loads(replay_path.read_text(encoding="utf-8"))
    return int(payload.get("replay_count", 0) or 0)


def _fmt(value: Any) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "0.000"

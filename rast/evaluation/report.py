"""Aggregate 결과를 Markdown result report로 변환합니다."""

from __future__ import annotations

import csv
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_SECTIONS: tuple[str, ...] = (
    "Experiment Context",
    "Simulator and Scope",
    "Scenarios",
    "Baselines",
    "Metrics",
    "Before/After Context",
    "EventToken Summary",
    "RelationToken Summary",
    "Aggregate Results",
    "Scenario-level Observations",
    "Baseline Disagreement Analysis",
    "Decision Trace Summary",
    "Scene Graph Baseline Summary",
    "Event-aware Planner Summary",
    "Event-aware Ablation Summary",
    "Threshold and Noise Sensitivity Summary",
    "Latency Summary",
    "Incremental Update Summary",
    "What This Result Supports",
    "What This Result Does Not Support",
    "Limitations",
    "Next Steps",
)


def generate_result_report(
    *,
    results_path: str | Path,
    summary_path: str | Path | None = None,
) -> str:
    """aggregate_results와 선택적 aggregate_summary를 읽어 Markdown report를 생성합니다."""

    results = read_table(results_path)
    summary_rows = read_table(summary_path) if summary_path is not None and Path(summary_path).exists() else []
    stats = compute_report_stats(results)
    lines: list[str] = []

    lines.extend(_title())
    lines.extend(_experiment_context(stats, results_path=Path(results_path), summary_path=Path(summary_path) if summary_path else None))
    lines.extend(_simulator_and_scope())
    lines.extend(_scenarios(stats))
    lines.extend(_baselines())
    lines.extend(_metrics())
    lines.extend(_before_after_context())
    lines.extend(_event_token_summary(stats))
    lines.extend(_relation_token_summary(stats))
    lines.extend(_aggregate_results(stats))
    lines.extend(_scenario_observations(stats, summary_rows))
    lines.extend(_baseline_disagreement_analysis(stats))
    lines.extend(_decision_trace_summary(stats))
    lines.extend(_scene_graph_baseline_summary(stats))
    lines.extend(_event_aware_planner_summary(stats))
    lines.extend(_event_aware_ablation_summary(stats))
    lines.extend(_threshold_and_noise_sensitivity_summary(stats))
    lines.extend(_latency_summary(stats))
    lines.extend(_incremental_update_summary(stats))
    lines.extend(_supports())
    lines.extend(_does_not_support())
    lines.extend(_limitations())
    lines.extend(_next_steps())
    return "\n".join(lines).rstrip() + "\n"


def write_result_report(
    *,
    results_path: str | Path,
    output_path: str | Path,
    summary_path: str | Path | None = None,
) -> str:
    """Markdown report를 생성하고 output_path에 저장합니다."""

    markdown = generate_result_report(results_path=results_path, summary_path=summary_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    return markdown


def read_table(path: str | Path | None) -> list[dict[str, Any]]:
    """CSV 또는 JSON aggregate table을 읽습니다."""

    if path is None:
        return []
    table_path = Path(path)
    if not table_path.exists():
        raise FileNotFoundError(f"결과 파일을 찾을 수 없습니다: {table_path}")
    if table_path.suffix.lower() == ".json":
        data = json.loads(table_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [dict(item) for item in data]
        if isinstance(data, dict):
            return [dict(item) for item in data.get("rows", [])]
        raise ValueError(f"지원하지 않는 JSON 구조입니다: {table_path}")
    with table_path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def compute_report_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Markdown 생성에 필요한 집계값을 계산합니다."""

    successful_rows = [row for row in rows if str(row.get("status", "success")).lower() == "success"]
    event_aware_rows = [row for row in successful_rows if str(row.get("apply_policy", "")) == "event_aware_rast"]
    scenario_groups = group_by(successful_rows, "scenario")
    policy_groups = group_by(successful_rows, "apply_policy")
    update_mode_groups = group_by(successful_rows, "update_mode", default="full_recompute")
    event_policy_variant_groups = group_by(event_aware_rows, "event_policy_variant", default="full")
    risk_threshold_groups = group_by(successful_rows, "risk_threshold")
    noise_level_groups = group_by_func(successful_rows, _row_noise_level)
    return {
        "total_runs": len(rows),
        "failed_runs": len(rows) - len(successful_rows),
        "successful_runs": len(successful_rows),
        "scenarios": sorted({str(row.get("scenario", "")) for row in rows if row.get("scenario", "")}),
        "apply_policies": sorted({str(row.get("apply_policy", "")) for row in rows if row.get("apply_policy", "")}),
        "update_modes": sorted({_row_update_mode(row) for row in rows}),
        "event_policy_variants": sorted({str(row.get("event_policy_variant") or "full") for row in rows}),
        "scenario_stats": {
            scenario: _group_stats(items)
            for scenario, items in sorted(scenario_groups.items())
        },
        "policy_stats": {
            policy: _group_stats(items)
            for policy, items in sorted(policy_groups.items())
        },
        "update_mode_stats": {
            mode: _group_stats(items)
            for mode, items in sorted(update_mode_groups.items())
        },
        "event_policy_variant_stats": {
            variant: _group_stats(items)
            for variant, items in sorted(event_policy_variant_groups.items())
        },
        "risk_threshold_stats": {
            threshold: _group_stats(items)
            for threshold, items in sorted(risk_threshold_groups.items())
        },
        "noise_level_stats": {
            noise_level: _group_stats(items)
            for noise_level, items in sorted(noise_level_groups.items())
        },
        "scenario_event_policy_variant_stats": {
            key: _group_stats(items)
            for key, items in sorted(group_by_func(event_aware_rows, _scenario_event_policy_variant_key).items())
        },
        "overall": _group_stats(successful_rows),
    }


def group_by(rows: list[dict[str, Any]], key: str, *, default: str = "") -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or default)].append(row)
    return grouped


def group_by_func(rows: list[dict[str, Any]], key_func) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(key_func(row))].append(row)
    return grouped


def _row_update_mode(row: dict[str, Any]) -> str:
    return str(row.get("update_mode") or "full_recompute")


def _row_noise_level(row: dict[str, Any]) -> str:
    return (
        f"position={row.get('position_noise_std') or 0.0}, "
        f"distance={row.get('distance_noise_std') or 0.0}, "
        f"visibility={row.get('visibility_flip_prob') or 0.0}"
    )


def _scenario_event_policy_variant_key(row: dict[str, Any]) -> str:
    return f"{row.get('scenario', '')} | {row.get('event_policy_variant') or 'full'}"


def _group_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_count": float(len(rows)),
        "success_rate": average(_bool_to_float(row.get("success")) for row in rows),
        "near_miss_count_avg": average(_to_float(row.get("near_miss_count")) for row in rows),
        "rast_vs_object_list_disagreement_avg": average(
            _to_float(row.get("rast_vs_object_list_disagreement_count")) for row in rows
        ),
        "rast_vs_flat_feature_disagreement_avg": average(
            _to_float(row.get("rast_vs_flat_feature_disagreement_count")) for row in rows
        ),
        "object_list_vs_flat_feature_disagreement_avg": average(
            _to_float(row.get("object_list_vs_flat_feature_disagreement_count")) for row in rows
        ),
        "rast_vs_event_aware_disagreement_avg": average(
            _to_float(row.get("rast_vs_event_aware_disagreement_count")) for row in rows
        ),
        "rast_vs_scene_graph_disagreement_avg": average(
            _to_float(row.get("rast_vs_scene_graph_disagreement_count")) for row in rows
        ),
        "scene_graph_vs_flat_feature_disagreement_avg": average(
            _to_float(row.get("scene_graph_vs_flat_feature_disagreement_count")) for row in rows
        ),
        "latency_avg_ms": average(_to_float(row.get("latency_avg_ms")) for row in rows),
        "latency_p50_ms": average(_to_float(row.get("latency_p50_ms")) for row in rows),
        "latency_p95_ms": average(_to_float(row.get("latency_p95_ms")) for row in rows),
        "token_generation_latency_avg_ms": average(_to_float(row.get("token_generation_latency_avg_ms")) for row in rows),
        "planning_latency_avg_ms": average(_to_float(row.get("planning_latency_avg_ms")) for row in rows),
        "total_latency_avg_ms": average(_to_float(row.get("total_latency_avg_ms")) for row in rows),
        "event_token_count_total": sum(_to_float(row.get("event_token_count_total")) or 0.0 for row in rows),
        "event_token_count_total_avg": average(_to_float(row.get("event_token_count_total")) for row in rows),
        "event_token_count_avg": average(_to_float(row.get("event_token_count_avg")) for row in rows),
        "event_type_counts": dict(_merge_event_type_counts(rows)),
        "relation_token_count_total": sum(_to_float(row.get("relation_token_count_total")) or 0.0 for row in rows),
        "relation_token_count_total_avg": average(_to_float(row.get("relation_token_count_total")) for row in rows),
        "relation_token_count_avg": average(_to_float(row.get("relation_token_count_avg")) for row in rows),
        "relation_type_counts": dict(_merge_count_dicts(rows, "relation_type_counts")),
        "scene_graph_node_count_avg": average(_to_float(row.get("scene_graph_node_count_avg")) for row in rows),
        "scene_graph_edge_count_avg": average(_to_float(row.get("scene_graph_edge_count_avg")) for row in rows),
        "changed_object_count_avg": average(_to_float(row.get("changed_object_count_avg")) for row in rows),
        "affected_token_count_avg": average(_to_float(row.get("affected_token_count_avg")) for row in rows),
        "full_recompute_latency_avg_ms": average(_to_float(row.get("full_recompute_latency_avg_ms")) for row in rows),
        "incremental_update_latency_avg_ms": average(
            _to_float(row.get("incremental_update_latency_avg_ms")) for row in rows
        ),
        "incremental_update_benefit_avg": average(_to_float(row.get("incremental_update_benefit_avg")) for row in rows),
        "rast_reason_code_counts": dict(_merge_count_dicts(rows, "rast_reason_code_counts")),
        "object_list_reason_code_counts": dict(_merge_count_dicts(rows, "object_list_reason_code_counts")),
        "flat_feature_reason_code_counts": dict(_merge_count_dicts(rows, "flat_feature_reason_code_counts")),
        "scene_graph_action_counts": dict(_merge_count_dicts(rows, "scene_graph_action_counts")),
        "scene_graph_reason_code_counts": dict(_merge_count_dicts(rows, "scene_graph_reason_code_counts")),
        "event_aware_rast_action_counts": dict(_merge_count_dicts(rows, "event_aware_rast_action_counts")),
        "event_aware_rast_reason_code_counts": dict(_merge_count_dicts(rows, "event_aware_rast_reason_code_counts")),
        "event_policy_variant_action_counts": dict(_merge_nested_count_dicts(rows, "event_policy_variant_action_counts")),
        "event_policy_variant_reason_code_counts": dict(
            _merge_nested_count_dicts(rows, "event_policy_variant_reason_code_counts")
        ),
        "rast_trigger_token_count_total": sum(_to_float(row.get("rast_trigger_token_count_total")) or 0.0 for row in rows),
        "rast_trigger_token_count_total_avg": average(_to_float(row.get("rast_trigger_token_count_total")) for row in rows),
        "decision_trace_coverage": average(_to_float(row.get("decision_trace_coverage")) for row in rows),
        "scene_graph_decision_trace_coverage": average(
            _to_float(row.get("scene_graph_decision_trace_coverage")) for row in rows
        ),
        "event_triggered_action_count_total": sum(_to_float(row.get("event_triggered_action_count")) or 0.0 for row in rows),
        "event_triggered_action_count_avg": average(_to_float(row.get("event_triggered_action_count")) for row in rows),
        "event_aware_decision_trace_coverage": average(
            _to_float(row.get("event_aware_decision_trace_coverage")) for row in rows
        ),
    }


def _title() -> list[str]:
    return [
        "# RAST MVP-0 Result Report",
        "",
        "이 문서는 WindowsMetadataSim 기반 RAST MVP-0 evaluation suite 결과를 자동 요약한 보고서입니다.",
        "",
    ]


def _experiment_context(stats: dict[str, Any], *, results_path: Path, summary_path: Path | None) -> list[str]:
    summary_text = str(summary_path) if summary_path is not None else "not provided"
    return [
        "## Experiment Context",
        "",
        f"- Results source: `{results_path}`",
        f"- Summary source: `{summary_text}`",
        f"- Total runs: {stats['total_runs']}",
        f"- Successful runs: {stats['successful_runs']}",
        f"- Failed runs: {stats['failed_runs']}",
        "- Current report purpose: evaluation infrastructure 검증과 관찰 결과 정리입니다.",
        "",
    ]


def _simulator_and_scope() -> list[str]:
    return [
        "## Simulator and Scope",
        "",
        "- 이 결과는 WindowsMetadataSim 기반 deterministic metadata simulator 결과입니다.",
        "- 실제 AI2-THOR / Webots / CoppeliaSim / real robot 결과가 아닙니다.",
        "- 실제 RGB-D perception latency나 perception error를 반영하지 않습니다.",
        "- collision, near-miss, goal reaching은 simple geometry rule 기반입니다.",
        "- 현재 seed는 metadata에 기록되지만 stochastic variation은 아직 제한적입니다.",
        "- 현재 결과는 연구 주장이라기보다 evaluation infrastructure 검증입니다.",
        "",
    ]


def _scenarios(stats: dict[str, Any]) -> list[str]:
    lines = ["## Scenarios", ""]
    for scenario in stats["scenarios"]:
        lines.append(f"- `{scenario}`")
    lines.append("")
    return lines


def _baselines() -> list[str]:
    return [
        "## Baselines",
        "",
        "- Object List: object id, category, position, visible, distance, confidence 중심의 baseline입니다.",
        "- Flat Feature Table: RAST와 유사한 scalar feature를 받지만 token contract field를 제거한 baseline입니다.",
        "- RAST: EntityToken, RiskToken, EventToken logging을 포함한 planner-facing token contract 경로입니다.",
        "- Event-aware RAST: 기존 RAST planner와 분리된 실험용 planner이며 EventToken을 decision reason에 반영합니다.",
        "- 기존 RAST planner는 EventToken으로 action을 바꾸지 않으며, Event-aware RAST planner에서만 실험적으로 EventToken reason을 사용합니다.",
        "",
    ]


def _metrics() -> list[str]:
    return [
        "## Metrics",
        "",
        "- success / goal_reached",
        "- completed_steps",
        "- collision_count / near_miss_count",
        "- RAST vs Object List disagreement",
        "- RAST vs Flat Feature disagreement",
        "- Object List vs Flat Feature disagreement",
        "- RAST vs Event-aware RAST disagreement",
        "- token_count_avg / object_count_avg / flat_feature_row_count_avg",
        "- event_token_count_total / event_token_count_avg / event_type_counts",
        "- update_mode / changed_object_count_avg / affected_token_count_avg",
        "- full_recompute_latency_avg_ms / incremental_update_latency_avg_ms / incremental_update_benefit_avg",
        "- rast_reason_code_counts / object_list_reason_code_counts / flat_feature_reason_code_counts",
        "- event_aware_rast_reason_code_counts / event_triggered_action_count",
        "- event_policy_variant / event_policy_variant_action_counts / event_policy_variant_reason_code_counts",
        "- risk_threshold / near_miss_threshold",
        "- position_noise_std / distance_noise_std / visibility_flip_prob",
        "- rast_trigger_token_count_total / decision_trace_coverage",
        "- event_aware_decision_trace_coverage",
        "- latency_avg_ms / latency_p50_ms / latency_p95_ms",
        "- token_generation_latency_avg_ms / planning_latency_avg_ms / total_latency_avg_ms",
        "",
    ]


def _before_after_context() -> list[str]:
    return [
        "## Before/After Context",
        "",
        "- 이전 report는 EventToken 추가 전 Object List / Flat Feature / RAST baseline comparison 결과였습니다.",
        "- 현재 report는 EventToken이 step log와 episode summary, aggregate result에 포함된 이후의 결과입니다.",
        "- EventToken은 semantic event 감지와 기록을 위한 token이며, 기존 RAST planner action에는 영향을 주지 않습니다.",
        "- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용됩니다. incremental update optimization is experimental.",
        "- 현재 report는 Event-aware RAST planner가 추가되어 EventToken을 action reason으로 사용할 수 있는 이후 결과입니다.",
        "- Event-aware planner는 deterministic rule-based policy이며 성능 개선을 단정하기 위한 결과가 아닙니다.",
        "- 따라서 현재 결과는 EventToken의 감지와 기록 검증이지, EventToken이 planning 성능을 개선했다는 증거가 아닙니다.",
        "",
    ]


def _event_token_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    event_type_counts = overall["event_type_counts"]
    total_event_tokens = int(overall["event_token_count_total"])
    lines = [
        "## EventToken Summary",
        "",
        f"- EventToken included in this report: {'yes' if total_event_tokens > 0 else 'no'}",
        f"- Total EventToken count across successful runs: {total_event_tokens}",
        f"- Average EventToken count per episode: {_fmt(overall['event_token_count_total_avg'])}",
        f"- Average EventToken count per step: {_fmt(overall['event_token_count_avg'])}",
        "- EventToken affects only the separate Event-aware RAST experimental planner; the existing RAST planner remains unchanged.",
        "- EventToken은 현재 semantic event diff 기반으로 생성되며 실제 perception event detection 결과가 아닙니다.",
        "",
        "| Event Type | Occurred | Count |",
        "|---|---:|---:|",
    ]
    for event_type in ("object_appeared", "object_moved", "risk_changed", "object_disappeared"):
        count = int(event_type_counts.get(event_type, 0))
        lines.append(f"| `{event_type}` | {'yes' if count > 0 else 'no'} | {count} |")

    lines.extend(
        [
            "",
            "| Scenario | Runs | Avg Event Tokens / Episode | Avg Event Tokens / Step | Event Type Counts |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['event_token_count_total_avg'])} | "
            f"{_fmt(item['event_token_count_avg'])} | "
            f"`{_json_compact(item['event_type_counts'])}` |"
        )
    lines.append("")
    return lines


def _relation_token_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    relation_counts = overall["relation_type_counts"]
    total_relations = int(overall["relation_token_count_total"])
    lines = [
        "## RelationToken Summary",
        "",
        f"- RelationToken included in this report: {'yes' if total_relations > 0 else 'no'}",
        f"- Total RelationToken count across successful runs: {total_relations}",
        f"- Average RelationToken count per episode: {_fmt(overall['relation_token_count_total_avg'])}",
        f"- Average RelationToken count per step: {_fmt(overall['relation_token_count_avg'])}",
        f"- Relation type distribution: `{_json_compact(relation_counts)}`",
        "- RelationToken은 MVP에서 navigation relation만 다루며 learned relation extraction 결과가 아닙니다.",
        "- Relation은 simple geometry rule 기반이므로 실제 perception relation 품질을 검증하지 않습니다.",
        "",
        "| Scenario | Runs | Avg Relation Tokens / Episode | Avg Relation Tokens / Step | Relation Type Counts |",
        "|---|---:|---:|---:|---|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['relation_token_count_total_avg'])} | "
            f"{_fmt(item['relation_token_count_avg'])} | "
            f"`{_json_compact(item['relation_type_counts'])}` |"
        )
    lines.append("")
    return lines


def _scene_graph_baseline_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    lines = [
        "## Scene Graph Baseline Summary",
        "",
        "- Scene Graph baseline은 MVP용 simplified graph입니다.",
        "- Graph node는 agent/object/optional goal이며 edge는 near_agent, near_path, blocking_path, target_reachable relation입니다.",
        "- Scene Graph planner는 RiskToken의 severity, risk_type, recommended_policy 같은 RAST-only contract field를 사용하지 않습니다.",
        f"- Average Scene Graph node count: {_fmt(overall['scene_graph_node_count_avg'])}",
        f"- Average Scene Graph edge count: {_fmt(overall['scene_graph_edge_count_avg'])}",
        f"- Average RAST vs Scene Graph disagreement: {_fmt(overall['rast_vs_scene_graph_disagreement_avg'])}",
        f"- Average Scene Graph vs Flat Feature disagreement: {_fmt(overall['scene_graph_vs_flat_feature_disagreement_avg'])}",
        f"- Average Scene Graph decision trace coverage: {_fmt(overall['scene_graph_decision_trace_coverage'])}",
        f"- Scene Graph reason code distribution: `{_json_compact(overall['scene_graph_reason_code_counts'])}`",
        "- RAST와 Scene Graph의 차이는 representation 차이를 관찰하기 위한 것이며 RAST 우수성을 의미하지 않습니다.",
        "",
        "| Scenario | Runs | Avg Nodes | Avg Edges | Avg RAST vs Scene Graph | Scene Graph Reason Codes |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['scene_graph_node_count_avg'])} | "
            f"{_fmt(item['scene_graph_edge_count_avg'])} | "
            f"{_fmt(item['rast_vs_scene_graph_disagreement_avg'])} | "
            f"`{_json_compact(item['scene_graph_reason_code_counts'])}` |"
        )
    lines.append("")
    return lines


def _aggregate_results(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    return [
        "## Aggregate Results",
        "",
        f"- Total runs: {stats['total_runs']}",
        f"- Failed runs: {stats['failed_runs']}",
        f"- Overall success rate: {_fmt(overall['success_rate'])}",
        f"- Overall average near-miss count: {_fmt(overall['near_miss_count_avg'])}",
        f"- Overall latency avg / p50 / p95 ms: {_fmt(overall['latency_avg_ms'])} / {_fmt(overall['latency_p50_ms'])} / {_fmt(overall['latency_p95_ms'])}",
        "",
    ]


def _scenario_observations(stats: dict[str, Any], summary_rows: list[dict[str, Any]]) -> list[str]:
    del summary_rows  # 현재는 aggregate_results를 source of truth로 재계산합니다.
    lines = [
        "## Scenario-level Observations",
        "",
        "| Scenario | Runs | Success Rate | Avg Near-miss | Avg RAST vs Object | Avg RAST vs Flat | Avg Object vs Flat | Avg RAST vs Event-aware |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | {_fmt(item['success_rate'])} | "
            f"{_fmt(item['near_miss_count_avg'])} | "
            f"{_fmt(item['rast_vs_object_list_disagreement_avg'])} | "
            f"{_fmt(item['rast_vs_flat_feature_disagreement_avg'])} | "
            f"{_fmt(item['object_list_vs_flat_feature_disagreement_avg'])} | "
            f"{_fmt(item['rast_vs_event_aware_disagreement_avg'])} |"
        )
    lines.append("")
    return lines


def _baseline_disagreement_analysis(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    rast_flat = overall["rast_vs_flat_feature_disagreement_avg"]
    rast_object = overall["rast_vs_object_list_disagreement_avg"]
    object_flat = overall["object_list_vs_flat_feature_disagreement_avg"]
    rast_event = overall["rast_vs_event_aware_disagreement_avg"]
    lines = [
        "## Baseline Disagreement Analysis",
        "",
        f"- Average RAST vs Object List disagreement: {_fmt(rast_object)}",
        f"- Average RAST vs Flat Feature disagreement: {_fmt(rast_flat)}",
        f"- Average Object List vs Flat Feature disagreement: {_fmt(object_flat)}",
        f"- Average RAST vs Event-aware RAST disagreement: {_fmt(rast_event)}",
        "- Flat Feature가 RAST와 자주 일치한다면, 현재 toy setup에서는 scalar risk feature가 두 planner의 action을 크게 좌우한다는 뜻으로 해석해야 합니다.",
        "- Object List와 RAST가 달라지는 경우는 distance-only object view와 risk-aware scalar/token view가 서로 다른 action boundary를 만들 수 있음을 보여줍니다.",
        "- 이 차이는 아직 RAST의 우수성을 뜻하지 않으며, 같은 information bound에서 구조화 효과를 더 분리해 검증해야 합니다.",
        "",
    ]
    return lines


def _decision_trace_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    lines = [
        "## Decision Trace Summary",
        "",
        "- PlannerDecision trace is included in this report when planner reason_code fields are present in aggregate results.",
        f"- Average decision_trace_coverage: {_fmt(overall['decision_trace_coverage'])}",
        f"- Total RAST trigger token references: {int(overall['rast_trigger_token_count_total'])}",
        f"- Average RAST trigger token references per episode: {_fmt(overall['rast_trigger_token_count_total_avg'])}",
        "- RAST, Object List, and Flat Feature planners can choose the same action for different reasons.",
        "- These traces are rule-based planner explanations, not learned model interpretability results.",
        "- EventToken is used only by the separate Event-aware RAST experimental planner; the existing RAST planner remains unchanged.",
        "",
        "| Planner | Reason Code Counts |",
        "|---|---|",
        f"| RAST | `{_json_compact(overall['rast_reason_code_counts'])}` |",
        f"| Object List | `{_json_compact(overall['object_list_reason_code_counts'])}` |",
        f"| Flat Feature | `{_json_compact(overall['flat_feature_reason_code_counts'])}` |",
        f"| Event-aware RAST | `{_json_compact(overall['event_aware_rast_reason_code_counts'])}` |",
        "",
        "| Scenario | Runs | Decision Trace Coverage | RAST Reason Codes |",
        "|---|---:|---:|---|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['decision_trace_coverage'])} | "
            f"`{_json_compact(item['rast_reason_code_counts'])}` |"
        )
    lines.append("")
    return lines


def _event_aware_planner_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    reason_counts = overall["event_aware_rast_reason_code_counts"]
    event_triggered_total = int(overall["event_triggered_action_count_total"])
    event_aware_included = "event_aware_rast" in stats["apply_policies"] or bool(reason_counts)
    differing_scenarios = [
        scenario
        for scenario, item in stats["scenario_stats"].items()
        if item["rast_vs_event_aware_disagreement_avg"] > 0
    ]
    lines = [
        "## Event-aware Planner Summary",
        "",
        f"- Event-aware RAST planner included in this report: {'yes' if event_aware_included else 'no'}",
        f"- Average RAST vs Event-aware RAST disagreement: {_fmt(overall['rast_vs_event_aware_disagreement_avg'])}",
        f"- Total event-triggered Event-aware actions: {event_triggered_total}",
        f"- Average event-triggered Event-aware actions per episode: {_fmt(overall['event_triggered_action_count_avg'])}",
        f"- Average Event-aware decision trace coverage: {_fmt(overall['event_aware_decision_trace_coverage'])}",
        f"- Event-aware reason code distribution: `{_json_compact(reason_counts)}`",
        f"- Scenarios with observed RAST vs Event-aware disagreement: `{', '.join(differing_scenarios) if differing_scenarios else 'none'}`",
        "- 같은 action이 선택되더라도 기존 RAST와 Event-aware RAST의 reason_code는 다를 수 있습니다.",
        "- Event-aware planner는 deterministic rule-based experimental policy이며 성능 개선을 단정하는 근거가 아닙니다.",
        "",
        "| Scenario | Runs | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions | Event-aware Reason Codes |",
        "|---|---:|---:|---:|---|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['rast_vs_event_aware_disagreement_avg'])} | "
            f"{_fmt(item['event_triggered_action_count_avg'])} | "
            f"`{_json_compact(item['event_aware_rast_reason_code_counts'])}` |"
        )
    lines.append("")
    return lines


def _event_aware_ablation_summary(stats: dict[str, Any]) -> list[str]:
    lines = [
        "## Event-aware Ablation Summary",
        "",
        "- Event-aware policy variant가 aggregate row에 기록되어 variant별 비교가 가능합니다.",
        "- `logging_only` variant는 EventToken을 입력으로 받지만 action에는 사용하지 않는 비교 조건입니다.",
        "- 이 표는 어떤 event rule이 action change와 함께 관찰되는지 분리하기 위한 infrastructure이며, 성능 개선 주장으로 해석하면 안 됩니다.",
        "",
        "| Event Policy Variant | Runs | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions | Reason Codes |",
        "|---|---:|---:|---:|---|",
    ]
    for variant, item in stats["event_policy_variant_stats"].items():
        lines.append(
            f"| `{variant}` | {int(item['run_count'])} | "
            f"{_fmt(item['rast_vs_event_aware_disagreement_avg'])} | "
            f"{_fmt(item['event_triggered_action_count_avg'])} | "
            f"`{_json_compact(item['event_aware_rast_reason_code_counts'])}` |"
        )
    lines.extend(
        [
            "",
            "| Scenario / Variant | Runs | Avg Disagreement | Avg Event-triggered Actions |",
            "|---|---:|---:|---:|",
        ]
    )
    for key, item in stats["scenario_event_policy_variant_stats"].items():
        lines.append(
            f"| `{key}` | {int(item['run_count'])} | "
            f"{_fmt(item['rast_vs_event_aware_disagreement_avg'])} | "
            f"{_fmt(item['event_triggered_action_count_avg'])} |"
        )
    lines.extend(
        [
            "",
            "- variant별 reason_code distribution은 event rule 활성/비활성에 따른 action trace 차이를 보는 용도입니다.",
            "- 현재 Event-aware planner는 deterministic rule-based policy이며 learned extractor나 learned policy가 아닙니다.",
            "",
        ]
    )
    return lines


def _threshold_and_noise_sensitivity_summary(stats: dict[str, Any]) -> list[str]:
    lines = [
        "## Threshold and Noise Sensitivity Summary",
        "",
        "- risk_threshold와 near_miss_threshold는 aggregate row에 보존되어 threshold sweep 분석에 사용할 수 있습니다.",
        "- noise 값은 WindowsMetadataSim metadata에 적용한 synthetic seeded noise이며 실제 perception error가 아닙니다.",
        "- 아래 값은 deterministic metadata simulator에서의 sensitivity 관찰용이며 real-world robustness claim을 지원하지 않습니다.",
        "",
        "| Risk Threshold | Runs | Avg Near-miss | Avg RAST vs Event-aware Disagreement | Avg Event-triggered Actions |",
        "|---|---:|---:|---:|---:|",
    ]
    for threshold, item in stats["risk_threshold_stats"].items():
        lines.append(
            f"| `{threshold}` | {int(item['run_count'])} | "
            f"{_fmt(item['near_miss_count_avg'])} | "
            f"{_fmt(item['rast_vs_event_aware_disagreement_avg'])} | "
            f"{_fmt(item['event_triggered_action_count_avg'])} |"
        )
    lines.extend(
        [
            "",
            "| Noise Level | Runs | Success Rate | Avg Near-miss | Avg Disagreement |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for noise_level, item in stats["noise_level_stats"].items():
        lines.append(
            f"| `{noise_level}` | {int(item['run_count'])} | "
            f"{_fmt(item['success_rate'])} | "
            f"{_fmt(item['near_miss_count_avg'])} | "
            f"{_fmt(item['rast_vs_event_aware_disagreement_avg'])} |"
        )
    lines.extend(
        [
            "",
            "- default suite가 작게 유지되는 경우 threshold/noise level 수가 제한될 수 있습니다.",
            "- 더 강한 결론을 위해서는 별도 extended config로 threshold와 synthetic noise grid를 확장해야 합니다.",
            "",
        ]
    )
    return lines


def _latency_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    lines = [
        "## Latency Summary",
        "",
        f"- Average latency: {_fmt(overall['latency_avg_ms'])} ms",
        f"- Average p50 latency: {_fmt(overall['latency_p50_ms'])} ms",
        f"- Average p95 latency: {_fmt(overall['latency_p95_ms'])} ms",
        f"- Average token generation latency: {_fmt(overall['token_generation_latency_avg_ms'])} ms",
        f"- Average planning latency: {_fmt(overall['planning_latency_avg_ms'])} ms",
        "- 이 latency는 Python metadata simulator 경로에서 측정된 값이며, real rendering이나 perception model overhead를 포함하지 않습니다.",
        "",
    ]
    lines.extend(_policy_latency_table(stats))
    return lines


def _policy_latency_table(stats: dict[str, Any]) -> list[str]:
    lines = [
        "| Apply Policy | Runs | Avg Latency ms | Avg Planning ms |",
        "|---|---:|---:|---:|",
    ]
    for policy, item in stats["policy_stats"].items():
        lines.append(
            f"| `{policy}` | {int(item['run_count'])} | {_fmt(item['latency_avg_ms'])} | {_fmt(item['planning_latency_avg_ms'])} |"
        )
    lines.append("")
    return lines


def _incremental_update_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    lines = [
        "## Incremental Update Summary",
        "",
        "- 이 섹션은 full token recomputation과 TokenMemory 기반 event-aware incremental update의 latency protocol을 비교합니다.",
        "- incremental update optimization is experimental; 현재 결과는 최적화 완료나 planner 성능 개선을 의미하지 않습니다.",
        "- WindowsMetadataSim은 metadata-only toy simulator이므로 absolute latency value는 매우 작고 실제 perception/model cost를 포함하지 않습니다.",
        "- 이번 runner는 같은 snapshot에서 full_recompute와 incremental 후보를 모두 측정하고, 선택된 update_mode의 token generation latency를 step latency에 기록합니다.",
        f"- Overall changed object count avg: {_fmt(overall['changed_object_count_avg'])}",
        f"- Overall affected token count avg: {_fmt(overall['affected_token_count_avg'])}",
        f"- Overall full recompute latency avg: {_fmt(overall['full_recompute_latency_avg_ms'])} ms",
        f"- Overall incremental update latency avg: {_fmt(overall['incremental_update_latency_avg_ms'])} ms",
        f"- Overall incremental update benefit avg: {_fmt(overall['incremental_update_benefit_avg'])}",
        "",
        "| Update Mode | Runs | Changed Objects Avg | Affected Tokens Avg | Full ms | Incremental ms | Benefit |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, item in stats["update_mode_stats"].items():
        lines.append(
            f"| `{mode}` | {int(item['run_count'])} | "
            f"{_fmt(item['changed_object_count_avg'])} | "
            f"{_fmt(item['affected_token_count_avg'])} | "
            f"{_fmt(item['full_recompute_latency_avg_ms'])} | "
            f"{_fmt(item['incremental_update_latency_avg_ms'])} | "
            f"{_fmt(item['incremental_update_benefit_avg'])} |"
        )
    lines.extend(
        [
            "",
            "| Scenario | Runs | Changed Objects Avg | Affected Tokens Avg | Incremental Benefit Avg |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['changed_object_count_avg'])} | "
            f"{_fmt(item['affected_token_count_avg'])} | "
            f"{_fmt(item['incremental_update_benefit_avg'])} |"
        )
    lines.append("")
    return lines


def _supports() -> list[str]:
    return [
        "## What This Result Supports",
        "",
        "- WindowsMetadataSim 기반 scenario suite를 반복 실행할 수 있음을 보여줍니다.",
        "- Object List / Flat Feature Table / RAST 세 representation과 planner action을 같은 log/summary contract로 기록할 수 있음을 보여줍니다.",
        "- scenario별 disagreement, near-miss, success, latency를 aggregate table로 모을 수 있음을 보여줍니다.",
        "- Flat Feature baseline을 통해 정보량 효과와 token contract 효과를 분리해서 보기 위한 실험 인프라가 준비되었음을 보여줍니다.",
        "- EventToken이 semantic event를 감지하고 step log, episode summary, aggregate result에 기록될 수 있음을 보여줍니다.",
        "- 별도 Event-aware RAST planner가 EventToken을 decision reason으로 사용할 수 있음을 보여줍니다.",
        "- 세 planner의 action 선택 사유를 PlannerDecision trace로 기록하고 집계할 수 있음을 보여줍니다.",
        "",
    ]


def _does_not_support() -> list[str]:
    return [
        "## What This Result Does Not Support",
        "",
        "- This result does not support real-world performance claims.",
        "- RAST가 Object List나 Flat Feature보다 일반적으로 우수하다는 결론을 지원하지 않습니다.",
        "- Event-aware planner나 EventToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.",
        "- Decision trace는 rule-based planner 로그이며 learned model explanation 품질을 검증하지 않습니다.",
        "- 실제 RGB-D perception, detector error, occlusion error, sim-to-real 성능을 검증하지 않습니다.",
        "- 상용 자율주행 또는 real robot safety guarantee를 제공하지 않습니다.",
        "- AI2-THOR / Webots / CoppeliaSim / real robot 환경에서의 성능을 대변하지 않습니다.",
        "",
    ]


def _limitations() -> list[str]:
    return [
        "## Limitations",
        "",
        "- deterministic metadata simulator이므로 물리, 렌더링, 센서 노이즈가 제한적입니다.",
        "- collision, near-miss, goal reaching은 simple geometry rule 기반입니다.",
        "- seed가 기록되지만 현재 stochastic variation은 제한적입니다.",
        "- token generation latency는 metadata 기반 Python 경로의 비용이며, perception-bound extractor 비용이 아닙니다.",
        "- EventToken은 semantic diff 기반으로 생성되며, 실제 perception event detection이 아닙니다.",
        "- Event-aware RAST planner는 deterministic rule-based policy이며 learned policy나 learned explanation이 아닙니다.",
        "- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용되지만, incremental update optimization is experimental입니다.",
        "- Batch 9의 incremental update는 measurement protocol 단계이며, 일부 token 계산은 correctness를 위해 여전히 재계산됩니다.",
        "- full_recompute와 incremental 후보를 같은 step에서 모두 측정하므로 report의 selected token_generation latency와 실제 Python wall-clock은 다를 수 있습니다.",
        "- EventToken은 별도 Event-aware planner에만 연결되므로, success/near-miss/disagreement 변화는 일반 RAST 효과로 해석하면 안 됩니다.",
        "- PlannerDecision은 현재 deterministic rule-based policy의 내부 규칙을 기록한 것이며, learned model interpretability는 아닙니다.",
        "- 동일 action이라도 planner별 reason_code와 trigger feature가 다를 수 있으므로 action count만으로 의사결정 근거를 해석하면 안 됩니다.",
        "- RelationToken과 Scene Graph baseline은 MVP용 geometry-rule 구현이며, UncertaintyToken은 아직 포함하지 않습니다.",
        "- Flat Feature와 RAST가 동일한 scalar risk rule에 강하게 묶여 있어 token contract 효과는 아직 제한적으로만 관찰됩니다.",
        "",
    ]


def _next_steps() -> list[str]:
    return [
        "## Next Steps",
        "",
        "- scenario별 failure case와 action trace를 함께 저장해 decision explainability 분석을 강화합니다.",
        "- threshold sensitivity sweep을 넓혀 RAST/Object List/Flat Feature disagreement boundary를 더 명확히 봅니다.",
        "- noise injection과 unknown/occlusion scenario를 추가해 metadata-only 결과의 한계를 점진적으로 줄입니다.",
        "- 이후 단계에서 Event-aware policy를 더 공정하게 ablation하고, 실제 incremental cache 재사용 최적화와 분리해 검토합니다.",
        "- UncertaintyToken과 perception-bound adapter는 별도 Batch로 추가합니다.",
        "- AI2-THOR나 다른 simulator로 확장할 때도 같은 aggregate/report contract를 유지합니다.",
        "",
    ]


def average(values) -> float:
    items = [item for item in values if item is not None]
    if not items:
        return 0.0
    return sum(items) / len(items)


def _to_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def _bool_to_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        return 1.0 if value.lower() == "true" else 0.0
    return 1.0 if value else 0.0


def _merge_event_type_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(_parse_event_type_counts(row.get("event_type_counts")))
    return counter


def _merge_count_dicts(rows: list[dict[str, Any]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(_parse_event_type_counts(row.get(key)))
    return counter


def _merge_nested_count_dicts(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    merged: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        parsed = _parse_nested_count_dict(row.get(key))
        for outer_key, counts in parsed.items():
            merged[outer_key].update(counts)
    return {outer_key: dict(counter) for outer_key, counter in merged.items()}


def _parse_nested_count_dict(value: Any) -> dict[str, dict[str, int]]:
    if value in ("", None):
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return {}
    if not isinstance(value, dict):
        return {}
    parsed: dict[str, dict[str, int]] = {}
    for outer_key, inner_value in value.items():
        if isinstance(inner_value, str):
            try:
                inner_value = json.loads(inner_value)
            except json.JSONDecodeError:
                inner_value = {}
        if isinstance(inner_value, dict):
            parsed[str(outer_key)] = {str(key): int(count) for key, count in inner_value.items()}
    return parsed


def _parse_event_type_counts(value: Any) -> dict[str, int]:
    if value in ("", None):
        return {}
    if isinstance(value, dict):
        return {str(key): int(count) for key, count in value.items()}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return {}
        if isinstance(parsed, dict):
            return {str(key): int(count) for key, count in parsed.items()}
    return {}


def _json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fmt(value: float) -> str:
    return f"{value:.3f}"

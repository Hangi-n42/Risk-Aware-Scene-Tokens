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
    "Suite Execution Metadata",
    "Simulator and Scope",
    "Scenarios",
    "Baselines",
    "Metrics",
    "Before/After Context",
    "EventToken Summary",
    "RelationToken Summary",
    "UncertaintyToken Summary",
    "EvidenceToken Summary",
    "AffordanceToken Summary",
    "Aggregate Results",
    "Scenario-level Observations",
    "Baseline Disagreement Analysis",
    "Decision Trace Summary",
    "Scene Graph Baseline Summary",
    "Scene Graph vs RAST Differentiation Summary",
    "Event-aware Planner Summary",
    "Uncertainty-aware Planner Summary",
    "Affordance-aware Planner Summary",
    "Event-aware Ablation Summary",
    "Threshold and Noise Sensitivity Summary",
    "Latency Summary",
    "Incremental Update Summary",
    "Replay Trace Summary",
    "Replay Artifact Summary",
    "Representative Decision Trace Summary",
    "Sampling Coverage and Stability Artifacts",
    "Sample-size Convergence Artifact",
    "What This Result Supports",
    "What This Result Does Not Support",
    "Limitations",
    "Next Steps",
)


def generate_result_report(
    *,
    results_path: str | Path,
    summary_path: str | Path | None = None,
    replay_index_path: str | Path | None = None,
    suite_metadata_path: str | Path | None = None,
    sampling_coverage_path: str | Path | None = None,
    seed_stability_path: str | Path | None = None,
    sample_size_convergence_path: str | Path | None = None,
) -> str:
    """aggregate_results와 선택적 aggregate_summary를 읽어 Markdown report를 생성합니다."""

    results = read_table(results_path)
    summary_rows = read_table(summary_path) if summary_path is not None and Path(summary_path).exists() else []
    stats = compute_report_stats(results)
    lines: list[str] = []

    lines.extend(_title())
    lines.extend(_experiment_context(stats, results_path=Path(results_path), summary_path=Path(summary_path) if summary_path else None))
    lines.extend(_suite_execution_metadata(suite_metadata_path))
    lines.extend(_simulator_and_scope())
    lines.extend(_scenarios(stats))
    lines.extend(_baselines())
    lines.extend(_metrics())
    lines.extend(_before_after_context())
    lines.extend(_event_token_summary(stats))
    lines.extend(_relation_token_summary(stats))
    lines.extend(_uncertainty_token_summary(stats))
    lines.extend(_evidence_token_summary(stats))
    lines.extend(_affordance_token_summary(stats))
    lines.extend(_aggregate_results(stats))
    lines.extend(_scenario_observations(stats, summary_rows))
    lines.extend(_baseline_disagreement_analysis(stats))
    lines.extend(_decision_trace_summary(stats))
    lines.extend(_scene_graph_baseline_summary(stats))
    lines.extend(_scene_graph_rast_differentiation_summary(stats))
    lines.extend(_event_aware_planner_summary(stats))
    lines.extend(_uncertainty_aware_planner_summary(stats))
    lines.extend(_affordance_aware_planner_summary(stats))
    lines.extend(_event_aware_ablation_summary(stats))
    lines.extend(_threshold_and_noise_sensitivity_summary(stats))
    lines.extend(_latency_summary(stats))
    lines.extend(_incremental_update_summary(stats))
    lines.extend(_replay_trace_summary())
    lines.extend(_replay_artifact_summary(replay_index_path))
    lines.extend(_representative_decision_trace_summary(stats))
    lines.extend(_sampling_coverage_and_stability_artifacts(sampling_coverage_path, seed_stability_path))
    lines.extend(_sample_size_convergence_artifact(sample_size_convergence_path))
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
    replay_index_path: str | Path | None = None,
    suite_metadata_path: str | Path | None = None,
    sampling_coverage_path: str | Path | None = None,
    seed_stability_path: str | Path | None = None,
    sample_size_convergence_path: str | Path | None = None,
) -> str:
    """Markdown report를 생성하고 output_path에 저장합니다."""

    markdown = generate_result_report(
        results_path=results_path,
        summary_path=summary_path,
        replay_index_path=replay_index_path,
        suite_metadata_path=suite_metadata_path,
        sampling_coverage_path=sampling_coverage_path,
        seed_stability_path=seed_stability_path,
        sample_size_convergence_path=sample_size_convergence_path,
    )
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
        "rast_vs_uncertainty_aware_disagreement_avg": average(
            _to_float(row.get("rast_vs_uncertainty_aware_disagreement_count")) for row in rows
        ),
        "rast_vs_affordance_aware_disagreement_avg": average(
            _to_float(row.get("rast_vs_affordance_aware_disagreement_count")) for row in rows
        ),
        "rast_vs_scene_graph_disagreement_avg": average(
            _to_float(row.get("rast_vs_scene_graph_disagreement_count")) for row in rows
        ),
        "scene_graph_vs_flat_feature_disagreement_avg": average(
            _to_float(row.get("scene_graph_vs_flat_feature_disagreement_count")) for row in rows
        ),
        "rast_vs_scene_graph_same_action_different_reason_avg": average(
            _to_float(row.get("rast_vs_scene_graph_same_action_different_reason_count")) for row in rows
        ),
        "rast_vs_scene_graph_same_action_different_reason_rate": average(
            _to_float(row.get("rast_vs_scene_graph_same_action_different_reason_rate")) for row in rows
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
        "evidence_token_count_total": sum(_to_float(row.get("evidence_token_count_total")) or 0.0 for row in rows),
        "evidence_token_count_total_avg": average(_to_float(row.get("evidence_token_count_total")) for row in rows),
        "evidence_token_count_avg": average(_to_float(row.get("evidence_token_count_avg")) for row in rows),
        "evidence_type_counts": dict(_merge_count_dicts(rows, "evidence_type_counts")),
        "risk_evidence_count_total": sum(_to_float(row.get("risk_evidence_count_total")) or 0.0 for row in rows),
        "uncertainty_evidence_count_total": sum(
            _to_float(row.get("uncertainty_evidence_count_total")) or 0.0 for row in rows
        ),
        "event_evidence_count_total": sum(_to_float(row.get("event_evidence_count_total")) or 0.0 for row in rows),
        "decision_evidence_count_total": sum(
            _to_float(row.get("decision_evidence_count_total")) or 0.0 for row in rows
        ),
        "decision_evidence_coverage": average(_to_float(row.get("decision_evidence_coverage")) for row in rows),
        "relation_token_count_total": sum(_to_float(row.get("relation_token_count_total")) or 0.0 for row in rows),
        "relation_token_count_total_avg": average(_to_float(row.get("relation_token_count_total")) for row in rows),
        "relation_token_count_avg": average(_to_float(row.get("relation_token_count_avg")) for row in rows),
        "relation_type_counts": dict(_merge_count_dicts(rows, "relation_type_counts")),
        "uncertainty_token_count_total": sum(
            _to_float(row.get("uncertainty_token_count_total")) or 0.0 for row in rows
        ),
        "uncertainty_token_count_total_avg": average(
            _to_float(row.get("uncertainty_token_count_total")) for row in rows
        ),
        "uncertainty_token_count_avg": average(_to_float(row.get("uncertainty_token_count_avg")) for row in rows),
        "uncertainty_type_counts": dict(_merge_count_dicts(rows, "uncertainty_type_counts")),
        "high_uncertainty_count_total": sum(
            _to_float(row.get("high_uncertainty_count_total")) or 0.0 for row in rows
        ),
        "high_uncertainty_count_total_avg": average(
            _to_float(row.get("high_uncertainty_count_total")) for row in rows
        ),
        "high_uncertainty_count_avg": average(_to_float(row.get("high_uncertainty_count_avg")) for row in rows),
        "affordance_token_count_total": sum(
            _to_float(row.get("affordance_token_count_total")) or 0.0 for row in rows
        ),
        "affordance_token_count_total_avg": average(
            _to_float(row.get("affordance_token_count_total")) for row in rows
        ),
        "affordance_token_count_avg": average(_to_float(row.get("affordance_token_count_avg")) for row in rows),
        "affordance_type_counts": dict(_merge_count_dicts(rows, "affordance_type_counts")),
        "scene_graph_node_count_avg": average(_to_float(row.get("scene_graph_node_count_avg")) for row in rows),
        "scene_graph_edge_count_avg": average(_to_float(row.get("scene_graph_edge_count_avg")) for row in rows),
        "scene_graph_trigger_edge_count": sum(_to_float(row.get("scene_graph_trigger_edge_count")) or 0.0 for row in rows),
        "scene_graph_trigger_edge_count_avg": average(_to_float(row.get("scene_graph_trigger_edge_count")) for row in rows),
        "rast_trigger_risk_token_count": sum(_to_float(row.get("rast_trigger_risk_token_count")) or 0.0 for row in rows),
        "rast_trigger_risk_token_count_avg": average(_to_float(row.get("rast_trigger_risk_token_count")) for row in rows),
        "event_aware_trigger_event_count": sum(_to_float(row.get("event_aware_trigger_event_count")) or 0.0 for row in rows),
        "event_aware_trigger_event_count_avg": average(_to_float(row.get("event_aware_trigger_event_count")) for row in rows),
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
        "uncertainty_aware_rast_action_counts": dict(
            _merge_count_dicts(rows, "uncertainty_aware_rast_action_counts")
        ),
        "uncertainty_aware_rast_reason_code_counts": dict(
            _merge_count_dicts(rows, "uncertainty_aware_rast_reason_code_counts")
        ),
        "affordance_aware_rast_action_counts": dict(
            _merge_count_dicts(rows, "affordance_aware_rast_action_counts")
        ),
        "affordance_aware_rast_reason_code_counts": dict(
            _merge_count_dicts(rows, "affordance_aware_rast_reason_code_counts")
        ),
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
        "uncertainty_triggered_action_count_total": sum(
            _to_float(row.get("uncertainty_triggered_action_count")) or 0.0 for row in rows
        ),
        "uncertainty_triggered_action_count_avg": average(
            _to_float(row.get("uncertainty_triggered_action_count")) for row in rows
        ),
        "affordance_triggered_action_count_total": sum(
            _to_float(row.get("affordance_triggered_action_count")) or 0.0 for row in rows
        ),
        "affordance_triggered_action_count_avg": average(
            _to_float(row.get("affordance_triggered_action_count")) for row in rows
        ),
        "event_aware_decision_trace_coverage": average(
            _to_float(row.get("event_aware_decision_trace_coverage")) for row in rows
        ),
        "uncertainty_aware_decision_trace_coverage": average(
            _to_float(row.get("uncertainty_aware_decision_trace_coverage")) for row in rows
        ),
        "affordance_aware_decision_trace_coverage": average(
            _to_float(row.get("affordance_aware_decision_trace_coverage")) for row in rows
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


def _suite_execution_metadata(suite_metadata_path: str | Path | None) -> list[str]:
    lines = ["## Suite Execution Metadata", ""]
    if suite_metadata_path is None:
        lines.extend(
            [
                "- No suite_metadata.json was provided.",
                "- Report generation remains backward compatible with older aggregate outputs.",
                "",
            ]
        )
        return lines

    metadata_path = Path(suite_metadata_path)
    if not metadata_path.exists():
        lines.extend(
            [
                f"- suite_metadata.json was not found at `{metadata_path}`.",
                "- Report generation continues without sampled execution metadata.",
                "",
            ]
        )
        return lines

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    planned = int(metadata.get("planned_runs_total") or 0)
    executed = int(metadata.get("executed_runs") or 0)
    sample_size = metadata.get("sample_size")
    limit = metadata.get("limit")
    sampled = sample_size not in (None, "", 0) or (planned > 0 and executed > 0 and executed < planned)
    lines.extend(
        [
            f"- suite_metadata: `{metadata_path}`",
            f"- suite_run_id: `{metadata.get('suite_run_id', '')}`",
            f"- config_path: `{metadata.get('config_path', '')}`",
            f"- config_name: `{metadata.get('config_name', '')}`",
            f"- planned_runs_total: {planned}",
            f"- executed_runs: {executed}",
            f"- failed_runs: {metadata.get('failed_runs', 0)}",
            f"- sampling_mode: `{metadata.get('sampling_mode', '')}`",
            f"- sample_size: `{sample_size}`",
            f"- sample_seed: `{metadata.get('sample_seed', '')}`",
            f"- limit: `{limit}`",
            f"- allow_large_run: `{metadata.get('allow_large_run', False)}`",
            f"- replay_export_enabled: `{metadata.get('replay_export_enabled', False)}`",
            f"- replay_index_path: `{metadata.get('replay_index_path', '')}`",
        ]
    )
    if sampled:
        lines.append(
            "- This report summarizes a sampled subset of the extended grid, not the full extended grid."
        )
    lines.append("")
    return lines


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
        "- Scene Graph: 같은 ObservationSnapshot에서 agent/object/goal node와 relation edge를 구성하는 graph baseline입니다.",
        "- RAST: EntityToken, RiskToken, RelationToken, EventToken, UncertaintyToken, EvidenceToken, AffordanceToken logging을 포함한 planner-facing token contract 경로입니다.",
        "- Event-aware RAST: 기존 RAST planner와 분리된 실험용 planner이며 EventToken을 decision reason에 반영합니다.",
        "- Uncertainty-aware RAST: 기존 RAST planner와 분리된 실험용 planner이며 UncertaintyToken을 decision reason에 반영합니다.",
        "- Affordance-aware RAST: 기존 RAST planner를 대체하지 않는 별도 experimental planner이며, navigation AffordanceToken을 decision reason으로 사용할 수 있습니다.",
        "- 기존 RAST planner는 EventToken으로 action을 바꾸지 않으며, Event-aware RAST planner에서만 실험적으로 EventToken reason을 사용합니다.",
        "- 기존 RAST planner는 UncertaintyToken으로 action을 바꾸지 않으며, Uncertainty-aware RAST planner에서만 실험적으로 uncertainty reason을 사용합니다.",
        "- 기존 RAST planner는 AffordanceToken으로 action을 바꾸지 않으며, Affordance-aware RAST planner에서만 navigation affordance reason을 사용합니다.",
        "- Affordance-aware RAST의 action 변화는 성능 개선이나 real robot feasibility를 의미하지 않습니다.",
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
        "- RAST vs Uncertainty-aware RAST disagreement",
        "- RAST vs Affordance-aware RAST disagreement",
        "- RAST vs Scene Graph disagreement / same-action-different-reason",
        "- token_count_avg / object_count_avg / flat_feature_row_count_avg",
        "- event_token_count_total / event_token_count_avg / event_type_counts",
        "- uncertainty_token_count_total / uncertainty_token_count_avg / uncertainty_type_counts / high_uncertainty_count",
        "- evidence_token_count_total / evidence_token_count_avg / evidence_type_counts / decision_evidence_coverage",
        "- affordance_token_count_total / affordance_token_count_avg / affordance_type_counts",
        "- rast_vs_affordance_aware_disagreement_count / affordance_triggered_action_count",
        "- affordance_aware_decision_trace_coverage",
        "- update_mode / changed_object_count_avg / affected_token_count_avg",
        "- full_recompute_latency_avg_ms / incremental_update_latency_avg_ms / incremental_update_benefit_avg",
        "- rast_reason_code_counts / object_list_reason_code_counts / flat_feature_reason_code_counts",
        "- event_aware_rast_reason_code_counts / event_triggered_action_count",
        "- uncertainty_aware_rast_reason_code_counts / uncertainty_triggered_action_count",
        "- affordance_aware_rast_reason_code_counts / affordance_triggered_action_count",
        "- event_policy_variant / event_policy_variant_action_counts / event_policy_variant_reason_code_counts",
        "- risk_threshold / relation thresholds / near_miss_threshold",
        "- position_noise_std / distance_noise_std / visibility_flip_prob",
        "- rast_trigger_token_count_total / decision_trace_coverage",
        "- scene_graph_trigger_edge_count / rast_trigger_risk_token_count / event_aware_trigger_event_count",
        "- event_aware_decision_trace_coverage",
        "- uncertainty_aware_decision_trace_coverage",
        "- latency_avg_ms / latency_p50_ms / latency_p95_ms",
        "- token_generation_latency_avg_ms / planning_latency_avg_ms / total_latency_avg_ms",
        "",
    ]


def _before_after_context() -> list[str]:
    return [
        "## Before/After Context",
        "",
        "- 현재 report는 EventToken, UncertaintyToken, EvidenceToken, AffordanceToken이 step log, episode summary, aggregate result에 포함된 이후의 결과입니다.",
        "- Event-aware, Uncertainty-aware, Affordance-aware planner는 각각 별도 experimental planner이며 기존 RAST planner를 대체하지 않습니다.",
        "- action 변화는 성능 개선 주장이 아니라 token-to-decision 연결 가능성과 decision boundary 차이를 관찰하기 위한 것입니다.",
        "- TokenMemory는 semantic diff와 incremental latency protocol에 사용됩니다. incremental update optimization is experimental.",
        "- UncertaintyToken은 WindowsMetadataSim의 synthetic metadata uncertainty를 기록하며 실제 perception uncertainty calibration이 아닙니다.",
        "- EvidenceToken은 metadata pointer 기반 traceability이며 raw image crop이나 real sensor evidence가 아닙니다.",
        "- AffordanceToken은 navigation affordance only이며 real robot action feasibility 검증을 의미하지 않습니다.",
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


def _uncertainty_token_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    uncertainty_counts = overall["uncertainty_type_counts"]
    total_uncertainty = int(overall["uncertainty_token_count_total"])
    lines = [
        "## UncertaintyToken Summary",
        "",
        f"- UncertaintyToken included in this report: {'yes' if total_uncertainty > 0 else 'no'}",
        f"- Total UncertaintyToken count across successful runs: {total_uncertainty}",
        f"- Average UncertaintyToken count per episode: {_fmt(overall['uncertainty_token_count_total_avg'])}",
        f"- Average UncertaintyToken count per step: {_fmt(overall['uncertainty_token_count_avg'])}",
        f"- Total high uncertainty count: {int(overall['high_uncertainty_count_total'])}",
        f"- Average high uncertainty count per step: {_fmt(overall['high_uncertainty_count_avg'])}",
        f"- Uncertainty type distribution: `{_json_compact(uncertainty_counts)}`",
        "- UncertaintyToken은 WindowsMetadataSim의 synthetic metadata uncertainty 기반이며 실제 perception uncertainty calibration이 아닙니다.",
        "- sensor disagreement는 simulated field이며 실제 multi-sensor fusion 결과가 아닙니다.",
        "",
        "| Uncertainty Type | Occurred | Count |",
        "|---|---:|---:|",
    ]
    for uncertainty_type in (
        "classification_uncertainty",
        "position_uncertainty",
        "partial_occlusion",
        "low_sensor_agreement",
        "unknown_object",
    ):
        count = int(uncertainty_counts.get(uncertainty_type, 0))
        lines.append(f"| `{uncertainty_type}` | {'yes' if count > 0 else 'no'} | {count} |")
    lines.extend(
        [
            "",
            "| Scenario | Runs | Avg Uncertainty Tokens / Episode | Avg High Uncertainty / Episode | Uncertainty Type Counts |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['uncertainty_token_count_total_avg'])} | "
            f"{_fmt(item['high_uncertainty_count_total_avg'])} | "
            f"`{_json_compact(item['uncertainty_type_counts'])}` |"
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


def _scene_graph_rast_differentiation_summary(stats: dict[str, Any]) -> list[str]:
    """Scene Graph와 RAST의 action 차이와 decision basis 차이를 함께 요약합니다."""

    overall = stats["overall"]
    lines = [
        "## Scene Graph vs RAST Differentiation Summary",
        "",
        "- 이 섹션은 Scene Graph baseline과 RAST의 우수/열위를 주장하지 않고 representation 차이를 관찰합니다.",
        "- action disagreement가 0이어도 같은 action을 서로 다른 reason_code로 선택할 수 있으므로 decision basis metric을 별도로 봅니다.",
        f"- Average RAST vs Scene Graph action disagreement: {_fmt(overall['rast_vs_scene_graph_disagreement_avg'])}",
        (
            "- Average same-action-different-reason count: "
            f"{_fmt(overall['rast_vs_scene_graph_same_action_different_reason_avg'])}"
        ),
        (
            "- Average same-action-different-reason rate: "
            f"{_fmt(overall['rast_vs_scene_graph_same_action_different_reason_rate'])}"
        ),
        f"- Total Scene Graph trigger edge count: {int(overall['scene_graph_trigger_edge_count'])}",
        f"- Total RAST trigger RiskToken count: {int(overall['rast_trigger_risk_token_count'])}",
        f"- Total Event-aware trigger EventToken count: {int(overall['event_aware_trigger_event_count'])}",
        "- relation edge 기반 decision과 Risk/EventToken 기반 decision은 같은 ObservationSnapshot에서 출발하지만 서로 다른 contract를 사용합니다.",
        "- risk_threshold와 relation threshold는 분리되어 있어 relation edge와 RiskToken boundary를 독립적으로 관찰할 수 있습니다.",
        "- 이 결과는 RAST 우수성 증거가 아니라 controlled metadata suite에서 decision basis 차이가 기록됨을 보여주는 자료입니다.",
        "",
        (
            "| Scenario | Runs | RAST vs Scene Graph Disagreement | Same Action Different Reason | "
            "Same Action Different Reason Rate | Relation Tokens Avg | Graph Edges Avg | RAST Risk Triggers Avg | Event Triggers Avg |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['rast_vs_scene_graph_disagreement_avg'])} | "
            f"{_fmt(item['rast_vs_scene_graph_same_action_different_reason_avg'])} | "
            f"{_fmt(item['rast_vs_scene_graph_same_action_different_reason_rate'])} | "
            f"{_fmt(item['relation_token_count_avg'])} | "
            f"{_fmt(item['scene_graph_edge_count_avg'])} | "
            f"{_fmt(item['rast_trigger_risk_token_count_avg'])} | "
            f"{_fmt(item['event_aware_trigger_event_count_avg'])} |"
        )
    lines.extend(
        [
            "",
            "- `relation_near_but_low_risk`, `blocking_relation_without_high_risk`, `risk_without_graph_blocking`, "
            "`event_changes_risk_but_graph_static`는 representation 차이를 관찰하기 위한 controlled scenario입니다.",
            "- Scene Graph는 simplified relation edge baseline이고, RelationToken은 simple geometry rule 기반입니다.",
            "",
        ]
    )
    return lines


def _evidence_token_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    total = int(overall["evidence_token_count_total"])
    included = total > 0
    lines = [
        "## EvidenceToken Summary",
        "",
        f"- EvidenceToken included in this report: {'yes' if included else 'no'}",
        f"- Total EvidenceToken count: {total}",
        f"- Average EvidenceToken count per episode: {_fmt(overall['evidence_token_count_avg'])}",
        f"- Evidence type distribution: `{_json_compact(overall['evidence_type_counts'])}`",
        f"- Risk evidence count: {int(overall['risk_evidence_count_total'])}",
        f"- Uncertainty evidence count: {int(overall['uncertainty_evidence_count_total'])}",
        f"- Event evidence count: {int(overall['event_evidence_count_total'])}",
        f"- Decision evidence count: {int(overall['decision_evidence_count_total'])}",
        f"- Decision evidence coverage: {_fmt(overall['decision_evidence_coverage'])}",
        "- EvidenceToken currently stores metadata pointers, bbox-like fields, token ids, and decision trace references.",
        "- It does not store raw image crops, RGB frames, or real sensor evidence in WindowsMetadataSim.",
        "- EvidenceToken presence supports traceability infrastructure only; it is not evidence of performance improvement.",
        "",
        "| Scenario | Runs | Avg EvidenceToken | Evidence Types | Decision Evidence Coverage |",
        "|---|---:|---:|---|---:|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['evidence_token_count_avg'])} | "
            f"`{_json_compact(item['evidence_type_counts'])}` | "
            f"{_fmt(item['decision_evidence_coverage'])} |"
        )
    lines.append("")
    return lines


def _affordance_token_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    total = int(overall["affordance_token_count_total"])
    counts = overall["affordance_type_counts"]
    lines = [
        "## AffordanceToken Summary",
        "",
        f"- AffordanceToken included in this report: {'yes' if total > 0 else 'no'}",
        f"- Total AffordanceToken count: {total}",
        f"- Average AffordanceToken count per episode: {_fmt(overall['affordance_token_count_total_avg'])}",
        f"- Average AffordanceToken count per step: {_fmt(overall['affordance_token_count_avg'])}",
        f"- Affordance type distribution: `{_json_compact(counts)}`",
        "- AffordanceToken is limited to navigation affordance in MVP-0.",
        "- Manipulation affordance such as graspable, movable, openable, container, and fragile is not included.",
        "- These affordances are simple geometry/rule-based metadata affordances, not verified real robot action feasibility.",
        "",
        "| Affordance Type | Occurred | Count |",
        "|---|---:|---:|",
    ]
    for affordance_type in (
        "passable",
        "blocking",
        "narrow_passage",
        "target_reachable",
        "inspect_required",
        "avoid_required",
    ):
        count = int(counts.get(affordance_type, 0))
        lines.append(f"| `{affordance_type}` | {'yes' if count > 0 else 'no'} | {count} |")
    lines.extend(
        [
            "",
            "| Scenario | Runs | Avg Affordance Tokens / Episode | Affordance Type Counts |",
            "|---|---:|---:|---|",
        ]
    )
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['affordance_token_count_total_avg'])} | "
            f"`{_json_compact(item['affordance_type_counts'])}` |"
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


def _uncertainty_aware_planner_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    reason_counts = overall["uncertainty_aware_rast_reason_code_counts"]
    uncertainty_triggered_total = int(overall["uncertainty_triggered_action_count_total"])
    included = "uncertainty_aware_rast" in stats["apply_policies"] or bool(reason_counts)
    differing_scenarios = [
        scenario
        for scenario, item in stats["scenario_stats"].items()
        if item["rast_vs_uncertainty_aware_disagreement_avg"] > 0
    ]
    lines = [
        "## Uncertainty-aware Planner Summary",
        "",
        f"- Uncertainty-aware RAST planner included in this report: {'yes' if included else 'no'}",
        f"- Average RAST vs Uncertainty-aware RAST disagreement: {_fmt(overall['rast_vs_uncertainty_aware_disagreement_avg'])}",
        f"- Total uncertainty-triggered actions: {uncertainty_triggered_total}",
        f"- Average uncertainty-triggered actions per episode: {_fmt(overall['uncertainty_triggered_action_count_avg'])}",
        f"- Average Uncertainty-aware decision trace coverage: {_fmt(overall['uncertainty_aware_decision_trace_coverage'])}",
        f"- Uncertainty-aware reason code distribution: `{_json_compact(reason_counts)}`",
        f"- Scenarios with observed RAST vs Uncertainty-aware disagreement: `{', '.join(differing_scenarios) if differing_scenarios else 'none'}`",
        "- Uncertainty-aware planner는 deterministic rule-based experimental policy이며 성능 개선을 단정하는 근거가 아닙니다.",
        "- uncertainty가 action/reason을 바꾸더라도 실제 perception uncertainty calibration이나 safety improvement를 의미하지 않습니다.",
        "",
        "| Scenario | Runs | Avg RAST vs Uncertainty-aware Disagreement | Avg Uncertainty-triggered Actions | Reason Codes |",
        "|---|---:|---:|---:|---|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['rast_vs_uncertainty_aware_disagreement_avg'])} | "
            f"{_fmt(item['uncertainty_triggered_action_count_avg'])} | "
            f"`{_json_compact(item['uncertainty_aware_rast_reason_code_counts'])}` |"
        )
    lines.append("")
    return lines


def _affordance_aware_planner_summary(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    reason_counts = overall["affordance_aware_rast_reason_code_counts"]
    triggered_total = int(overall["affordance_triggered_action_count_total"])
    included = "affordance_aware_rast" in stats["apply_policies"] or bool(reason_counts)
    differing_scenarios = [
        scenario
        for scenario, item in stats["scenario_stats"].items()
        if item["rast_vs_affordance_aware_disagreement_avg"] > 0
    ]
    lines = [
        "## Affordance-aware Planner Summary",
        "",
        f"- Affordance-aware RAST planner included in this report: {'yes' if included else 'no'}",
        f"- Average RAST vs Affordance-aware RAST disagreement: {_fmt(overall['rast_vs_affordance_aware_disagreement_avg'])}",
        f"- Total affordance-triggered actions: {triggered_total}",
        f"- Average affordance-triggered actions per episode: {_fmt(overall['affordance_triggered_action_count_avg'])}",
        f"- Average Affordance-aware decision trace coverage: {_fmt(overall['affordance_aware_decision_trace_coverage'])}",
        f"- Affordance-aware reason code distribution: `{_json_compact(reason_counts)}`",
        f"- Scenarios with observed RAST vs Affordance-aware disagreement: `{', '.join(differing_scenarios) if differing_scenarios else 'none'}`",
        "- Affordance-aware planner is a deterministic rule-based experimental policy.",
        "- Affordance-triggered action changes do not imply verified performance improvement or real robot feasibility.",
        "",
        "| Scenario | Runs | Avg RAST vs Affordance-aware Disagreement | Avg Affordance-triggered Actions | Reason Codes |",
        "|---|---:|---:|---:|---|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | "
            f"{_fmt(item['rast_vs_affordance_aware_disagreement_avg'])} | "
            f"{_fmt(item['affordance_triggered_action_count_avg'])} | "
            f"`{_json_compact(item['affordance_aware_rast_reason_code_counts'])}` |"
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


def _replay_trace_summary() -> list[str]:
    return [
        "## Replay Trace Summary",
        "",
        "- Decision replay export is available through `experiments/export_decision_replay.py`.",
        "- Replay cases include collision, near-miss, planner disagreement, RAST vs Scene Graph disagreement, RAST vs Uncertainty-aware disagreement, RAST vs Affordance-aware disagreement, event-triggered action, uncertainty-triggered action, affordance-triggered action, high RiskToken, and high UncertaintyToken steps.",
        "- The exported replay contains selected actions, planner decisions, reason codes, trigger tokens, EvidenceToken references, object metadata summary, and risk/uncertainty/event/affordance summaries.",
        "- This is metadata/action trace reconstruction, not visual replay and not learned interpretability.",
        "- Future versions can attach real image crop, bbox, sensor frame pointer, or perception-bound evidence references.",
        "",
    ]


def _replay_artifact_summary(replay_index_path: str | Path | None) -> list[str]:
    lines = [
        "## Replay Artifact Summary",
        "",
    ]
    if replay_index_path is None:
        lines.extend(
            [
                "- No replay artifact index was provided or found.",
                "- Run `experiments/run_windows_eval_suite.py --export-replays` and pass `--replay-index` to include concrete replay artifact links.",
                "- Replay artifacts remain metadata/action/evidence trace reconstruction, not visual replay.",
                "",
            ]
        )
        return lines

    index_path = Path(replay_index_path)
    if not index_path.exists():
        lines.extend(
            [
                f"- No replay artifact index was provided or found at `{index_path}`.",
                "- Report generation continues without replay artifact rows.",
                "- Replay artifacts remain metadata/action/evidence trace reconstruction, not visual replay.",
                "",
            ]
        )
        return lines

    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        lines.extend(
            [
                f"- Replay artifact index could not be parsed: `{index_path}`.",
                "- Report generation continues without replay artifact rows.",
                "",
            ]
        )
        return lines

    entries = [dict(item) for item in index.get("entries", []) if isinstance(item, dict)]
    case_counts = Counter(str(item.get("case_type", "")) for item in entries if item.get("case_type"))
    lines.extend(
        [
            f"- replay artifact export enabled: {'yes' if entries else 'no'}",
            f"- replay_index.json: `{index_path}`",
            f"- generated replay count: {int(index.get('replay_count', len(entries)) or 0)}",
            f"- case_type distribution: `{_json_compact(dict(case_counts))}`",
            "- Replay artifacts are metadata/action/evidence trace reconstruction, not visual replay.",
            "",
            "| Case Type | Scenario | Step | Markdown Path | Summary |",
            "|---|---|---:|---|---|",
        ]
    )
    if not entries:
        lines.append("| n/a | n/a | 0 | n/a | No replay entries were generated. |")
    for item in entries[:10]:
        lines.append(
            f"| `{item.get('case_type', '')}` | `{item.get('scenario', '')}` | "
            f"{item.get('step', '')} | `{item.get('markdown_path', '')}` | {item.get('summary', '')} |"
        )
    lines.append("")
    return lines


def _representative_decision_trace_summary(stats: dict[str, Any]) -> list[str]:
    candidates: list[dict[str, Any]] = []
    disagreement_specs = (
        (
            "RAST vs Affordance-aware",
            "rast_vs_affordance_aware_disagreement_avg",
            "affordance_aware_rast_reason_code_counts",
            "AffordanceToken 기반 action possibility가 기존 RAST risk boundary와 다르게 작동한 case입니다.",
        ),
        (
            "RAST vs Scene Graph",
            "rast_vs_scene_graph_disagreement_avg",
            "scene_graph_reason_code_counts",
            "Relation edge 기반 decision과 Risk/Token contract 기반 decision이 갈라진 case입니다.",
        ),
        (
            "RAST vs Uncertainty-aware",
            "rast_vs_uncertainty_aware_disagreement_avg",
            "uncertainty_aware_rast_reason_code_counts",
            "synthetic uncertainty token이 action reason boundary에 연결된 case입니다.",
        ),
        (
            "RAST vs Object List",
            "rast_vs_object_list_disagreement_avg",
            "object_list_reason_code_counts",
            "object distance 중심 baseline과 RAST token contract가 다른 action을 낸 case입니다.",
        ),
    )
    for scenario, item in stats["scenario_stats"].items():
        for label, metric_key, reason_key, interpretation in disagreement_specs:
            value = float(item.get(metric_key, 0.0) or 0.0)
            if value <= 0:
                continue
            candidates.append(
                {
                    "scenario": scenario,
                    "label": label,
                    "value": value,
                    "reason_counts": item.get(reason_key, {}),
                    "interpretation": interpretation,
                }
            )

    candidates.sort(key=lambda item: item["value"], reverse=True)
    lines = [
        "## Representative Decision Trace Summary",
        "",
        "- 이 섹션은 scenario별 disagreement가 큰 decision trace 후보를 요약합니다.",
        "- 성능 우수성 주장이 아니라 representation별 decision boundary가 갈라지는 case를 찾기 위한 요약입니다.",
        "",
        "| Scenario | Disagreement Type | Avg Disagreement | Relevant Reason Codes | Interpretation |",
        "|---|---|---:|---|---|",
    ]
    if not candidates:
        lines.append("| n/a | n/a | 0.000 | `{}` | No non-zero disagreement cases were observed in this aggregate. |")
    for item in candidates[:5]:
        lines.append(
            f"| `{item['scenario']}` | {item['label']} | {_fmt(item['value'])} | "
            f"`{_json_compact(item['reason_counts'])}` | {item['interpretation']} |"
        )
    lines.append("")
    return lines


def _sampling_coverage_and_stability_artifacts(
    sampling_coverage_path: str | Path | None,
    seed_stability_path: str | Path | None,
) -> list[str]:
    lines = [
        "## Sampling Coverage and Stability Artifacts",
        "",
        "- 이 섹션은 sampled extended result를 해석하기 전에 coverage와 seed sensitivity를 점검하기 위한 artifact 연결입니다.",
    ]
    if sampling_coverage_path is None and seed_stability_path is None:
        lines.extend(
            [
                "- No sampling coverage or seed stability artifact was provided.",
                "- Generate them with `experiments/analyze_sampling_coverage.py` and `experiments/compare_seed_sweep.py` when interpreting sampled extended results.",
                "",
            ]
        )
        return lines
    lines.extend(
        [
            f"- sampling coverage report: `{sampling_coverage_path or 'not provided'}`",
            f"- seed stability report: `{seed_stability_path or 'not provided'}`",
            "- 이 artifact들은 sampled extended result의 coverage/stability 검토용이며, 성능 우수성 주장을 지원하지 않습니다.",
            "- sampled result는 full extended grid exhaustive result가 아니므로 seed와 sample size에 의존할 수 있습니다.",
            "",
        ]
    )
    return lines


def _sample_size_convergence_artifact(sample_size_convergence_path: str | Path | None) -> list[str]:
    lines = [
        "## Sample-size Convergence Artifact",
        "",
        "- 이 섹션은 sampled extended evaluation에서 sample-size 변화에 따른 metric/coverage 안정성을 점검하기 위한 artifact 연결입니다.",
    ]
    if sample_size_convergence_path is None:
        lines.extend(
            [
                "- No sample-size convergence artifact was provided.",
                "- Generate it with `experiments/run_sample_size_sweep.py` and `experiments/analyze_sample_size_convergence.py` when interpreting sampled extended results.",
                "",
            ]
        )
        return lines
    lines.extend(
        [
            f"- sample-size convergence report: `{sample_size_convergence_path}`",
            "- 이 artifact는 sample-size sensitivity와 sampling quality score를 보기 위한 보조 자료입니다.",
            "- full extended grid exhaustive evaluation이 아니며, sampling quality score는 RAST 성능 점수가 아닙니다.",
            "",
        ]
    )
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
        "- UncertaintyToken이 synthetic classification/position/occlusion/sensor agreement uncertainty를 기록할 수 있음을 보여줍니다.",
        "- 별도 Uncertainty-aware RAST planner가 UncertaintyToken을 decision reason으로 사용할 수 있음을 보여줍니다.",
        "- EvidenceToken이 risk/uncertainty/event/planner decision evidence를 metadata pointer로 연결할 수 있음을 보여줍니다.",
        "- decision replay markdown/json을 생성해 metadata/action/evidence trace를 재구성할 수 있음을 보여줍니다.",
        "- AffordanceToken이 navigation affordance를 기록하고, 별도 Affordance-aware RAST planner가 이를 decision reason으로 사용할 수 있음을 보여줍니다.",
        "- 세 planner의 action 선택 사유를 PlannerDecision trace로 기록하고 집계할 수 있음을 보여줍니다.",
        "- Scene Graph와 RAST가 같은 action을 선택해도 서로 다른 decision basis를 가질 수 있음을 기록할 수 있습니다.",
        "",
    ]


def _does_not_support() -> list[str]:
    return [
        "## What This Result Does Not Support",
        "",
        "- This result does not support real-world performance claims.",
        "- RAST가 Object List나 Flat Feature보다 일반적으로 우수하다는 결론을 지원하지 않습니다.",
        "- Event-aware planner나 EventToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.",
        "- Uncertainty-aware planner나 UncertaintyToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.",
        "- Affordance-aware planner나 AffordanceToken이 task performance, safety, real robot action feasibility를 개선했다는 결론을 지원하지 않습니다.",
        "- EvidenceToken이 real sensor evidence, raw image crop, RGB/depth frame, visual evidence를 제공한다는 결론을 지원하지 않습니다.",
        "- Decision trace는 rule-based planner 로그이며 learned model explanation 품질을 검증하지 않습니다.",
        "- 실제 perception uncertainty calibration이나 multi-sensor fusion 품질을 검증하지 않습니다.",
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
        "- UncertaintyToken은 synthetic metadata uncertainty 기반이며, 실제 perception uncertainty calibration이 아닙니다.",
        "- sensor disagreement는 simulated field이며 실제 multi-sensor fusion 결과가 아닙니다.",
        "- EvidenceToken은 metadata pointer 기반입니다.",
        "- raw image crop, RGB/depth frame, real sensor evidence는 저장하지 않습니다.",
        "- decision replay는 visual replay가 아니라 metadata/action trace reconstruction입니다.",
        "- AffordanceToken은 navigation affordance only입니다.",
        "- manipulation affordance는 구현하지 않았습니다.",
        "- AffordanceToken은 simple geometry/rule 기반입니다.",
        "- 실제 robot action feasibility를 검증하지 않습니다.",
        "- Event-aware RAST planner는 deterministic rule-based policy이며 learned policy나 learned explanation이 아닙니다.",
        "- Uncertainty-aware RAST planner는 deterministic rule-based experimental policy이며 learned policy가 아닙니다.",
        "- Affordance-aware RAST planner는 deterministic rule-based experimental policy입니다.",
        "- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용되지만, incremental update optimization is experimental입니다.",
        "- Batch 9의 incremental update는 measurement protocol 단계이며, 일부 token 계산은 correctness를 위해 여전히 재계산됩니다.",
        "- full_recompute와 incremental 후보를 같은 step에서 모두 측정하므로 report의 selected token_generation latency와 실제 Python wall-clock은 다를 수 있습니다.",
        "- EventToken은 별도 Event-aware planner에만 연결되므로, success/near-miss/disagreement 변화는 일반 RAST 효과로 해석하면 안 됩니다.",
        "- PlannerDecision은 현재 deterministic rule-based policy의 내부 규칙을 기록한 것이며, learned model interpretability는 아닙니다.",
        "- 동일 action이라도 planner별 reason_code와 trigger feature가 다를 수 있으므로 action count만으로 의사결정 근거를 해석하면 안 됩니다.",
        "- RelationToken과 Scene Graph baseline은 MVP용 geometry-rule 구현이며, UncertaintyToken 역시 synthetic metadata rule 기반입니다.",
        "- Scene Graph vs RAST differentiation scenario는 controlled metadata case이며, 일반적인 representation 우수성 결론을 지원하지 않습니다.",
        "- Flat Feature와 RAST가 동일한 scalar risk rule에 강하게 묶여 있어 token contract 효과는 아직 제한적으로만 관찰됩니다.",
        "",
    ]


def _next_steps() -> list[str]:
    return [
        "## Next Steps",
        "",
        "P0 next:",
        "- extended threshold/noise sweep을 넓혀 RAST/Object List/Flat Feature/Scene Graph/Event-aware/Uncertainty-aware/Affordance-aware disagreement boundary를 더 명확히 봅니다.",
        "- replay artifact와 report 연결을 강화해 decision trace, evidence pointer, scenario context를 함께 추적합니다.",
        "- result/technical report polish를 통해 현재 MVP-0의 관찰 결과와 한계를 더 읽기 쉽게 정리합니다.",
        "- failure case/action trace analysis를 강화해 planner별 reason_code와 trigger token 차이를 더 세밀하게 분석합니다.",
        "",
        "P1:",
        "- Webots adapter spike로 Windows native에서 실제 3D simulator adapter 가능성을 검토합니다.",
        "- perception-bound adapter를 추가해 simulator metadata가 아니라 detector/segmentation/depth output에서 token을 생성하는 경로를 검토합니다.",
        "- real simulator metadata adapter로 AI2-THOR, Webots, CoppeliaSim metadata와 ObservationSnapshot adapter 연결을 검토합니다.",
        "- manipulation affordance extension으로 graspable, openable, movable 등 navigation 외 affordance를 별도 후속 범위로 둡니다.",
        "",
        "P2:",
        "- learned extractor와 rule-based tokenizer를 비교합니다.",
        "- VLA/LLM planner integration을 통해 structured token JSON 또는 text rendering 전달 방식을 실험합니다.",
        "- real robot bridge로 실제 robot sensor stream과 RAST interface 연결 가능성을 검토합니다.",
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

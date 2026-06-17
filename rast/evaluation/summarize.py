"""Aggregate result를 간단한 scenario/policy summary로 요약합니다."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def summarize_aggregate_results(
    rows: list[dict[str, Any]],
    *,
    output_dir: str | Path,
) -> dict[str, list[dict[str, Any]]]:
    """aggregate rows를 scenario별, apply_policy별 summary로 저장합니다."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = {
        "by_scenario": summarize_by_key(rows, "scenario"),
        "by_apply_policy": summarize_by_key(rows, "apply_policy"),
        "by_update_mode": summarize_by_key(rows, "update_mode"),
        "by_event_policy_variant": summarize_by_key(rows, "event_policy_variant"),
        "by_scenario_event_policy_variant": summarize_by_keys(rows, ("scenario", "event_policy_variant")),
        "by_scenario_risk_threshold": summarize_by_keys(rows, ("scenario", "risk_threshold")),
        "by_scenario_noise_level": summarize_by_keys(
            rows,
            ("scenario", "position_noise_std", "distance_noise_std", "visibility_flip_prob"),
        ),
    }
    (output / "aggregate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_summary_csv(summary, output / "aggregate_summary.csv")
    return summary


def summarize_by_key(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """지정 key 기준으로 성공률, near-miss, disagreement, latency 평균을 계산합니다."""

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("status", "success") != "success":
            continue
        groups[str(row.get(key, ""))].append(row)

    summaries: list[dict[str, Any]] = []
    for value, items in sorted(groups.items()):
        summaries.append(
            {
                key: value,
                "run_count": len(items),
                "success_rate": average(_bool_to_float(item.get("success")) for item in items),
                "near_miss_count_avg": average(_to_float(item.get("near_miss_count")) for item in items),
                "rast_vs_object_list_disagreement_avg": average(
                    _to_float(item.get("rast_vs_object_list_disagreement_count")) for item in items
                ),
                "rast_vs_flat_feature_disagreement_avg": average(
                    _to_float(item.get("rast_vs_flat_feature_disagreement_count")) for item in items
                ),
                "object_list_vs_flat_feature_disagreement_avg": average(
                    _to_float(item.get("object_list_vs_flat_feature_disagreement_count")) for item in items
                ),
                "rast_vs_event_aware_disagreement_avg": average(
                    _to_float(item.get("rast_vs_event_aware_disagreement_count")) for item in items
                ),
                "rast_vs_uncertainty_aware_disagreement_avg": average(
                    _to_float(item.get("rast_vs_uncertainty_aware_disagreement_count")) for item in items
                ),
                "rast_vs_affordance_aware_disagreement_avg": average(
                    _to_float(item.get("rast_vs_affordance_aware_disagreement_count")) for item in items
                ),
                "rast_vs_scene_graph_disagreement_avg": average(
                    _to_float(item.get("rast_vs_scene_graph_disagreement_count")) for item in items
                ),
                "scene_graph_vs_flat_feature_disagreement_avg": average(
                    _to_float(item.get("scene_graph_vs_flat_feature_disagreement_count")) for item in items
                ),
                "rast_vs_scene_graph_same_action_different_reason_avg": average(
                    _to_float(item.get("rast_vs_scene_graph_same_action_different_reason_count")) for item in items
                ),
                "rast_vs_scene_graph_same_action_different_reason_rate_avg": average(
                    _to_float(item.get("rast_vs_scene_graph_same_action_different_reason_rate")) for item in items
                ),
                "scene_graph_trigger_edge_count_avg": average(
                    _to_float(item.get("scene_graph_trigger_edge_count")) for item in items
                ),
                "rast_trigger_risk_token_count_avg": average(
                    _to_float(item.get("rast_trigger_risk_token_count")) for item in items
                ),
                "event_aware_trigger_event_count_avg": average(
                    _to_float(item.get("event_aware_trigger_event_count")) for item in items
                ),
                "event_triggered_action_count_avg": average(
                    _to_float(item.get("event_triggered_action_count")) for item in items
                ),
                "uncertainty_triggered_action_count_avg": average(
                    _to_float(item.get("uncertainty_triggered_action_count")) for item in items
                ),
                "affordance_triggered_action_count_avg": average(
                    _to_float(item.get("affordance_triggered_action_count")) for item in items
                ),
                "relation_token_count_total_avg": average(
                    _to_float(item.get("relation_token_count_total")) for item in items
                ),
                "relation_token_count_avg": average(_to_float(item.get("relation_token_count_avg")) for item in items),
                "relation_type_counts": dict(_merge_count_dicts(items, "relation_type_counts")),
                "uncertainty_token_count_total_avg": average(
                    _to_float(item.get("uncertainty_token_count_total")) for item in items
                ),
                "uncertainty_token_count_avg": average(
                    _to_float(item.get("uncertainty_token_count_avg")) for item in items
                ),
                "uncertainty_type_counts": dict(_merge_count_dicts(items, "uncertainty_type_counts")),
                "high_uncertainty_count_total_avg": average(
                    _to_float(item.get("high_uncertainty_count_total")) for item in items
                ),
                "high_uncertainty_count_avg": average(_to_float(item.get("high_uncertainty_count_avg")) for item in items),
                "affordance_token_count_total_avg": average(
                    _to_float(item.get("affordance_token_count_total")) for item in items
                ),
                "affordance_token_count_avg": average(
                    _to_float(item.get("affordance_token_count_avg")) for item in items
                ),
                "affordance_type_counts": dict(_merge_count_dicts(items, "affordance_type_counts")),
                "scene_graph_node_count_avg": average(
                    _to_float(item.get("scene_graph_node_count_avg")) for item in items
                ),
                "scene_graph_edge_count_avg": average(
                    _to_float(item.get("scene_graph_edge_count_avg")) for item in items
                ),
                "event_token_count_total_avg": average(
                    _to_float(item.get("event_token_count_total")) for item in items
                ),
                "event_token_count_avg": average(_to_float(item.get("event_token_count_avg")) for item in items),
                "event_type_counts": dict(_merge_event_type_counts(items)),
                "evidence_token_count_total_avg": average(
                    _to_float(item.get("evidence_token_count_total")) for item in items
                ),
                "evidence_token_count_avg": average(_to_float(item.get("evidence_token_count_avg")) for item in items),
                "evidence_type_counts": dict(_merge_count_dicts(items, "evidence_type_counts")),
                "risk_evidence_count_total_avg": average(
                    _to_float(item.get("risk_evidence_count_total")) for item in items
                ),
                "uncertainty_evidence_count_total_avg": average(
                    _to_float(item.get("uncertainty_evidence_count_total")) for item in items
                ),
                "event_evidence_count_total_avg": average(
                    _to_float(item.get("event_evidence_count_total")) for item in items
                ),
                "decision_evidence_count_total_avg": average(
                    _to_float(item.get("decision_evidence_count_total")) for item in items
                ),
                "decision_evidence_coverage_avg": average(
                    _to_float(item.get("decision_evidence_coverage")) for item in items
                ),
                "changed_object_count_avg": average(_to_float(item.get("changed_object_count_avg")) for item in items),
                "affected_token_count_avg": average(_to_float(item.get("affected_token_count_avg")) for item in items),
                "full_recompute_latency_avg_ms": average(
                    _to_float(item.get("full_recompute_latency_avg_ms")) for item in items
                ),
                "incremental_update_latency_avg_ms": average(
                    _to_float(item.get("incremental_update_latency_avg_ms")) for item in items
                ),
                "incremental_update_benefit_avg": average(
                    _to_float(item.get("incremental_update_benefit_avg")) for item in items
                ),
                "rast_reason_code_counts": dict(_merge_count_dicts(items, "rast_reason_code_counts")),
                "object_list_reason_code_counts": dict(_merge_count_dicts(items, "object_list_reason_code_counts")),
                "flat_feature_reason_code_counts": dict(_merge_count_dicts(items, "flat_feature_reason_code_counts")),
                "scene_graph_reason_code_counts": dict(_merge_count_dicts(items, "scene_graph_reason_code_counts")),
                "event_aware_rast_reason_code_counts": dict(
                    _merge_count_dicts(items, "event_aware_rast_reason_code_counts")
                ),
                "uncertainty_aware_rast_reason_code_counts": dict(
                    _merge_count_dicts(items, "uncertainty_aware_rast_reason_code_counts")
                ),
                "affordance_aware_rast_action_counts": dict(
                    _merge_count_dicts(items, "affordance_aware_rast_action_counts")
                ),
                "affordance_aware_rast_reason_code_counts": dict(
                    _merge_count_dicts(items, "affordance_aware_rast_reason_code_counts")
                ),
                "event_policy_variant_action_counts": dict(
                    _merge_nested_count_dicts(items, "event_policy_variant_action_counts")
                ),
                "event_policy_variant_reason_code_counts": dict(
                    _merge_nested_count_dicts(items, "event_policy_variant_reason_code_counts")
                ),
                "rast_trigger_token_count_total_avg": average(
                    _to_float(item.get("rast_trigger_token_count_total")) for item in items
                ),
                "decision_trace_coverage_avg": average(
                    _to_float(item.get("decision_trace_coverage")) for item in items
                ),
                "scene_graph_decision_trace_coverage_avg": average(
                    _to_float(item.get("scene_graph_decision_trace_coverage")) for item in items
                ),
                "event_aware_decision_trace_coverage_avg": average(
                    _to_float(item.get("event_aware_decision_trace_coverage")) for item in items
                ),
                "uncertainty_aware_decision_trace_coverage_avg": average(
                    _to_float(item.get("uncertainty_aware_decision_trace_coverage")) for item in items
                ),
                "affordance_aware_decision_trace_coverage_avg": average(
                    _to_float(item.get("affordance_aware_decision_trace_coverage")) for item in items
                ),
                "latency_avg_ms": average(_to_float(item.get("latency_avg_ms")) for item in items),
                "planning_latency_avg_ms": average(_to_float(item.get("planning_latency_avg_ms")) for item in items),
            }
        )
    return summaries


def summarize_by_keys(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    """복수 key 조합을 하나의 group value로 묶어 sensitivity summary를 계산합니다."""

    group_key = "__".join(keys)
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        copied[group_key] = " | ".join(f"{key}={row.get(key, '')}" for key in keys)
        normalized_rows.append(copied)
    return summarize_by_key(normalized_rows, group_key)


def write_summary_csv(summary: dict[str, list[dict[str, Any]]], path: Path) -> None:
    """두 종류의 group summary를 하나의 CSV로 저장합니다."""

    fieldnames = [
        "group_type",
        "group_value",
        "run_count",
        "success_rate",
        "near_miss_count_avg",
        "rast_vs_object_list_disagreement_avg",
        "rast_vs_flat_feature_disagreement_avg",
        "object_list_vs_flat_feature_disagreement_avg",
        "rast_vs_event_aware_disagreement_avg",
        "rast_vs_uncertainty_aware_disagreement_avg",
        "rast_vs_affordance_aware_disagreement_avg",
        "rast_vs_scene_graph_disagreement_avg",
        "scene_graph_vs_flat_feature_disagreement_avg",
        "rast_vs_scene_graph_same_action_different_reason_avg",
        "rast_vs_scene_graph_same_action_different_reason_rate_avg",
        "scene_graph_trigger_edge_count_avg",
        "rast_trigger_risk_token_count_avg",
        "event_aware_trigger_event_count_avg",
        "event_triggered_action_count_avg",
        "uncertainty_triggered_action_count_avg",
        "affordance_triggered_action_count_avg",
        "relation_token_count_total_avg",
        "relation_token_count_avg",
        "relation_type_counts",
        "uncertainty_token_count_total_avg",
        "uncertainty_token_count_avg",
        "uncertainty_type_counts",
        "high_uncertainty_count_total_avg",
        "high_uncertainty_count_avg",
        "affordance_token_count_total_avg",
        "affordance_token_count_avg",
        "affordance_type_counts",
        "scene_graph_node_count_avg",
        "scene_graph_edge_count_avg",
        "event_token_count_total_avg",
        "event_token_count_avg",
        "event_type_counts",
        "evidence_token_count_total_avg",
        "evidence_token_count_avg",
        "evidence_type_counts",
        "risk_evidence_count_total_avg",
        "uncertainty_evidence_count_total_avg",
        "event_evidence_count_total_avg",
        "decision_evidence_count_total_avg",
        "decision_evidence_coverage_avg",
        "changed_object_count_avg",
        "affected_token_count_avg",
        "full_recompute_latency_avg_ms",
        "incremental_update_latency_avg_ms",
        "incremental_update_benefit_avg",
        "rast_reason_code_counts",
        "object_list_reason_code_counts",
        "flat_feature_reason_code_counts",
        "scene_graph_reason_code_counts",
        "event_aware_rast_reason_code_counts",
        "uncertainty_aware_rast_reason_code_counts",
        "affordance_aware_rast_action_counts",
        "affordance_aware_rast_reason_code_counts",
        "event_policy_variant_action_counts",
        "event_policy_variant_reason_code_counts",
        "rast_trigger_token_count_total_avg",
        "decision_trace_coverage_avg",
        "scene_graph_decision_trace_coverage_avg",
        "event_aware_decision_trace_coverage_avg",
        "uncertainty_aware_decision_trace_coverage_avg",
        "affordance_aware_decision_trace_coverage_avg",
        "latency_avg_ms",
        "planning_latency_avg_ms",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for group_type, group_rows in summary.items():
            key = _summary_group_key(group_type, group_rows)
            for row in group_rows:
                writer.writerow(
                    {
                        "group_type": group_type,
                        "group_value": row.get(key, ""),
                        "run_count": row["run_count"],
                        "success_rate": row["success_rate"],
                        "near_miss_count_avg": row["near_miss_count_avg"],
                        "rast_vs_object_list_disagreement_avg": row["rast_vs_object_list_disagreement_avg"],
                        "rast_vs_flat_feature_disagreement_avg": row["rast_vs_flat_feature_disagreement_avg"],
                        "object_list_vs_flat_feature_disagreement_avg": row[
                            "object_list_vs_flat_feature_disagreement_avg"
                        ],
                        "rast_vs_event_aware_disagreement_avg": row["rast_vs_event_aware_disagreement_avg"],
                        "rast_vs_uncertainty_aware_disagreement_avg": row[
                            "rast_vs_uncertainty_aware_disagreement_avg"
                        ],
                        "rast_vs_affordance_aware_disagreement_avg": row[
                            "rast_vs_affordance_aware_disagreement_avg"
                        ],
                        "rast_vs_scene_graph_disagreement_avg": row["rast_vs_scene_graph_disagreement_avg"],
                        "scene_graph_vs_flat_feature_disagreement_avg": row[
                            "scene_graph_vs_flat_feature_disagreement_avg"
                        ],
                        "rast_vs_scene_graph_same_action_different_reason_avg": row[
                            "rast_vs_scene_graph_same_action_different_reason_avg"
                        ],
                        "rast_vs_scene_graph_same_action_different_reason_rate_avg": row[
                            "rast_vs_scene_graph_same_action_different_reason_rate_avg"
                        ],
                        "scene_graph_trigger_edge_count_avg": row["scene_graph_trigger_edge_count_avg"],
                        "rast_trigger_risk_token_count_avg": row["rast_trigger_risk_token_count_avg"],
                        "event_aware_trigger_event_count_avg": row["event_aware_trigger_event_count_avg"],
                        "event_triggered_action_count_avg": row["event_triggered_action_count_avg"],
                        "uncertainty_triggered_action_count_avg": row["uncertainty_triggered_action_count_avg"],
                        "affordance_triggered_action_count_avg": row["affordance_triggered_action_count_avg"],
                        "relation_token_count_total_avg": row["relation_token_count_total_avg"],
                        "relation_token_count_avg": row["relation_token_count_avg"],
                        "relation_type_counts": json.dumps(row["relation_type_counts"], ensure_ascii=False),
                        "uncertainty_token_count_total_avg": row["uncertainty_token_count_total_avg"],
                        "uncertainty_token_count_avg": row["uncertainty_token_count_avg"],
                        "uncertainty_type_counts": json.dumps(row["uncertainty_type_counts"], ensure_ascii=False),
                        "high_uncertainty_count_total_avg": row["high_uncertainty_count_total_avg"],
                        "high_uncertainty_count_avg": row["high_uncertainty_count_avg"],
                        "affordance_token_count_total_avg": row["affordance_token_count_total_avg"],
                        "affordance_token_count_avg": row["affordance_token_count_avg"],
                        "affordance_type_counts": json.dumps(row["affordance_type_counts"], ensure_ascii=False),
                        "scene_graph_node_count_avg": row["scene_graph_node_count_avg"],
                        "scene_graph_edge_count_avg": row["scene_graph_edge_count_avg"],
                        "event_token_count_total_avg": row["event_token_count_total_avg"],
                        "event_token_count_avg": row["event_token_count_avg"],
                        "event_type_counts": json.dumps(row["event_type_counts"], ensure_ascii=False),
                        "evidence_token_count_total_avg": row["evidence_token_count_total_avg"],
                        "evidence_token_count_avg": row["evidence_token_count_avg"],
                        "evidence_type_counts": json.dumps(row["evidence_type_counts"], ensure_ascii=False),
                        "risk_evidence_count_total_avg": row["risk_evidence_count_total_avg"],
                        "uncertainty_evidence_count_total_avg": row["uncertainty_evidence_count_total_avg"],
                        "event_evidence_count_total_avg": row["event_evidence_count_total_avg"],
                        "decision_evidence_count_total_avg": row["decision_evidence_count_total_avg"],
                        "decision_evidence_coverage_avg": row["decision_evidence_coverage_avg"],
                        "changed_object_count_avg": row["changed_object_count_avg"],
                        "affected_token_count_avg": row["affected_token_count_avg"],
                        "full_recompute_latency_avg_ms": row["full_recompute_latency_avg_ms"],
                        "incremental_update_latency_avg_ms": row["incremental_update_latency_avg_ms"],
                        "incremental_update_benefit_avg": row["incremental_update_benefit_avg"],
                        "rast_reason_code_counts": json.dumps(row["rast_reason_code_counts"], ensure_ascii=False),
                        "object_list_reason_code_counts": json.dumps(
                            row["object_list_reason_code_counts"],
                            ensure_ascii=False,
                        ),
                        "flat_feature_reason_code_counts": json.dumps(
                            row["flat_feature_reason_code_counts"],
                            ensure_ascii=False,
                        ),
                        "scene_graph_reason_code_counts": json.dumps(
                            row["scene_graph_reason_code_counts"],
                            ensure_ascii=False,
                        ),
                        "event_aware_rast_reason_code_counts": json.dumps(
                            row["event_aware_rast_reason_code_counts"],
                            ensure_ascii=False,
                        ),
                        "uncertainty_aware_rast_reason_code_counts": json.dumps(
                            row["uncertainty_aware_rast_reason_code_counts"],
                            ensure_ascii=False,
                        ),
                        "affordance_aware_rast_action_counts": json.dumps(
                            row["affordance_aware_rast_action_counts"],
                            ensure_ascii=False,
                        ),
                        "affordance_aware_rast_reason_code_counts": json.dumps(
                            row["affordance_aware_rast_reason_code_counts"],
                            ensure_ascii=False,
                        ),
                        "event_policy_variant_action_counts": json.dumps(
                            row["event_policy_variant_action_counts"],
                            ensure_ascii=False,
                        ),
                        "event_policy_variant_reason_code_counts": json.dumps(
                            row["event_policy_variant_reason_code_counts"],
                            ensure_ascii=False,
                        ),
                        "rast_trigger_token_count_total_avg": row["rast_trigger_token_count_total_avg"],
                        "decision_trace_coverage_avg": row["decision_trace_coverage_avg"],
                        "scene_graph_decision_trace_coverage_avg": row[
                            "scene_graph_decision_trace_coverage_avg"
                        ],
                        "event_aware_decision_trace_coverage_avg": row[
                            "event_aware_decision_trace_coverage_avg"
                        ],
                        "uncertainty_aware_decision_trace_coverage_avg": row[
                            "uncertainty_aware_decision_trace_coverage_avg"
                        ],
                        "affordance_aware_decision_trace_coverage_avg": row[
                            "affordance_aware_decision_trace_coverage_avg"
                        ],
                        "latency_avg_ms": row["latency_avg_ms"],
                        "planning_latency_avg_ms": row["planning_latency_avg_ms"],
                    }
                )


def average(values) -> float:
    items = [value for value in values if value is not None]
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
            return {}
    if not isinstance(value, dict):
        return {}
    parsed: dict[str, dict[str, int]] = {}
    for outer_key, inner_value in value.items():
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
            return {}
        if isinstance(parsed, dict):
            return {str(key): int(count) for key, count in parsed.items()}
    return {}


def _summary_group_key(group_type: str, group_rows: list[dict[str, Any]]) -> str:
    known = {
        "by_scenario": "scenario",
        "by_apply_policy": "apply_policy",
        "by_update_mode": "update_mode",
        "by_event_policy_variant": "event_policy_variant",
        "by_scenario_event_policy_variant": "scenario__event_policy_variant",
        "by_scenario_risk_threshold": "scenario__risk_threshold",
        "by_scenario_noise_level": "scenario__position_noise_std__distance_noise_std__visibility_flip_prob",
    }
    if group_type in known:
        return known[group_type]
    if group_rows:
        for key in group_rows[0]:
            if key not in {"run_count", "success_rate"}:
                return key
    return "group_value"

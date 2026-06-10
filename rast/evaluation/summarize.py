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
                "event_token_count_total_avg": average(
                    _to_float(item.get("event_token_count_total")) for item in items
                ),
                "event_token_count_avg": average(_to_float(item.get("event_token_count_avg")) for item in items),
                "event_type_counts": dict(_merge_event_type_counts(items)),
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
                "rast_trigger_token_count_total_avg": average(
                    _to_float(item.get("rast_trigger_token_count_total")) for item in items
                ),
                "decision_trace_coverage_avg": average(
                    _to_float(item.get("decision_trace_coverage")) for item in items
                ),
                "latency_avg_ms": average(_to_float(item.get("latency_avg_ms")) for item in items),
                "planning_latency_avg_ms": average(_to_float(item.get("planning_latency_avg_ms")) for item in items),
            }
        )
    return summaries


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
        "event_token_count_total_avg",
        "event_token_count_avg",
        "event_type_counts",
        "changed_object_count_avg",
        "affected_token_count_avg",
        "full_recompute_latency_avg_ms",
        "incremental_update_latency_avg_ms",
        "incremental_update_benefit_avg",
        "rast_reason_code_counts",
        "object_list_reason_code_counts",
        "flat_feature_reason_code_counts",
        "rast_trigger_token_count_total_avg",
        "decision_trace_coverage_avg",
        "latency_avg_ms",
        "planning_latency_avg_ms",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for group_type, group_rows in summary.items():
            key = {"by_scenario": "scenario", "by_apply_policy": "apply_policy", "by_update_mode": "update_mode"}[
                group_type
            ]
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
                        "event_token_count_total_avg": row["event_token_count_total_avg"],
                        "event_token_count_avg": row["event_token_count_avg"],
                        "event_type_counts": json.dumps(row["event_type_counts"], ensure_ascii=False),
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
                        "rast_trigger_token_count_total_avg": row["rast_trigger_token_count_total_avg"],
                        "decision_trace_coverage_avg": row["decision_trace_coverage_avg"],
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

"""여러 episode summary를 하나의 aggregate result로 합치는 유틸리티입니다."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


REQUIRED_AGGREGATE_COLUMNS: tuple[str, ...] = (
    "suite_run_id",
    "scenario",
    "seed",
    "apply_policy",
    "update_mode",
    "risk_threshold",
    "near_miss_threshold",
    "collision_threshold",
    "success",
    "goal_reached",
    "completed_steps",
    "collision_count",
    "near_miss_count",
    "baseline_disagreement_count",
    "rast_vs_object_list_disagreement_count",
    "rast_vs_flat_feature_disagreement_count",
    "object_list_vs_flat_feature_disagreement_count",
    "token_count_avg",
    "object_count_avg",
    "flat_feature_row_count_avg",
    "event_token_count_total",
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
    "rast_trigger_token_count_total",
    "decision_trace_coverage",
    "latency_avg_ms",
    "latency_p50_ms",
    "latency_p95_ms",
    "token_generation_latency_avg_ms",
    "planning_latency_avg_ms",
    "total_latency_avg_ms",
)

AGGREGATE_DEFAULTS: dict[str, Any] = {
    "update_mode": "full_recompute",
    "event_token_count_total": 0,
    "event_token_count_avg": 0.0,
    "event_type_counts": {},
    "changed_object_count_avg": 0.0,
    "affected_token_count_avg": 0.0,
    "full_recompute_latency_avg_ms": 0.0,
    "incremental_update_latency_avg_ms": 0.0,
    "incremental_update_benefit_avg": 0.0,
    "rast_reason_code_counts": {},
    "object_list_reason_code_counts": {},
    "flat_feature_reason_code_counts": {},
    "rast_trigger_token_count_total": 0,
    "decision_trace_coverage": 0.0,
}

EXTRA_AGGREGATE_COLUMNS: tuple[str, ...] = (
    "status",
    "error",
    "summary_path",
    "episode_output_dir",
)


def aggregate_episode_summaries(
    run_metadata: Iterable[dict[str, Any]],
    *,
    output_dir: str | Path,
) -> list[dict[str, Any]]:
    """run metadata와 episode_summary.json들을 읽어 CSV/JSON aggregate를 저장합니다."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = [aggregate_row(metadata) for metadata in run_metadata]
    write_aggregate_results(rows, output)
    return rows


def aggregate_row(metadata: dict[str, Any]) -> dict[str, Any]:
    """단일 run metadata를 aggregate row로 변환합니다."""

    row = _base_row(metadata)
    status = str(metadata.get("status", "success"))
    row["status"] = status
    row["error"] = metadata.get("error", "")
    row["summary_path"] = str(metadata.get("summary_path", ""))
    row["episode_output_dir"] = str(metadata.get("episode_output_dir", ""))

    if status != "success":
        return row

    summary_path = Path(str(metadata.get("summary_path", "")))
    if not summary_path.exists():
        row["status"] = "failed"
        row["error"] = f"summary_path가 존재하지 않습니다: {summary_path}"
        return row

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for column in REQUIRED_AGGREGATE_COLUMNS:
        if column in metadata:
            continue
        row[column] = summary.get(column, row.get(column, _default_value(column)))
    return row


def write_aggregate_results(rows: list[dict[str, Any]], output_dir: Path) -> None:
    """aggregate_results.csv와 aggregate_results.json을 저장합니다."""

    fieldnames = list(REQUIRED_AGGREGATE_COLUMNS + EXTRA_AGGREGATE_COLUMNS)
    normalized_rows = [{field: row.get(field, "") for field in fieldnames} for row in rows]

    csv_path = output_dir / "aggregate_results.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)

    json_path = output_dir / "aggregate_results.json"
    json_path.write_text(json.dumps(normalized_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _base_row(metadata: dict[str, Any]) -> dict[str, Any]:
    row = {column: _default_value(column) for column in REQUIRED_AGGREGATE_COLUMNS}
    for column in (
        "suite_run_id",
        "scenario",
        "seed",
        "apply_policy",
        "update_mode",
        "risk_threshold",
        "near_miss_threshold",
        "collision_threshold",
    ):
        row[column] = metadata.get(column, _default_value(column))
    return row


def _default_value(column: str) -> Any:
    """과거 summary에 없는 신규 event field를 backward-compatible 기본값으로 채웁니다."""

    if column in AGGREGATE_DEFAULTS:
        return AGGREGATE_DEFAULTS[column]
    return ""

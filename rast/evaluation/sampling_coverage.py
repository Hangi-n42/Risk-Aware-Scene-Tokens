"""Sampled evaluation coverage report utilities."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from rast.evaluation.report import read_table


COVERAGE_AXES: tuple[str, ...] = (
    "scenario",
    "apply_policy",
    "update_mode",
    "event_policy_variant",
    "risk_threshold",
    "near_miss_threshold",
    "near_agent_relation_threshold",
    "near_path_relation_threshold",
    "blocking_relation_threshold",
    "classification_uncertainty_threshold",
    "position_variance_threshold",
    "occlusion_ratio_threshold",
    "sensor_agreement_threshold",
    "position_noise_std",
    "distance_noise_std",
    "visibility_flip_prob",
)


def analyze_sampling_coverage(
    *,
    results_path: str | Path,
    metadata_path: str | Path | None = None,
) -> dict[str, Any]:
    """Aggregate 결과에서 sampling 축별 관측 분포와 coverage를 계산합니다."""

    rows = read_table(results_path)
    metadata = _read_json(metadata_path)
    expected_values = expected_axis_values(metadata)
    axes: dict[str, dict[str, Any]] = {}
    for axis in COVERAGE_AXES:
        axis_rows = _rows_for_axis(rows, axis)
        counts = Counter(_normalize_value(row.get(axis)) for row in axis_rows if row.get(axis) not in ("", None))
        observed = sorted(counts.keys(), key=_sort_key)
        expected = expected_values.get(axis)
        missing: list[str] = []
        coverage_rate: float | None = None
        if expected:
            expected_normalized = [_normalize_value(value) for value in expected]
            missing = sorted(set(expected_normalized) - set(observed), key=_sort_key)
            coverage_rate = (len(set(expected_normalized) - set(missing)) / len(set(expected_normalized))) if expected_normalized else None
        underrepresented = _underrepresented_values(counts)
        axes[axis] = {
            "observed_values": observed,
            "observed_counts": dict(sorted(counts.items(), key=lambda item: _sort_key(item[0]))),
            "expected_values": [_normalize_value(value) for value in expected] if expected else [],
            "coverage_rate": coverage_rate,
            "missing_values": missing,
            "underrepresented_values": underrepresented,
            "row_scope": _row_scope_for_axis(axis),
            "row_count": len(axis_rows),
        }
    return {
        "results_path": str(results_path),
        "metadata_path": str(metadata_path) if metadata_path is not None else "",
        "row_count": len(rows),
        "suite_run_id": _suite_run_id(rows, metadata),
        "axes": axes,
        "interpretation_note": (
            "Missing or underrepresented values indicate sampling coverage gaps, not planner performance changes."
        ),
    }


def generate_sampling_coverage_markdown(summary: dict[str, Any]) -> str:
    """Coverage summary를 사람이 읽을 수 있는 Markdown으로 변환합니다."""

    lines = [
        "# RAST Sampling Coverage Report",
        "",
        "이 문서는 sampled extended evaluation의 축별 포함 여부를 점검합니다.",
        "missing 또는 underrepresented 값은 성능 문제가 아니라 sampling coverage 문제로 해석해야 합니다.",
        "",
        "## Context",
        "",
        f"- suite_run_id: `{summary.get('suite_run_id', '')}`",
        f"- results: `{summary.get('results_path', '')}`",
        f"- metadata: `{summary.get('metadata_path') or 'not provided'}`",
        f"- analyzed rows: {summary.get('row_count', 0)}",
        "",
        "## Axis Coverage",
        "",
        "| Axis | Row Scope | Observed Values | Observed Counts | Coverage Rate | Missing Values | Underrepresented Values |",
        "|---|---|---|---|---:|---|---|",
    ]
    for axis in COVERAGE_AXES:
        item = summary["axes"].get(axis, {})
        coverage = item.get("coverage_rate")
        coverage_text = "n/a" if coverage is None else f"{coverage:.3f}"
        lines.append(
            f"| `{axis}` | {item.get('row_scope', 'all rows')} ({item.get('row_count', 0)} rows) | "
            f"`{', '.join(item.get('observed_values', []))}` | "
            f"`{json.dumps(item.get('observed_counts', {}), ensure_ascii=False, sort_keys=True)}` | "
            f"{coverage_text} | `{', '.join(item.get('missing_values', [])) or 'none'}` | "
            f"`{', '.join(item.get('underrepresented_values', [])) or 'none'}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- expected values를 metadata에서 알 수 없는 축은 observed distribution만 표시합니다.",
            "- coverage rate는 metadata/config에서 expected value list를 확인할 수 있는 축에만 계산합니다.",
            "- 이 보고서는 sampled extended result가 full extended grid를 대체하지 않는다는 점을 확인하기 위한 보조 artifact입니다.",
            "- WindowsMetadataSim metadata simulator 기반 결과이며 real-world performance claim을 지원하지 않습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_sampling_coverage_report(
    *,
    results_path: str | Path,
    output_path: str | Path,
    metadata_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Markdown report와 JSON summary를 저장합니다."""

    summary = analyze_sampling_coverage(results_path=results_path, metadata_path=metadata_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate_sampling_coverage_markdown(summary), encoding="utf-8")
    json_path = Path(json_output_path) if json_output_path is not None else output.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def expected_axis_values(metadata: dict[str, Any]) -> dict[str, list[Any]]:
    """suite_metadata axis_summary에서 알 수 있는 expected values를 추출합니다."""

    axis_summary = metadata.get("axis_summary", {}) if isinstance(metadata, dict) else {}
    relation = axis_summary.get("relation_threshold_values", {}) if isinstance(axis_summary, dict) else {}
    uncertainty = axis_summary.get("uncertainty_threshold_values", {}) if isinstance(axis_summary, dict) else {}
    noise_values = axis_summary.get("noise_values", []) if isinstance(axis_summary, dict) else []
    return {
        "scenario": _list_or_empty(axis_summary.get("scenario_values")),
        "apply_policy": _list_or_empty(axis_summary.get("apply_policy_values")),
        "update_mode": _list_or_empty(axis_summary.get("update_mode_values")),
        "event_policy_variant": _list_or_empty(axis_summary.get("event_policy_variant_values")),
        "risk_threshold": _list_or_empty(axis_summary.get("risk_threshold_values")),
        "near_miss_threshold": _list_or_empty(axis_summary.get("near_miss_threshold_values")),
        "near_agent_relation_threshold": _list_or_empty(relation.get("near_agent")),
        "near_path_relation_threshold": _list_or_empty(relation.get("near_path")),
        "blocking_relation_threshold": _list_or_empty(relation.get("blocking")),
        "classification_uncertainty_threshold": _list_or_empty(uncertainty.get("classification_uncertainty")),
        "position_variance_threshold": _list_or_empty(uncertainty.get("position_variance")),
        "occlusion_ratio_threshold": _list_or_empty(uncertainty.get("occlusion_ratio")),
        "sensor_agreement_threshold": _list_or_empty(uncertainty.get("sensor_agreement")),
        "position_noise_std": _noise_axis_values(noise_values, "position_noise_std"),
        "distance_noise_std": _noise_axis_values(noise_values, "distance_noise_std"),
        "visibility_flip_prob": _noise_axis_values(noise_values, "visibility_flip_prob"),
    }


def _rows_for_axis(rows: list[dict[str, Any]], axis: str) -> list[dict[str, Any]]:
    if axis == "event_policy_variant":
        return [row for row in rows if str(row.get("apply_policy", "")) == "event_aware_rast"]
    return rows


def _row_scope_for_axis(axis: str) -> str:
    if axis == "event_policy_variant":
        return "`apply_policy=event_aware_rast`"
    return "all rows"


def _read_json(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    json_path = Path(path)
    if not json_path.exists():
        return {}
    return json.loads(json_path.read_text(encoding="utf-8"))


def _suite_run_id(rows: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    if metadata.get("suite_run_id"):
        return str(metadata["suite_run_id"])
    if rows:
        return str(rows[0].get("suite_run_id", ""))
    return ""


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _noise_axis_values(noise_values: Any, key: str) -> list[Any]:
    if not isinstance(noise_values, list):
        return []
    return sorted({item.get(key) for item in noise_values if isinstance(item, dict) and item.get(key) is not None})


def _underrepresented_values(counts: Counter[str]) -> list[str]:
    if not counts:
        return []
    average_count = sum(counts.values()) / len(counts)
    threshold = max(1.0, average_count * 0.5)
    return sorted([value for value, count in counts.items() if count < threshold], key=_sort_key)


def _normalize_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    text = str(value)
    try:
        numeric = float(text)
    except ValueError:
        return text
    return f"{numeric:g}"


def _sort_key(value: str) -> tuple[int, float | str]:
    try:
        return (0, float(value))
    except ValueError:
        return (1, value)

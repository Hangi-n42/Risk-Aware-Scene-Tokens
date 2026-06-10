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
    "Aggregate Results",
    "Scenario-level Observations",
    "Baseline Disagreement Analysis",
    "Decision Trace Summary",
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
    lines.extend(_aggregate_results(stats))
    lines.extend(_scenario_observations(stats, summary_rows))
    lines.extend(_baseline_disagreement_analysis(stats))
    lines.extend(_decision_trace_summary(stats))
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
    scenario_groups = group_by(successful_rows, "scenario")
    policy_groups = group_by(successful_rows, "apply_policy")
    update_mode_groups = group_by(successful_rows, "update_mode", default="full_recompute")
    return {
        "total_runs": len(rows),
        "failed_runs": len(rows) - len(successful_rows),
        "successful_runs": len(successful_rows),
        "scenarios": sorted({str(row.get("scenario", "")) for row in rows if row.get("scenario", "")}),
        "apply_policies": sorted({str(row.get("apply_policy", "")) for row in rows if row.get("apply_policy", "")}),
        "update_modes": sorted({_row_update_mode(row) for row in rows}),
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
        "overall": _group_stats(successful_rows),
    }


def group_by(rows: list[dict[str, Any]], key: str, *, default: str = "") -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key) or default)].append(row)
    return grouped


def _row_update_mode(row: dict[str, Any]) -> str:
    return str(row.get("update_mode") or "full_recompute")


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
        "rast_trigger_token_count_total": sum(_to_float(row.get("rast_trigger_token_count_total")) or 0.0 for row in rows),
        "rast_trigger_token_count_total_avg": average(_to_float(row.get("rast_trigger_token_count_total")) for row in rows),
        "decision_trace_coverage": average(_to_float(row.get("decision_trace_coverage")) for row in rows),
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
        "- 이번 Batch에서 EventToken은 planner input으로 action을 바꾸지 않고, semantic event logging과 summary에만 사용됩니다.",
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
        "- token_count_avg / object_count_avg / flat_feature_row_count_avg",
        "- event_token_count_total / event_token_count_avg / event_type_counts",
        "- update_mode / changed_object_count_avg / affected_token_count_avg",
        "- full_recompute_latency_avg_ms / incremental_update_latency_avg_ms / incremental_update_benefit_avg",
        "- rast_reason_code_counts / object_list_reason_code_counts / flat_feature_reason_code_counts",
        "- rast_trigger_token_count_total / decision_trace_coverage",
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
        "- EventToken은 semantic event 감지와 기록을 위한 token이며, 현재 planner action에는 영향을 주지 않습니다.",
        "- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용됩니다. incremental update optimization is experimental.",
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
        "- EventToken does not affect planner action in this batch; it is used only for logging and summary.",
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
        "| Scenario | Runs | Success Rate | Avg Near-miss | Avg RAST vs Object | Avg RAST vs Flat | Avg Object vs Flat |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario, item in stats["scenario_stats"].items():
        lines.append(
            f"| `{scenario}` | {int(item['run_count'])} | {_fmt(item['success_rate'])} | "
            f"{_fmt(item['near_miss_count_avg'])} | "
            f"{_fmt(item['rast_vs_object_list_disagreement_avg'])} | "
            f"{_fmt(item['rast_vs_flat_feature_disagreement_avg'])} | "
            f"{_fmt(item['object_list_vs_flat_feature_disagreement_avg'])} |"
        )
    lines.append("")
    return lines


def _baseline_disagreement_analysis(stats: dict[str, Any]) -> list[str]:
    overall = stats["overall"]
    rast_flat = overall["rast_vs_flat_feature_disagreement_avg"]
    rast_object = overall["rast_vs_object_list_disagreement_avg"]
    object_flat = overall["object_list_vs_flat_feature_disagreement_avg"]
    lines = [
        "## Baseline Disagreement Analysis",
        "",
        f"- Average RAST vs Object List disagreement: {_fmt(rast_object)}",
        f"- Average RAST vs Flat Feature disagreement: {_fmt(rast_flat)}",
        f"- Average Object List vs Flat Feature disagreement: {_fmt(object_flat)}",
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
        "- EventToken is still not used by planner policy in this batch.",
        "",
        "| Planner | Reason Code Counts |",
        "|---|---|",
        f"| RAST | `{_json_compact(overall['rast_reason_code_counts'])}` |",
        f"| Object List | `{_json_compact(overall['object_list_reason_code_counts'])}` |",
        f"| Flat Feature | `{_json_compact(overall['flat_feature_reason_code_counts'])}` |",
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
        "- 세 planner의 action 선택 사유를 PlannerDecision trace로 기록하고 집계할 수 있음을 보여줍니다.",
        "",
    ]


def _does_not_support() -> list[str]:
    return [
        "## What This Result Does Not Support",
        "",
        "- This result does not support real-world performance claims.",
        "- RAST가 Object List나 Flat Feature보다 일반적으로 우수하다는 결론을 지원하지 않습니다.",
        "- EventToken이 planning 성능, success, near-miss, disagreement를 개선했다는 결론을 지원하지 않습니다.",
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
        "- TokenMemory는 현재 semantic diff와 incremental latency protocol에 사용되지만, incremental update optimization is experimental입니다.",
        "- Batch 9의 incremental update는 measurement protocol 단계이며, 일부 token 계산은 correctness를 위해 여전히 재계산됩니다.",
        "- full_recompute와 incremental 후보를 같은 step에서 모두 측정하므로 report의 selected token_generation latency와 실제 Python wall-clock은 다를 수 있습니다.",
        "- EventToken은 planner action에 영향을 주지 않으므로, success/near-miss/disagreement 변화는 EventToken 효과로 해석하면 안 됩니다.",
        "- PlannerDecision은 현재 deterministic rule-based policy의 내부 규칙을 기록한 것이며, learned model interpretability는 아닙니다.",
        "- 동일 action이라도 planner별 reason_code와 trigger feature가 다를 수 있으므로 action count만으로 의사결정 근거를 해석하면 안 됩니다.",
        "- RelationToken, UncertaintyToken, Scene Graph baseline은 아직 포함하지 않습니다.",
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
        "- 이후 단계에서 EventToken을 planner policy 또는 실제 incremental cache 재사용 최적화에 연결할지 별도 Batch에서 검토합니다.",
        "- Scene Graph baseline, RelationToken, UncertaintyToken, perception-bound adapter는 별도 Batch로 추가합니다.",
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

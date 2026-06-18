"""기존 WindowsMetadataSim evaluation path를 API 응답으로 요약하는 서비스 계층입니다."""

from __future__ import annotations

import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from apps.api.schemas import SUPPORTED_POLICIES, RunScenarioRequest
from experiments.run_windows_metadata_sim import run_simulation
from rast.evaluation.records import StepLogRecord
from rast.simulator.windows_scenarios import available_scenarios, build_windows_scenario


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATHS = (
    ROOT / "docs" / "result_report.md",
    ROOT / "docs" / "technical_report.md",
    ROOT / "docs" / "artifact_manifest.md",
    ROOT / "docs" / "reproducibility_guide.md",
)

_POLICY_DECISION_FIELDS = {
    "object_list": ("object_list_decision", "object_list_reason_code"),
    "flat_feature": ("flat_feature_decision", "flat_feature_reason_code"),
    "scene_graph": ("scene_graph_decision", "scene_graph_reason_code"),
    "rast": ("rast_decision", "rast_reason_code"),
    "event_aware_rast": ("event_aware_rast_decision", "event_aware_rast_reason_code"),
    "uncertainty_aware_rast": ("uncertainty_aware_rast_decision", "uncertainty_aware_rast_reason_code"),
    "affordance_aware_rast": ("affordance_aware_rast_decision", "affordance_aware_rast_reason_code"),
}


def list_scenarios() -> list[str]:
    """현재 WindowsMetadataSim에서 지원하는 scenario 목록입니다."""

    return list(available_scenarios())


def list_policies() -> list[str]:
    """API demo에서 선택 가능한 deterministic planner policy 목록입니다."""

    return list(SUPPORTED_POLICIES)


def run_scenario_summary(request: RunScenarioRequest) -> dict[str, Any]:
    """기존 runner 함수를 직접 호출하고 API용 summary payload만 반환합니다."""

    scenario = build_windows_scenario(request.scenario)
    with tempfile.TemporaryDirectory(prefix="rast_api_") as tmp_dir:
        output_path = Path(tmp_dir) / "step_log.jsonl"
        # 기존 runner는 CLI 진행 로그를 print하므로 API 응답 테스트에서는 stdout을 조용히 둡니다.
        with redirect_stdout(io.StringIO()):
            records = run_simulation(
                sim=scenario.simulator,
                scenario_name=scenario.name,
                max_steps=request.max_steps,
                risk_threshold=scenario.risk_threshold,
                object_list_threshold=scenario.object_list_threshold,
                near_agent_relation_threshold=scenario.resolved_near_agent_relation_threshold,
                near_path_relation_threshold=scenario.resolved_near_path_relation_threshold,
                blocking_relation_threshold=scenario.resolved_blocking_relation_threshold,
                collision_threshold=scenario.collision_threshold,
                near_miss_threshold=scenario.near_miss_threshold,
                update_mode=request.update_mode,
                apply_policy=request.apply_policy,
                output_path=output_path,
                goal=scenario.goal,
            )
        summary = _read_summary(output_path.parent / "episode_summary.json")

    final_record = records[-1] if records else None
    final_decision = _policy_decision(final_record, request.apply_policy) if final_record else {}
    return {
        "scenario": request.scenario,
        "apply_policy": request.apply_policy,
        "max_steps": request.max_steps,
        "update_mode": request.update_mode,
        "selected_action": final_record.selected_action if final_record else "",
        "planner_decision_summary": _decision_summary(final_decision),
        "reason_code": str(final_decision.get("reason_code") or ""),
        "token_counts": _final_token_counts(final_record),
        "token_count_totals": _summary_token_counts(summary),
        "step_count": len(records),
        "latency_summary": _latency_summary(summary),
        "near_miss_count": int(summary.get("near_miss_count", 0)),
        "collision_count": int(summary.get("collision_count", 0)),
        "replay_trace_preview": [_trace_step(record, request.apply_policy) for record in records[:10]],
        "scope_note": (
            "WindowsMetadataSim metadata-only prototype입니다. "
            "실제 로봇, 실제 RGB-D perception, real-world safety 성능을 의미하지 않습니다."
        ),
    }


def latest_report_summaries() -> list[dict[str, Any]]:
    """canonical report 파일의 존재 여부와 첫 heading을 반환합니다."""

    reports: list[dict[str, Any]] = []
    for path in REPORT_PATHS:
        reports.append(
            {
                "path": str(path.relative_to(ROOT)),
                "exists": path.exists(),
                "title": _first_heading(path) if path.exists() else "",
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    return reports


def _read_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _first_heading(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return path.name


def _policy_decision(record: StepLogRecord | None, policy: str) -> dict[str, Any]:
    if record is None:
        return {}
    decision_field, _ = _POLICY_DECISION_FIELDS[policy]
    decision = getattr(record, decision_field, {}) or {}
    return decision if isinstance(decision, dict) else {}


def _decision_summary(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "planner_name": decision.get("planner_name", ""),
        "action": decision.get("action", ""),
        "reason_code": decision.get("reason_code", ""),
        "reason_text": decision.get("reason_text", ""),
        "trigger_object_ids": list(decision.get("trigger_object_ids") or []),
        "trigger_token_ids": list(decision.get("trigger_token_ids") or []),
        "evidence_token_ids": list(decision.get("evidence_token_ids") or []),
    }


def _final_token_counts(record: StepLogRecord | None) -> dict[str, int]:
    if record is None:
        return {name: 0 for name in ("entity", "risk", "relation", "event", "uncertainty", "evidence", "affordance")}
    return {
        "entity": record.entity_token_count,
        "risk": record.risk_token_count,
        "relation": record.relation_token_count,
        "event": record.event_token_count,
        "uncertainty": record.uncertainty_token_count,
        "evidence": record.evidence_token_count,
        "affordance": record.affordance_token_count,
    }


def _summary_token_counts(summary: dict[str, Any]) -> dict[str, int]:
    mapping = {
        "entity": "entity_token_count_total",
        "risk": "risk_token_count_total",
        "relation": "relation_token_count_total",
        "event": "event_token_count_total",
        "uncertainty": "uncertainty_token_count_total",
        "evidence": "evidence_token_count_total",
        "affordance": "affordance_token_count_total",
    }
    return {name: int(summary.get(field, 0) or 0) for name, field in mapping.items()}


def _latency_summary(summary: dict[str, Any]) -> dict[str, float]:
    return {
        "latency_avg_ms": float(summary.get("latency_avg_ms", 0.0) or 0.0),
        "latency_p50_ms": float(summary.get("latency_p50_ms", 0.0) or 0.0),
        "latency_p95_ms": float(summary.get("latency_p95_ms", 0.0) or 0.0),
        "token_generation_latency_avg_ms": float(summary.get("token_generation_latency_avg_ms", 0.0) or 0.0),
        "planning_latency_avg_ms": float(summary.get("planning_latency_avg_ms", 0.0) or 0.0),
        "total_latency_avg_ms": float(summary.get("total_latency_avg_ms", 0.0) or 0.0),
    }


def _trace_step(record: StepLogRecord, policy: str) -> dict[str, Any]:
    decision = _policy_decision(record, policy)
    return {
        "step": record.step,
        "action": record.selected_action,
        "planner_reason_codes": {
            "rast": record.rast_reason_code,
            "object_list": record.object_list_reason_code,
            "flat_feature": record.flat_feature_reason_code,
            "scene_graph": record.scene_graph_reason_code,
            "event_aware_rast": record.event_aware_rast_reason_code,
            "uncertainty_aware_rast": record.uncertainty_aware_rast_reason_code,
            "affordance_aware_rast": record.affordance_aware_rast_reason_code,
        },
        "selected_policy_reason_code": decision.get("reason_code", ""),
        "trigger_token_ids": list(decision.get("trigger_token_ids") or []),
        "trigger_object_ids": list(decision.get("trigger_object_ids") or []),
        "evidence_token_ids": list(decision.get("evidence_token_ids") or [])[:10],
    }

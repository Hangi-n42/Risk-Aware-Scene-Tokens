"""Step log에서 decision replay trace를 내보내는 유틸리티입니다."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPLAY_CASES: tuple[str, ...] = (
    "collision",
    "near_miss",
    "planner_disagreement",
    "rast_vs_scene_graph_disagreement",
    "rast_vs_uncertainty_aware_disagreement",
    "rast_vs_affordance_aware_disagreement",
    "event_triggered_action",
    "uncertainty_triggered_action",
    "affordance_triggered_action",
    "high_risk_token",
    "high_uncertainty_token",
)

REPLAY_CASE_PRIORITY: tuple[str, ...] = (
    "collision",
    "near_miss",
    "rast_vs_scene_graph_disagreement",
    "rast_vs_uncertainty_aware_disagreement",
    "rast_vs_affordance_aware_disagreement",
    "event_triggered_action",
    "uncertainty_triggered_action",
    "affordance_triggered_action",
    "high_risk_token",
    "high_uncertainty_token",
)


def load_step_log(path: str | Path) -> list[dict[str, Any]]:
    """JSONL step log를 dict 목록으로 읽습니다."""

    step_log = Path(path)
    records: list[dict[str, Any]] = []
    with step_log.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def find_step_log(run_dir: str | Path) -> Path:
    """run directory에서 step_log.jsonl을 찾습니다."""

    root = Path(run_dir)
    direct = root / "step_log.jsonl"
    if direct.exists():
        return direct
    candidates = sorted(root.rglob("step_log.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"step_log.jsonl을 찾을 수 없습니다: {root}")
    return candidates[0]


def select_replay_records(records: list[dict[str, Any]], *, limit: int = 20) -> list[dict[str, Any]]:
    """중요한 decision replay case에 해당하는 step만 선택합니다."""

    selected: list[dict[str, Any]] = []
    seen_steps: set[int] = set()
    for record in records:
        cases = replay_cases_for_record(record)
        step = int(record.get("step", -1))
        if cases and step not in seen_steps:
            copied = dict(record)
            copied["replay_cases"] = cases
            selected.append(copied)
            seen_steps.add(step)
        if len(selected) >= limit:
            break
    return selected


def replay_cases_for_record(record: dict[str, Any]) -> list[str]:
    """단일 step record가 어떤 replay case에 해당하는지 판정합니다."""

    cases: list[str] = []
    if record.get("collision"):
        cases.append("collision")
    if record.get("near_miss"):
        cases.append("near_miss")
    if record.get("baseline_disagreed") or record.get("rast_vs_object_list_disagreed"):
        cases.append("planner_disagreement")
    if record.get("rast_vs_scene_graph_disagreed"):
        cases.append("rast_vs_scene_graph_disagreement")
    if record.get("rast_vs_uncertainty_aware_disagreed"):
        cases.append("rast_vs_uncertainty_aware_disagreement")
    if record.get("rast_vs_affordance_aware_disagreed"):
        cases.append("rast_vs_affordance_aware_disagreement")
    if str(record.get("event_aware_rast_reason_code", "")).startswith("event_"):
        cases.append("event_triggered_action")
    if _is_uncertainty_reason(str(record.get("uncertainty_aware_rast_reason_code", ""))):
        cases.append("uncertainty_triggered_action")
    if str(record.get("affordance_aware_rast_reason_code", "")).startswith("affordance_"):
        cases.append("affordance_triggered_action")
    if _has_high_risk_token(record):
        cases.append("high_risk_token")
    if int(record.get("high_uncertainty_count") or 0) > 0 or _has_high_uncertainty_token(record):
        cases.append("high_uncertainty_token")
    return cases


def build_replay_payload(records: list[dict[str, Any]], *, limit: int = 20) -> dict[str, Any]:
    """선택된 replay step을 JSON payload로 구성합니다."""

    selected = select_replay_records(records, limit=limit)
    first = records[0] if records else {}
    return {
        "run_id": first.get("run_id", ""),
        "episode_id": first.get("episode_id", ""),
        "scene_id": first.get("scene_id", ""),
        "scenario": (first.get("extra") or {}).get("scenario", ""),
        "limitation": "WindowsMetadataSim metadata replay, not visual replay.",
        "replay_cases_supported": list(REPLAY_CASES),
        "selected_step_count": len(selected),
        "steps": [_step_payload(record) for record in selected],
    }


def write_decision_replay(
    *,
    step_log_path: str | Path,
    output_md_path: str | Path,
    output_json_path: str | Path | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """step_log.jsonl을 읽어 decision_replay.md/json을 생성합니다."""

    records = load_step_log(step_log_path)
    payload = build_replay_payload(records, limit=limit)
    markdown = render_replay_markdown(payload)

    md_path = Path(output_md_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")

    json_path = Path(output_json_path) if output_json_path is not None else md_path.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_single_step_replay_payload(
    record: dict[str, Any],
    *,
    case_type: str,
    suite_run_id: str = "",
    run_dir: str = "",
) -> dict[str, Any]:
    """suite representative replay용 단일 step payload를 구성합니다."""

    copied = dict(record)
    cases = replay_cases_for_record(copied)
    if case_type and case_type not in cases:
        cases.insert(0, case_type)
    copied["replay_cases"] = cases
    return {
        "suite_run_id": suite_run_id,
        "run_id": copied.get("run_id", ""),
        "episode_id": copied.get("episode_id", ""),
        "scene_id": copied.get("scene_id", ""),
        "scenario": (copied.get("extra") or {}).get("scenario", ""),
        "run_dir": run_dir,
        "case_type": case_type,
        "limitation": "WindowsMetadataSim metadata replay, not visual replay.",
        "replay_cases_supported": list(REPLAY_CASES),
        "selected_step_count": 1,
        "steps": [_step_payload(copied)],
    }


def write_single_step_replay(
    *,
    record: dict[str, Any],
    case_type: str,
    output_md_path: str | Path,
    output_json_path: str | Path | None = None,
    suite_run_id: str = "",
    run_dir: str = "",
) -> dict[str, Any]:
    """대표 replay 한 step을 Markdown/JSON artifact로 저장합니다."""

    payload = build_single_step_replay_payload(
        record,
        case_type=case_type,
        suite_run_id=suite_run_id,
        run_dir=run_dir,
    )
    markdown = render_replay_markdown(payload)

    md_path = Path(output_md_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")

    json_path = Path(output_json_path) if output_json_path is not None else md_path.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def render_replay_markdown(payload: dict[str, Any]) -> str:
    """decision replay payload를 사람이 읽을 수 있는 Markdown으로 변환합니다."""

    lines = [
        "# RAST Decision Replay",
        "",
        f"- run_id: `{payload.get('run_id', '')}`",
        f"- suite_run_id: `{payload.get('suite_run_id', '')}`",
        f"- episode_id: `{payload.get('episode_id', '')}`",
        f"- scene_id: `{payload.get('scene_id', '')}`",
        f"- scenario: `{payload.get('scenario', '')}`",
        f"- case_type: `{payload.get('case_type', '')}`",
        f"- run_dir: `{payload.get('run_dir', '')}`",
        f"- selected_step_count: {payload.get('selected_step_count', 0)}",
        "- limitation: metadata simulator replay, not visual replay",
        "",
    ]
    for step in payload.get("steps", []):
        lines.extend(
            [
                f"## Step {step.get('step')}",
                "",
                f"- replay_cases: `{', '.join(step.get('replay_cases', []))}`",
                f"- selected_action: `{step.get('selected_action', '')}`",
                f"- actions: `{json.dumps(step.get('selected_actions', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- reason_codes: `{json.dumps(step.get('reason_codes', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- trigger_tokens: `{json.dumps(step.get('trigger_tokens', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- evidence_token_ids: `{', '.join(step.get('evidence_token_ids', []))}`",
                f"- evidence_types: `{json.dumps(step.get('evidence_types', []), ensure_ascii=False)}`",
                f"- risk_summary: `{json.dumps(step.get('risk_summary', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- uncertainty_summary: `{json.dumps(step.get('uncertainty_summary', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- event_summary: `{json.dumps(step.get('event_summary', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- affordance_summary: `{json.dumps(step.get('affordance_summary', {}), ensure_ascii=False, sort_keys=True)}`",
                f"- object_metadata_summary: `{json.dumps(step.get('object_metadata_summary', {}), ensure_ascii=False, sort_keys=True)}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _step_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "step": record.get("step"),
        "replay_cases": record.get("replay_cases", []),
        "selected_action": record.get("selected_action", ""),
        "selected_actions": {
            "rast": record.get("rast_selected_action", ""),
            "object_list": record.get("object_list_selected_action", ""),
            "flat_feature": record.get("flat_feature_selected_action", ""),
            "scene_graph": record.get("scene_graph_selected_action", ""),
            "event_aware_rast": record.get("event_aware_rast_selected_action", ""),
            "uncertainty_aware_rast": record.get("uncertainty_aware_rast_selected_action", ""),
            "affordance_aware_rast": record.get("affordance_aware_rast_selected_action", ""),
        },
        "planner_decisions": {
            "rast": record.get("rast_decision", {}),
            "object_list": record.get("object_list_decision", {}),
            "flat_feature": record.get("flat_feature_decision", {}),
            "scene_graph": record.get("scene_graph_decision", {}),
            "event_aware_rast": record.get("event_aware_rast_decision", {}),
            "uncertainty_aware_rast": record.get("uncertainty_aware_rast_decision", {}),
            "affordance_aware_rast": record.get("affordance_aware_rast_decision", {}),
        },
        "reason_codes": {
            "rast": record.get("rast_reason_code", ""),
            "object_list": record.get("object_list_reason_code", ""),
            "flat_feature": record.get("flat_feature_reason_code", ""),
            "scene_graph": record.get("scene_graph_reason_code", ""),
            "event_aware_rast": record.get("event_aware_rast_reason_code", ""),
            "uncertainty_aware_rast": record.get("uncertainty_aware_rast_reason_code", ""),
            "affordance_aware_rast": record.get("affordance_aware_rast_reason_code", ""),
        },
        "trigger_tokens": {
            "rast": record.get("rast_trigger_token_ids", []),
            "event_aware_rast": record.get("event_aware_rast_trigger_token_ids", []),
            "uncertainty_aware_rast": record.get("uncertainty_aware_rast_trigger_token_ids", []),
            "affordance_aware_rast": record.get("affordance_aware_rast_trigger_token_ids", []),
        },
        "evidence_token_ids": record.get("evidence_token_ids", []),
        "evidence_types": record.get("evidence_types", []),
        "evidence_counts": {
            "risk": record.get("risk_evidence_count", 0),
            "uncertainty": record.get("uncertainty_evidence_count", 0),
            "event": record.get("event_evidence_count", 0),
            "decision": record.get("decision_evidence_count", 0),
        },
        "object_metadata_summary": {
            "metadata_snapshot_ref": record.get("metadata_snapshot_ref", ""),
            "min_object_distance": record.get("min_object_distance"),
            "object_list_count": record.get("object_list_count", 0),
        },
        "risk_summary": {
            "risk_token_count": record.get("risk_token_count", 0),
            "rast_trigger_risk_token_count": record.get("rast_trigger_risk_token_count", 0),
        },
        "uncertainty_summary": {
            "uncertainty_token_count": record.get("uncertainty_token_count", 0),
            "uncertainty_types": record.get("uncertainty_types", []),
            "high_uncertainty_count": record.get("high_uncertainty_count", 0),
        },
        "event_summary": {
            "event_token_count": record.get("event_token_count", 0),
            "event_types": record.get("event_types", []),
        },
        "affordance_summary": {
            "affordance_token_count": record.get("affordance_token_count", 0),
            "affordance_types": record.get("affordance_types", []),
        },
    }


def _has_high_risk_token(record: dict[str, Any]) -> bool:
    for token in record.get("tokens", []):
        if token.get("type") == "RiskToken" and token.get("severity") == "high":
            return True
    return False


def _has_high_uncertainty_token(record: dict[str, Any]) -> bool:
    for token in record.get("tokens", []):
        if token.get("type") == "UncertaintyToken" and token.get("level") == "high":
            return True
    return False


def _is_uncertainty_reason(reason_code: str) -> bool:
    return reason_code in {
        "high_uncertainty_near_path",
        "unknown_object_uncertainty",
        "partial_occlusion_uncertainty",
        "position_uncertainty_boundary",
        "low_sensor_agreement",
    }

"""Episode-level metric 계산 유틸리티입니다."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from rast.evaluation.records import StepLogRecord
from rast.schemas.metrics import EpisodeSummary, GoalSpec, StepMetrics


def step_metrics_from_record(
    record: StepLogRecord,
    *,
    collision_threshold: float,
    near_miss_threshold: float,
) -> StepMetrics:
    """StepLogRecord를 summary 계산용 StepMetrics로 변환합니다."""

    _validate_safety_thresholds(collision_threshold=collision_threshold, near_miss_threshold=near_miss_threshold)

    rast_action = record.rast_selected_action or record.selected_action
    object_list_action = record.object_list_selected_action or record.extra.get("object_list_action") or ""
    flat_feature_action = record.flat_feature_selected_action or record.extra.get("flat_feature_action") or ""

    rast_vs_object_list = record.rast_vs_object_list_disagreed
    if rast_vs_object_list is None:
        rast_vs_object_list = bool(object_list_action and rast_action != object_list_action)
    rast_vs_flat_feature = record.rast_vs_flat_feature_disagreed
    if rast_vs_flat_feature is None:
        rast_vs_flat_feature = bool(flat_feature_action and rast_action != flat_feature_action)
    object_list_vs_flat_feature = record.object_list_vs_flat_feature_disagreed
    if object_list_vs_flat_feature is None:
        object_list_vs_flat_feature = bool(
            object_list_action and flat_feature_action and object_list_action != flat_feature_action
        )

    baseline_disagreed = record.baseline_disagreed
    if baseline_disagreed is None:
        baseline_disagreed = rast_vs_object_list

    collision = record.collision
    near_miss = bool(record.near_miss)
    if record.min_object_distance is not None:
        collision = record.min_object_distance <= collision_threshold
        near_miss = collision_threshold < record.min_object_distance <= near_miss_threshold

    entity_count = record.entity_token_count or int(record.extra.get("entity_count", 0))
    risk_count = record.risk_token_count or int(record.extra.get("risk_count", 0))
    event_count = record.event_token_count or int(record.extra.get("event_token_count", 0))
    event_types = record.event_types or list(record.extra.get("event_types", []))
    total_count = record.total_token_count or len(record.tokens)
    object_count = record.object_list_count or int(record.extra.get("object_list_count", 0))
    flat_row_count = record.flat_feature_row_count or int(record.extra.get("flat_feature_row_count", 0))
    token_generation_latency = record.token_generation_latency_ms or record.latency.token_generation

    return StepMetrics(
        run_id=record.run_id,
        episode_id=record.episode_id,
        scene_id=record.scene_id,
        step=record.step,
        rast_selected_action=rast_action,
        object_list_selected_action=object_list_action,
        flat_feature_selected_action=flat_feature_action,
        rast_reason_code=_decision_reason(record, "rast"),
        object_list_reason_code=_decision_reason(record, "object_list"),
        flat_feature_reason_code=_decision_reason(record, "flat_feature"),
        rast_trigger_token_ids=list(record.rast_trigger_token_ids),
        rast_trigger_object_ids=list(record.rast_trigger_object_ids),
        object_list_trigger_object_ids=list(record.object_list_trigger_object_ids),
        flat_feature_trigger_object_ids=list(record.flat_feature_trigger_object_ids),
        baseline_disagreed=bool(baseline_disagreed),
        rast_vs_object_list_disagreed=bool(rast_vs_object_list),
        rast_vs_flat_feature_disagreed=bool(rast_vs_flat_feature),
        object_list_vs_flat_feature_disagreed=bool(object_list_vs_flat_feature),
        entity_token_count=entity_count,
        risk_token_count=risk_count,
        event_token_count=event_count,
        event_types=event_types,
        total_token_count=total_count,
        object_list_count=object_count,
        flat_feature_row_count=flat_row_count,
        near_miss=near_miss,
        collision=collision,
        min_object_distance=record.min_object_distance,
        token_generation_latency_ms=token_generation_latency,
        planning_latency_ms=record.latency.planning,
        total_latency_ms=record.latency.total,
        update_mode=record.update_mode if record.update_mode in {"full_recompute", "incremental"} else "full_recompute",
        changed_object_count=record.changed_object_count,
        affected_token_count=record.affected_token_count,
        full_recompute_latency_ms=record.full_recompute_latency_ms,
        incremental_update_latency_ms=record.incremental_update_latency_ms,
        incremental_update_benefit=record.incremental_update_benefit,
    )


def calculate_episode_summary(
    step_records: Iterable[StepLogRecord | StepMetrics],
    *,
    max_steps: int,
    collision_threshold: float,
    near_miss_threshold: float,
    goal: GoalSpec | None = None,
    goal_reached: bool = False,
    final_distance_to_goal: float | None = None,
) -> EpisodeSummary:
    """step record 목록에서 episode 단위 summary를 계산합니다."""

    if max_steps <= 0:
        raise ValueError("max_steps는 0보다 커야 합니다.")
    _validate_safety_thresholds(collision_threshold=collision_threshold, near_miss_threshold=near_miss_threshold)

    metrics = [
        record
        if isinstance(record, StepMetrics)
        else step_metrics_from_record(
            record,
            collision_threshold=collision_threshold,
            near_miss_threshold=near_miss_threshold,
        )
        for record in step_records
    ]
    if not metrics:
        return _empty_summary(max_steps=max_steps, goal=goal)

    total_latencies = [item.total_latency_ms for item in metrics]
    token_generation_latencies = [item.token_generation_latency_ms for item in metrics]
    planning_latencies = [item.planning_latency_ms for item in metrics]
    collision_count = sum(1 for item in metrics if item.collision)
    total_latency_avg = average(total_latencies)
    success_definition = (
        "goal_reached_and_no_collision"
        if goal is not None
        else "completed_steps_eq_max_steps_and_no_collision"
    )
    success = (goal_reached and collision_count == 0) if goal is not None else (len(metrics) >= max_steps and collision_count == 0)
    rast_vs_object_list_count = sum(1 for item in metrics if item.rast_vs_object_list_disagreed)

    return EpisodeSummary(
        run_id=metrics[0].run_id,
        episode_id=metrics[0].episode_id,
        scene_id=metrics[0].scene_id,
        max_steps=max_steps,
        completed_steps=len(metrics),
        success=success,
        success_definition=success_definition,
        goal_reached=goal_reached,
        final_distance_to_goal=final_distance_to_goal,
        collision_count=collision_count,
        near_miss_count=sum(1 for item in metrics if item.near_miss),
        rast_action_counts=dict(Counter(item.rast_selected_action for item in metrics)),
        object_list_action_counts=dict(Counter(item.object_list_selected_action for item in metrics)),
        flat_feature_action_counts=dict(Counter(item.flat_feature_selected_action for item in metrics if item.flat_feature_selected_action)),
        rast_reason_code_counts=dict(Counter(item.rast_reason_code for item in metrics if item.rast_reason_code)),
        object_list_reason_code_counts=dict(Counter(item.object_list_reason_code for item in metrics if item.object_list_reason_code)),
        flat_feature_reason_code_counts=dict(Counter(item.flat_feature_reason_code for item in metrics if item.flat_feature_reason_code)),
        rast_trigger_token_count_total=sum(len(item.rast_trigger_token_ids) for item in metrics),
        decision_trace_coverage=average(1.0 if _has_decision_trace(item) else 0.0 for item in metrics),
        baseline_disagreement_count=rast_vs_object_list_count,
        rast_vs_object_list_disagreement_count=rast_vs_object_list_count,
        rast_vs_flat_feature_disagreement_count=sum(1 for item in metrics if item.rast_vs_flat_feature_disagreed),
        object_list_vs_flat_feature_disagreement_count=sum(
            1 for item in metrics if item.object_list_vs_flat_feature_disagreed
        ),
        entity_token_count_total=sum(item.entity_token_count for item in metrics),
        risk_token_count_total=sum(item.risk_token_count for item in metrics),
        event_token_count_total=sum(item.event_token_count for item in metrics),
        event_token_count_avg=average(item.event_token_count for item in metrics),
        event_type_counts=dict(Counter(event_type for item in metrics for event_type in item.event_types)),
        flat_feature_row_count_total=sum(item.flat_feature_row_count for item in metrics),
        token_count_avg=average(item.total_token_count for item in metrics),
        object_count_avg=average(item.object_list_count for item in metrics),
        flat_feature_row_count_avg=average(item.flat_feature_row_count for item in metrics),
        latency_avg_ms=total_latency_avg,
        latency_p50_ms=percentile(total_latencies, 50),
        latency_p95_ms=percentile(total_latencies, 95),
        token_generation_latency_avg_ms=average(token_generation_latencies),
        planning_latency_avg_ms=average(planning_latencies),
        total_latency_avg_ms=total_latency_avg,
        risk_triggered_action_count=sum(
            1 for item in metrics if item.risk_token_count > 0 and item.rast_selected_action != "MoveAhead"
        ),
        update_mode=metrics[0].update_mode,
        changed_object_count_avg=average(item.changed_object_count for item in metrics),
        affected_token_count_avg=average(item.affected_token_count for item in metrics),
        full_recompute_latency_avg_ms=average(item.full_recompute_latency_ms for item in metrics),
        incremental_update_latency_avg_ms=average(item.incremental_update_latency_ms for item in metrics),
        incremental_update_benefit_avg=average(item.incremental_update_benefit for item in metrics),
    )


def average(values: Iterable[float | int]) -> float:
    """비어 있는 입력은 0.0으로 처리하는 평균 계산입니다."""

    items = [float(value) for value in values]
    if not items:
        return 0.0
    return sum(items) / len(items)


def percentile(values: Iterable[float | int], percent: float) -> float:
    """선형 보간 기반 percentile 계산입니다."""

    if percent < 0 or percent > 100:
        raise ValueError("percent는 0 이상 100 이하이어야 합니다.")
    items = sorted(float(value) for value in values)
    if not items:
        return 0.0
    if len(items) == 1:
        return items[0]
    rank = (len(items) - 1) * (percent / 100.0)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(items) - 1)
    fraction = rank - lower_index
    return items[lower_index] + (items[upper_index] - items[lower_index]) * fraction


def _empty_summary(*, max_steps: int, goal: GoalSpec | None) -> EpisodeSummary:
    """실행 step이 없어도 schema가 안정적으로 유지되게 합니다."""

    return EpisodeSummary(
        run_id="",
        episode_id="",
        scene_id="",
        max_steps=max_steps,
        completed_steps=0,
        success=False,
        success_definition=(
            "goal_reached_and_no_collision"
            if goal is not None
            else "completed_steps_eq_max_steps_and_no_collision"
        ),
        goal_reached=False,
        final_distance_to_goal=None,
        collision_count=0,
        near_miss_count=0,
        rast_action_counts={},
        object_list_action_counts={},
        flat_feature_action_counts={},
        rast_reason_code_counts={},
        object_list_reason_code_counts={},
        flat_feature_reason_code_counts={},
        rast_trigger_token_count_total=0,
        decision_trace_coverage=0.0,
        baseline_disagreement_count=0,
        rast_vs_object_list_disagreement_count=0,
        rast_vs_flat_feature_disagreement_count=0,
        object_list_vs_flat_feature_disagreement_count=0,
        entity_token_count_total=0,
        risk_token_count_total=0,
        event_token_count_total=0,
        event_token_count_avg=0.0,
        event_type_counts={},
        flat_feature_row_count_total=0,
        token_count_avg=0.0,
        object_count_avg=0.0,
        flat_feature_row_count_avg=0.0,
        latency_avg_ms=0.0,
        latency_p50_ms=0.0,
        latency_p95_ms=0.0,
        token_generation_latency_avg_ms=0.0,
        planning_latency_avg_ms=0.0,
        total_latency_avg_ms=0.0,
        risk_triggered_action_count=0,
        update_mode="full_recompute",
        changed_object_count_avg=0.0,
        affected_token_count_avg=0.0,
        full_recompute_latency_avg_ms=0.0,
        incremental_update_latency_avg_ms=0.0,
        incremental_update_benefit_avg=0.0,
    )


def _decision_reason(record: StepLogRecord, planner_prefix: str) -> str:
    """record field 또는 decision payload에서 planner reason_code를 꺼냅니다."""

    direct_value = getattr(record, f"{planner_prefix}_reason_code", "")
    if direct_value:
        return str(direct_value)
    decision = getattr(record, f"{planner_prefix}_decision", {}) or {}
    return str(decision.get("reason_code") or "")


def _has_decision_trace(item: StepMetrics) -> bool:
    """세 planner 모두 reason_code를 남긴 step을 trace-covered step으로 봅니다."""

    return bool(item.rast_reason_code and item.object_list_reason_code and item.flat_feature_reason_code)


def _validate_safety_thresholds(*, collision_threshold: float, near_miss_threshold: float) -> None:
    if collision_threshold <= 0:
        raise ValueError("collision_threshold는 0보다 커야 합니다.")
    if near_miss_threshold <= 0:
        raise ValueError("near_miss_threshold는 0보다 커야 합니다.")
    if collision_threshold >= near_miss_threshold:
        raise ValueError("collision_threshold는 near_miss_threshold보다 작아야 합니다.")

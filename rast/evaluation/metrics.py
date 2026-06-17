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
    scene_graph_action = record.scene_graph_selected_action or record.extra.get("scene_graph_action") or ""
    event_aware_action = record.event_aware_rast_selected_action or record.extra.get("event_aware_rast_action") or ""
    uncertainty_aware_action = (
        record.uncertainty_aware_rast_selected_action or record.extra.get("uncertainty_aware_rast_action") or ""
    )
    affordance_aware_action = (
        record.affordance_aware_rast_selected_action or record.extra.get("affordance_aware_rast_action") or ""
    )

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
    rast_vs_event_aware = record.rast_vs_event_aware_disagreed
    if rast_vs_event_aware is None:
        rast_vs_event_aware = bool(event_aware_action and rast_action != event_aware_action)
    rast_vs_uncertainty_aware = record.rast_vs_uncertainty_aware_disagreed
    if rast_vs_uncertainty_aware is None:
        rast_vs_uncertainty_aware = bool(uncertainty_aware_action and rast_action != uncertainty_aware_action)
    rast_vs_affordance_aware = record.rast_vs_affordance_aware_disagreed
    if rast_vs_affordance_aware is None:
        rast_vs_affordance_aware = bool(affordance_aware_action and rast_action != affordance_aware_action)
    rast_vs_scene_graph = record.rast_vs_scene_graph_disagreed
    if rast_vs_scene_graph is None:
        rast_vs_scene_graph = bool(scene_graph_action and rast_action != scene_graph_action)
    scene_graph_vs_flat_feature = record.scene_graph_vs_flat_feature_disagreed
    if scene_graph_vs_flat_feature is None:
        scene_graph_vs_flat_feature = bool(
            scene_graph_action and flat_feature_action and scene_graph_action != flat_feature_action
        )
    rast_reason = _decision_reason(record, "rast")
    object_list_reason = _decision_reason(record, "object_list")
    flat_feature_reason = _decision_reason(record, "flat_feature")
    scene_graph_reason = _decision_reason(record, "scene_graph")
    event_aware_reason = _decision_reason(record, "event_aware_rast")
    uncertainty_aware_reason = _decision_reason(record, "uncertainty_aware_rast")
    affordance_aware_reason = _decision_reason(record, "affordance_aware_rast")
    same_action_different_reason = record.rast_vs_scene_graph_same_action_different_reason
    if same_action_different_reason is None:
        same_action_different_reason = bool(
            scene_graph_action
            and rast_action == scene_graph_action
            and rast_reason
            and scene_graph_reason
            and rast_reason != scene_graph_reason
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
    relation_count = record.relation_token_count or int(record.extra.get("relation_token_count", 0))
    relation_types = record.relation_types or list(record.extra.get("relation_types", []))
    uncertainty_count = record.uncertainty_token_count or int(record.extra.get("uncertainty_token_count", 0))
    uncertainty_types = record.uncertainty_types or list(record.extra.get("uncertainty_types", []))
    high_uncertainty_count = record.high_uncertainty_count or int(record.extra.get("high_uncertainty_count", 0))
    affordance_count = record.affordance_token_count or int(record.extra.get("affordance_token_count", 0))
    affordance_types = record.affordance_types or list(record.extra.get("affordance_types", []))
    event_count = record.event_token_count or int(record.extra.get("event_token_count", 0))
    event_types = record.event_types or list(record.extra.get("event_types", []))
    evidence_count = record.evidence_token_count or int(record.extra.get("evidence_token_count", 0))
    evidence_types = record.evidence_types or list(record.extra.get("evidence_types", []))
    evidence_token_ids = record.evidence_token_ids or list(record.extra.get("evidence_token_ids", []))
    risk_evidence_count = record.risk_evidence_count or int(record.extra.get("risk_evidence_count", 0))
    uncertainty_evidence_count = record.uncertainty_evidence_count or int(record.extra.get("uncertainty_evidence_count", 0))
    event_evidence_count = record.event_evidence_count or int(record.extra.get("event_evidence_count", 0))
    decision_evidence_count = record.decision_evidence_count or int(record.extra.get("decision_evidence_count", 0))
    total_count = record.total_token_count or len(record.tokens)
    object_count = record.object_list_count or int(record.extra.get("object_list_count", 0))
    flat_row_count = record.flat_feature_row_count or int(record.extra.get("flat_feature_row_count", 0))
    scene_node_count = record.scene_graph_node_count or int(record.extra.get("scene_graph_node_count", 0))
    scene_edge_count = record.scene_graph_edge_count or int(record.extra.get("scene_graph_edge_count", 0))
    token_generation_latency = record.token_generation_latency_ms or record.latency.token_generation

    return StepMetrics(
        run_id=record.run_id,
        episode_id=record.episode_id,
        scene_id=record.scene_id,
        step=record.step,
        rast_selected_action=rast_action,
        object_list_selected_action=object_list_action,
        flat_feature_selected_action=flat_feature_action,
        scene_graph_selected_action=scene_graph_action,
        event_aware_rast_selected_action=event_aware_action,
        uncertainty_aware_rast_selected_action=uncertainty_aware_action,
        affordance_aware_rast_selected_action=affordance_aware_action,
        rast_reason_code=rast_reason,
        object_list_reason_code=object_list_reason,
        flat_feature_reason_code=flat_feature_reason,
        scene_graph_reason_code=scene_graph_reason,
        event_aware_rast_reason_code=event_aware_reason,
        uncertainty_aware_rast_reason_code=uncertainty_aware_reason,
        affordance_aware_rast_reason_code=affordance_aware_reason,
        rast_trigger_token_ids=list(record.rast_trigger_token_ids),
        rast_trigger_object_ids=list(record.rast_trigger_object_ids),
        object_list_trigger_object_ids=list(record.object_list_trigger_object_ids),
        flat_feature_trigger_object_ids=list(record.flat_feature_trigger_object_ids),
        scene_graph_trigger_object_ids=list(record.scene_graph_trigger_object_ids),
        event_aware_rast_trigger_event_types=list(record.event_aware_rast_trigger_event_types),
        event_aware_rast_trigger_token_ids=list(record.event_aware_rast_trigger_token_ids),
        uncertainty_aware_rast_trigger_token_ids=list(record.uncertainty_aware_rast_trigger_token_ids),
        affordance_aware_rast_trigger_token_ids=list(record.affordance_aware_rast_trigger_token_ids),
        baseline_disagreed=bool(baseline_disagreed),
        rast_vs_object_list_disagreed=bool(rast_vs_object_list),
        rast_vs_flat_feature_disagreed=bool(rast_vs_flat_feature),
        object_list_vs_flat_feature_disagreed=bool(object_list_vs_flat_feature),
        rast_vs_event_aware_disagreed=bool(rast_vs_event_aware),
        rast_vs_uncertainty_aware_disagreed=bool(rast_vs_uncertainty_aware),
        rast_vs_affordance_aware_disagreed=bool(rast_vs_affordance_aware),
        rast_vs_scene_graph_disagreed=bool(rast_vs_scene_graph),
        scene_graph_vs_flat_feature_disagreed=bool(scene_graph_vs_flat_feature),
        rast_vs_scene_graph_same_action_different_reason=bool(same_action_different_reason),
        entity_token_count=entity_count,
        risk_token_count=risk_count,
        relation_token_count=relation_count,
        relation_types=relation_types,
        uncertainty_token_count=uncertainty_count,
        uncertainty_types=uncertainty_types,
        high_uncertainty_count=high_uncertainty_count,
        affordance_token_count=affordance_count,
        affordance_types=affordance_types,
        event_token_count=event_count,
        event_types=event_types,
        evidence_token_count=evidence_count,
        evidence_types=evidence_types,
        evidence_token_ids=evidence_token_ids,
        risk_evidence_count=risk_evidence_count,
        uncertainty_evidence_count=uncertainty_evidence_count,
        event_evidence_count=event_evidence_count,
        decision_evidence_count=decision_evidence_count,
        total_token_count=total_count,
        object_list_count=object_count,
        flat_feature_row_count=flat_row_count,
        scene_graph_node_count=scene_node_count,
        scene_graph_edge_count=scene_edge_count,
        scene_graph_trigger_edge_count=record.scene_graph_trigger_edge_count
        or (0 if scene_graph_reason == "graph_no_blocking_move_ahead" else len(record.scene_graph_trigger_object_ids)),
        rast_trigger_risk_token_count=record.rast_trigger_risk_token_count or len(record.rast_trigger_token_ids),
        event_aware_trigger_event_count=record.event_aware_trigger_event_count
        or len(record.event_aware_rast_trigger_event_types),
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
        event_policy_variant=record.event_policy_variant,
        risk_threshold=record.risk_threshold,
        near_agent_relation_threshold=record.near_agent_relation_threshold,
        near_path_relation_threshold=record.near_path_relation_threshold,
        blocking_relation_threshold=record.blocking_relation_threshold,
        near_miss_threshold=record.near_miss_threshold,
        position_noise_std=record.position_noise_std,
        distance_noise_std=record.distance_noise_std,
        visibility_flip_prob=record.visibility_flip_prob,
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
    rast_scene_same_reason_count = sum(
        1 for item in metrics if item.rast_vs_scene_graph_same_action_different_reason
    )
    event_variant = metrics[0].event_policy_variant or "full"

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
        scene_graph_action_counts=dict(Counter(item.scene_graph_selected_action for item in metrics if item.scene_graph_selected_action)),
        event_aware_rast_action_counts=dict(
            Counter(item.event_aware_rast_selected_action for item in metrics if item.event_aware_rast_selected_action)
        ),
        uncertainty_aware_rast_action_counts=dict(
            Counter(
                item.uncertainty_aware_rast_selected_action
                for item in metrics
                if item.uncertainty_aware_rast_selected_action
            )
        ),
        affordance_aware_rast_action_counts=dict(
            Counter(
                item.affordance_aware_rast_selected_action
                for item in metrics
                if item.affordance_aware_rast_selected_action
            )
        ),
        rast_reason_code_counts=dict(Counter(item.rast_reason_code for item in metrics if item.rast_reason_code)),
        object_list_reason_code_counts=dict(Counter(item.object_list_reason_code for item in metrics if item.object_list_reason_code)),
        flat_feature_reason_code_counts=dict(Counter(item.flat_feature_reason_code for item in metrics if item.flat_feature_reason_code)),
        scene_graph_reason_code_counts=dict(Counter(item.scene_graph_reason_code for item in metrics if item.scene_graph_reason_code)),
        event_aware_rast_reason_code_counts=dict(
            Counter(item.event_aware_rast_reason_code for item in metrics if item.event_aware_rast_reason_code)
        ),
        uncertainty_aware_rast_reason_code_counts=dict(
            Counter(
                item.uncertainty_aware_rast_reason_code
                for item in metrics
                if item.uncertainty_aware_rast_reason_code
            )
        ),
        affordance_aware_rast_reason_code_counts=dict(
            Counter(
                item.affordance_aware_rast_reason_code
                for item in metrics
                if item.affordance_aware_rast_reason_code
            )
        ),
        event_policy_variant_action_counts={
            event_variant: dict(
                Counter(item.event_aware_rast_selected_action for item in metrics if item.event_aware_rast_selected_action)
            )
        },
        event_policy_variant_reason_code_counts={
            event_variant: dict(
                Counter(item.event_aware_rast_reason_code for item in metrics if item.event_aware_rast_reason_code)
            )
        },
        rast_trigger_token_count_total=sum(len(item.rast_trigger_token_ids) for item in metrics),
        decision_trace_coverage=average(1.0 if _has_decision_trace(item) else 0.0 for item in metrics),
        baseline_disagreement_count=rast_vs_object_list_count,
        rast_vs_object_list_disagreement_count=rast_vs_object_list_count,
        rast_vs_flat_feature_disagreement_count=sum(1 for item in metrics if item.rast_vs_flat_feature_disagreed),
        object_list_vs_flat_feature_disagreement_count=sum(
            1 for item in metrics if item.object_list_vs_flat_feature_disagreed
        ),
        rast_vs_event_aware_disagreement_count=sum(1 for item in metrics if item.rast_vs_event_aware_disagreed),
        rast_vs_uncertainty_aware_disagreement_count=sum(
            1 for item in metrics if item.rast_vs_uncertainty_aware_disagreed
        ),
        rast_vs_affordance_aware_disagreement_count=sum(
            1 for item in metrics if item.rast_vs_affordance_aware_disagreed
        ),
        rast_vs_scene_graph_disagreement_count=sum(1 for item in metrics if item.rast_vs_scene_graph_disagreed),
        scene_graph_vs_flat_feature_disagreement_count=sum(
            1 for item in metrics if item.scene_graph_vs_flat_feature_disagreed
        ),
        rast_vs_scene_graph_same_action_different_reason_count=rast_scene_same_reason_count,
        rast_vs_scene_graph_same_action_different_reason_rate=rast_scene_same_reason_count / len(metrics),
        scene_graph_trigger_edge_count=sum(item.scene_graph_trigger_edge_count for item in metrics),
        rast_trigger_risk_token_count=sum(item.rast_trigger_risk_token_count for item in metrics),
        event_aware_trigger_event_count=sum(item.event_aware_trigger_event_count for item in metrics),
        event_triggered_action_count=sum(1 for item in metrics if _is_event_triggered_reason(item.event_aware_rast_reason_code)),
        uncertainty_triggered_action_count=sum(
            1 for item in metrics if _is_uncertainty_triggered_reason(item.uncertainty_aware_rast_reason_code)
        ),
        affordance_triggered_action_count=sum(
            1 for item in metrics if _is_affordance_triggered_reason(item.affordance_aware_rast_reason_code)
        ),
        event_aware_decision_trace_coverage=average(
            1.0 if item.event_aware_rast_selected_action and item.event_aware_rast_reason_code else 0.0
            for item in metrics
        ),
        uncertainty_aware_decision_trace_coverage=average(
            1.0 if item.uncertainty_aware_rast_selected_action and item.uncertainty_aware_rast_reason_code else 0.0
            for item in metrics
        ),
        affordance_aware_decision_trace_coverage=average(
            1.0 if item.affordance_aware_rast_selected_action and item.affordance_aware_rast_reason_code else 0.0
            for item in metrics
        ),
        scene_graph_decision_trace_coverage=average(
            1.0 if item.scene_graph_selected_action and item.scene_graph_reason_code else 0.0
            for item in metrics
        ),
        entity_token_count_total=sum(item.entity_token_count for item in metrics),
        risk_token_count_total=sum(item.risk_token_count for item in metrics),
        relation_token_count_total=sum(item.relation_token_count for item in metrics),
        relation_token_count_avg=average(item.relation_token_count for item in metrics),
        relation_type_counts=dict(Counter(relation_type for item in metrics for relation_type in item.relation_types)),
        uncertainty_token_count_total=sum(item.uncertainty_token_count for item in metrics),
        uncertainty_token_count_avg=average(item.uncertainty_token_count for item in metrics),
        uncertainty_type_counts=dict(
            Counter(uncertainty_type for item in metrics for uncertainty_type in item.uncertainty_types)
        ),
        high_uncertainty_count_total=sum(item.high_uncertainty_count for item in metrics),
        high_uncertainty_count_avg=average(item.high_uncertainty_count for item in metrics),
        affordance_token_count_total=sum(item.affordance_token_count for item in metrics),
        affordance_token_count_avg=average(item.affordance_token_count for item in metrics),
        affordance_type_counts=dict(Counter(affordance_type for item in metrics for affordance_type in item.affordance_types)),
        event_token_count_total=sum(item.event_token_count for item in metrics),
        event_token_count_avg=average(item.event_token_count for item in metrics),
        event_type_counts=dict(Counter(event_type for item in metrics for event_type in item.event_types)),
        evidence_token_count_total=sum(item.evidence_token_count for item in metrics),
        evidence_token_count_avg=average(item.evidence_token_count for item in metrics),
        evidence_type_counts=dict(
            Counter(evidence_type for item in metrics for evidence_type in item.evidence_types)
        ),
        risk_evidence_count_total=sum(item.risk_evidence_count for item in metrics),
        uncertainty_evidence_count_total=sum(item.uncertainty_evidence_count for item in metrics),
        event_evidence_count_total=sum(item.event_evidence_count for item in metrics),
        decision_evidence_count_total=sum(item.decision_evidence_count for item in metrics),
        decision_evidence_coverage=average(
            1.0 if item.decision_evidence_count > 0 else 0.0 for item in metrics
        ),
        flat_feature_row_count_total=sum(item.flat_feature_row_count for item in metrics),
        token_count_avg=average(item.total_token_count for item in metrics),
        object_count_avg=average(item.object_list_count for item in metrics),
        flat_feature_row_count_avg=average(item.flat_feature_row_count for item in metrics),
        scene_graph_node_count_avg=average(item.scene_graph_node_count for item in metrics),
        scene_graph_edge_count_avg=average(item.scene_graph_edge_count for item in metrics),
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
        event_policy_variant=event_variant,
        risk_threshold=metrics[0].risk_threshold,
        near_agent_relation_threshold=metrics[0].near_agent_relation_threshold,
        near_path_relation_threshold=metrics[0].near_path_relation_threshold,
        blocking_relation_threshold=metrics[0].blocking_relation_threshold,
        near_miss_threshold=metrics[0].near_miss_threshold,
        position_noise_std=metrics[0].position_noise_std,
        distance_noise_std=metrics[0].distance_noise_std,
        visibility_flip_prob=metrics[0].visibility_flip_prob,
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
        scene_graph_action_counts={},
        event_aware_rast_action_counts={},
        uncertainty_aware_rast_action_counts={},
        affordance_aware_rast_action_counts={},
        rast_reason_code_counts={},
        object_list_reason_code_counts={},
        flat_feature_reason_code_counts={},
        scene_graph_reason_code_counts={},
        event_aware_rast_reason_code_counts={},
        uncertainty_aware_rast_reason_code_counts={},
        affordance_aware_rast_reason_code_counts={},
        event_policy_variant_action_counts={},
        event_policy_variant_reason_code_counts={},
        rast_trigger_token_count_total=0,
        decision_trace_coverage=0.0,
        baseline_disagreement_count=0,
        rast_vs_object_list_disagreement_count=0,
        rast_vs_flat_feature_disagreement_count=0,
        object_list_vs_flat_feature_disagreement_count=0,
        rast_vs_event_aware_disagreement_count=0,
        rast_vs_uncertainty_aware_disagreement_count=0,
        rast_vs_affordance_aware_disagreement_count=0,
        rast_vs_scene_graph_disagreement_count=0,
        scene_graph_vs_flat_feature_disagreement_count=0,
        rast_vs_scene_graph_same_action_different_reason_count=0,
        rast_vs_scene_graph_same_action_different_reason_rate=0.0,
        scene_graph_trigger_edge_count=0,
        rast_trigger_risk_token_count=0,
        event_aware_trigger_event_count=0,
        event_triggered_action_count=0,
        uncertainty_triggered_action_count=0,
        affordance_triggered_action_count=0,
        event_aware_decision_trace_coverage=0.0,
        uncertainty_aware_decision_trace_coverage=0.0,
        affordance_aware_decision_trace_coverage=0.0,
        scene_graph_decision_trace_coverage=0.0,
        entity_token_count_total=0,
        risk_token_count_total=0,
        relation_token_count_total=0,
        relation_token_count_avg=0.0,
        relation_type_counts={},
        uncertainty_token_count_total=0,
        uncertainty_token_count_avg=0.0,
        uncertainty_type_counts={},
        high_uncertainty_count_total=0,
        high_uncertainty_count_avg=0.0,
        affordance_token_count_total=0,
        affordance_token_count_avg=0.0,
        affordance_type_counts={},
        event_token_count_total=0,
        event_token_count_avg=0.0,
        event_type_counts={},
        evidence_token_count_total=0,
        evidence_token_count_avg=0.0,
        evidence_type_counts={},
        risk_evidence_count_total=0,
        uncertainty_evidence_count_total=0,
        event_evidence_count_total=0,
        decision_evidence_count_total=0,
        decision_evidence_coverage=0.0,
        flat_feature_row_count_total=0,
        token_count_avg=0.0,
        object_count_avg=0.0,
        flat_feature_row_count_avg=0.0,
        scene_graph_node_count_avg=0.0,
        scene_graph_edge_count_avg=0.0,
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
        event_policy_variant="full",
        risk_threshold=None,
        near_agent_relation_threshold=None,
        near_path_relation_threshold=None,
        blocking_relation_threshold=None,
        near_miss_threshold=None,
        position_noise_std=0.0,
        distance_noise_std=0.0,
        visibility_flip_prob=0.0,
    )


def _decision_reason(record: StepLogRecord, planner_prefix: str) -> str:
    """record field 또는 decision payload에서 planner reason_code를 꺼냅니다."""

    direct_value = getattr(record, f"{planner_prefix}_reason_code", "")
    if direct_value:
        return str(direct_value)
    decision = getattr(record, f"{planner_prefix}_decision", {}) or {}
    return str(decision.get("reason_code") or "")


def _has_decision_trace(item: StepMetrics) -> bool:
    """기존 core planner 세 가지가 모두 reason_code를 갖는지 확인합니다."""

    return bool(item.rast_reason_code and item.object_list_reason_code and item.flat_feature_reason_code)


def _is_event_triggered_reason(reason_code: str) -> bool:
    """Event-aware planner의 event 기반 reason_code 여부를 판정합니다."""

    return reason_code.startswith("event_")


def _is_uncertainty_triggered_reason(reason_code: str) -> bool:
    """Uncertainty-aware planner의 uncertainty 기반 reason_code 여부를 판정합니다."""

    return reason_code in {
        "high_uncertainty_near_path",
        "unknown_object_uncertainty",
        "partial_occlusion_uncertainty",
        "position_uncertainty_boundary",
        "low_sensor_agreement",
    }


def _is_affordance_triggered_reason(reason_code: str) -> bool:
    """Affordance-aware planner??affordance 湲곕컲 reason_code ?щ?瑜??먯젙?⑸땲??"""

    return reason_code.startswith("affordance_")


def _validate_safety_thresholds(*, collision_threshold: float, near_miss_threshold: float) -> None:
    if collision_threshold <= 0:
        raise ValueError("collision_threshold는 0보다 커야 합니다.")
    if near_miss_threshold <= 0:
        raise ValueError("near_miss_threshold는 0보다 커야 합니다.")
    if collision_threshold >= near_miss_threshold:
        raise ValueError("collision_threshold는 near_miss_threshold보다 작아야 합니다.")

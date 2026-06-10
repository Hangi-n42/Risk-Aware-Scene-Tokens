import pytest

from rast.evaluation.metrics import calculate_episode_summary, step_metrics_from_record
from rast.evaluation.records import StepLogRecord
from rast.schemas.common import Vector3
from rast.schemas.latency import LatencyRecord
from rast.schemas.metrics import GoalSpec


def make_record(
    *,
    step: int,
    total_latency: float,
    rast_action: str,
    object_list_action: str,
    flat_feature_action: str | None = None,
    min_object_distance: float | None = None,
    near_miss: bool | None = None,
    event_token_count: int = 0,
    event_types: list[str] | None = None,
    update_mode: str = "full_recompute",
    changed_object_count: int = 0,
    affected_token_count: int = 0,
    full_recompute_latency_ms: float = 0.0,
    incremental_update_latency_ms: float = 0.0,
    incremental_update_benefit: float = 0.0,
    rast_reason_code: str | None = None,
    object_list_reason_code: str | None = None,
    flat_feature_reason_code: str | None = None,
) -> StepLogRecord:
    flat_action = flat_feature_action or rast_action
    rast_reason = rast_reason_code or ("no_risk_move_ahead" if rast_action == "MoveAhead" else "high_risk_token")
    object_reason = object_list_reason_code or (
        "no_near_object_move_ahead" if object_list_action == "MoveAhead" else "near_object_distance"
    )
    flat_reason = flat_feature_reason_code or (
        "no_risk_scalar_move_ahead" if flat_action == "MoveAhead" else "within_risk_threshold"
    )
    latency = LatencyRecord(
        observation=0.0,
        perception=0.0,
        token_generation=total_latency * 0.2,
        planning=total_latency * 0.3,
        action=total_latency * 0.5,
        total=total_latency,
    )
    return StepLogRecord.from_parts(
        run_id="metrics_run",
        episode_id="episode_001",
        scene_id="WindowsRoom1",
        step=step,
        baseline_type="rast",
        latency=latency,
        selected_action=rast_action,
        rast_selected_action=rast_action,
        object_list_selected_action=object_list_action,
        flat_feature_selected_action=flat_action,
        rast_reason_code=rast_reason,
        object_list_reason_code=object_reason,
        flat_feature_reason_code=flat_reason,
        rast_trigger_token_ids=["risk-token-1"] if rast_action != "MoveAhead" else [],
        rast_trigger_object_ids=["object-1"] if rast_action != "MoveAhead" else [],
        object_list_trigger_object_ids=["object-1"] if object_list_action != "MoveAhead" else [],
        flat_feature_trigger_object_ids=["object-1"] if flat_action != "MoveAhead" else [],
        baseline_disagreed=rast_action != object_list_action,
        rast_vs_object_list_disagreed=rast_action != object_list_action,
        rast_vs_flat_feature_disagreed=rast_action != flat_action,
        object_list_vs_flat_feature_disagreed=object_list_action != flat_action,
        entity_token_count=4,
        risk_token_count=1,
        event_token_count=event_token_count,
        event_types=event_types or [],
        update_mode=update_mode,
        changed_object_count=changed_object_count,
        affected_token_count=affected_token_count,
        full_recompute_latency_ms=full_recompute_latency_ms,
        incremental_update_latency_ms=incremental_update_latency_ms,
        incremental_update_benefit=incremental_update_benefit,
        token_generation_latency_ms=latency.token_generation,
        total_token_count=5 + event_token_count,
        object_list_count=4,
        flat_feature_row_count=4,
        near_miss=near_miss,
        collision=False,
        min_object_distance=min_object_distance,
        phase="windows_metadata_sim_oracle",
    )


def test_episode_summary_calculates_latency_percentiles_and_counts() -> None:
    records = [
        make_record(step=0, total_latency=10.0, rast_action="MoveAhead", object_list_action="MoveAhead"),
        make_record(
            step=1,
            total_latency=20.0,
            rast_action="RotateRight",
            object_list_action="MoveAhead",
            flat_feature_action="MoveAhead",
        ),
        make_record(step=2, total_latency=30.0, rast_action="RotateRight", object_list_action="RotateRight"),
        make_record(
            step=3,
            total_latency=40.0,
            rast_action="Stop",
            object_list_action="RotateRight",
            flat_feature_action="MoveAhead",
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=4,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.success is True
    assert summary.success_definition == "completed_steps_eq_max_steps_and_no_collision"
    assert summary.completed_steps == 4
    assert summary.baseline_disagreement_count == 2
    assert summary.rast_vs_object_list_disagreement_count == 2
    assert summary.rast_vs_flat_feature_disagreement_count == 2
    assert summary.object_list_vs_flat_feature_disagreement_count == 1
    assert summary.flat_feature_action_counts == {"MoveAhead": 3, "RotateRight": 1}
    assert summary.entity_token_count_total == 16
    assert summary.risk_token_count_total == 4
    assert summary.event_token_count_total == 0
    assert summary.event_type_counts == {}
    assert summary.flat_feature_row_count_total == 16
    assert summary.token_count_avg == 5.0
    assert summary.object_count_avg == 4.0
    assert summary.flat_feature_row_count_avg == 4.0
    assert summary.latency_avg_ms == 25.0
    assert summary.latency_p50_ms == 25.0
    assert summary.latency_p95_ms == pytest.approx(38.5)
    assert summary.token_generation_latency_avg_ms == 5.0
    assert summary.planning_latency_avg_ms == 7.5
    assert summary.total_latency_avg_ms == 25.0
    assert summary.risk_triggered_action_count == 3
    assert summary.rast_reason_code_counts == {"no_risk_move_ahead": 1, "high_risk_token": 3}
    assert summary.object_list_reason_code_counts == {"no_near_object_move_ahead": 2, "near_object_distance": 2}
    assert summary.flat_feature_reason_code_counts == {"no_risk_scalar_move_ahead": 3, "within_risk_threshold": 1}
    assert summary.rast_trigger_token_count_total == 3
    assert summary.decision_trace_coverage == 1.0
    assert summary.update_mode == "full_recompute"
    assert summary.changed_object_count_avg == 0.0
    assert summary.incremental_update_benefit_avg == 0.0


def test_episode_summary_counts_event_tokens_and_types() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
        ),
        make_record(
            step=1,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            event_token_count=2,
            event_types=["object_appeared", "risk_changed"],
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=2,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.event_token_count_total == 2
    assert summary.event_token_count_avg == 1.0
    assert summary.event_type_counts == {"object_appeared": 1, "risk_changed": 1}


def test_episode_summary_calculates_incremental_update_fields() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            update_mode="incremental",
            changed_object_count=2,
            affected_token_count=4,
            full_recompute_latency_ms=1.0,
            incremental_update_latency_ms=0.5,
            incremental_update_benefit=0.5,
        ),
        make_record(
            step=1,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            update_mode="incremental",
            changed_object_count=0,
            affected_token_count=0,
            full_recompute_latency_ms=1.0,
            incremental_update_latency_ms=1.5,
            incremental_update_benefit=-0.5,
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=2,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.update_mode == "incremental"
    assert summary.changed_object_count_avg == 1.0
    assert summary.affected_token_count_avg == 2.0
    assert summary.full_recompute_latency_avg_ms == 1.0
    assert summary.incremental_update_latency_avg_ms == 1.0
    assert summary.incremental_update_benefit_avg == 0.0


def test_step_metrics_calculates_near_miss_from_distance_threshold() -> None:
    record = make_record(
        step=0,
        total_latency=10.0,
        rast_action="RotateRight",
        object_list_action="MoveAhead",
        min_object_distance=0.75,
        near_miss=None,
    )

    metrics = step_metrics_from_record(record, collision_threshold=0.2, near_miss_threshold=1.0)

    assert metrics.near_miss is True
    assert metrics.baseline_disagreed is True
    assert metrics.rast_reason_code == "high_risk_token"


def test_collision_and_near_miss_thresholds_are_separated() -> None:
    collision_record = make_record(
        step=0,
        total_latency=10.0,
        rast_action="RotateRight",
        object_list_action="RotateRight",
        min_object_distance=0.15,
        near_miss=None,
    )
    near_miss_record = make_record(
        step=1,
        total_latency=10.0,
        rast_action="RotateRight",
        object_list_action="RotateRight",
        min_object_distance=0.5,
        near_miss=None,
    )

    collision_metrics = step_metrics_from_record(
        collision_record,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )
    near_miss_metrics = step_metrics_from_record(
        near_miss_record,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert collision_metrics.collision is True
    assert collision_metrics.near_miss is False
    assert near_miss_metrics.collision is False
    assert near_miss_metrics.near_miss is True


def test_goal_reached_success_overrides_max_step_completion() -> None:
    records = [
        make_record(step=0, total_latency=10.0, rast_action="MoveAhead", object_list_action="MoveAhead"),
        make_record(step=1, total_latency=10.0, rast_action="MoveAhead", object_list_action="MoveAhead"),
    ]
    goal = GoalSpec(
        goal_type="reach_position",
        target_position=Vector3(x=0.0, y=0.0, z=1.0),
        success_distance=0.3,
    )

    summary = calculate_episode_summary(
        records,
        max_steps=10,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
        goal=goal,
        goal_reached=True,
        final_distance_to_goal=0.2,
    )

    assert summary.success is True
    assert summary.success_definition == "goal_reached_and_no_collision"
    assert summary.goal_reached is True
    assert summary.final_distance_to_goal == 0.2

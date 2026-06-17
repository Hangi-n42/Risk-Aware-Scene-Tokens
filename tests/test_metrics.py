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
    scene_graph_action: str | None = None,
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
    scene_graph_reason_code: str | None = None,
    event_aware_action: str | None = None,
    event_aware_reason_code: str | None = None,
    event_aware_trigger_event_types: list[str] | None = None,
    uncertainty_aware_action: str | None = None,
    uncertainty_aware_reason_code: str | None = None,
    affordance_aware_action: str | None = None,
    affordance_aware_reason_code: str | None = None,
    affordance_token_count: int = 0,
    affordance_types: list[str] | None = None,
    uncertainty_token_count: int = 0,
    uncertainty_types: list[str] | None = None,
    high_uncertainty_count: int = 0,
    event_policy_variant: str = "full",
    risk_threshold: float | None = 1.5,
    near_miss_threshold: float | None = 1.0,
    position_noise_std: float = 0.0,
    distance_noise_std: float = 0.0,
    visibility_flip_prob: float = 0.0,
    evidence_token_count: int = 0,
    evidence_types: list[str] | None = None,
    risk_evidence_count: int = 0,
    uncertainty_evidence_count: int = 0,
    event_evidence_count: int = 0,
    decision_evidence_count: int = 0,
) -> StepLogRecord:
    flat_action = flat_feature_action or rast_action
    graph_action = scene_graph_action or rast_action
    event_action = event_aware_action or rast_action
    uncertainty_action = uncertainty_aware_action or rast_action
    affordance_action = affordance_aware_action or rast_action
    rast_reason = rast_reason_code or ("no_risk_move_ahead" if rast_action == "MoveAhead" else "high_risk_token")
    object_reason = object_list_reason_code or (
        "no_near_object_move_ahead" if object_list_action == "MoveAhead" else "near_object_distance"
    )
    flat_reason = flat_feature_reason_code or (
        "no_risk_scalar_move_ahead" if flat_action == "MoveAhead" else "within_risk_threshold"
    )
    graph_reason = scene_graph_reason_code or (
        "graph_no_blocking_move_ahead" if graph_action == "MoveAhead" else "graph_blocking_path"
    )
    event_reason = event_aware_reason_code or (
        "fallback_no_risk_move_ahead" if event_action == "MoveAhead" else "fallback_risk_token_present"
    )
    uncertainty_reason = uncertainty_aware_reason_code or (
        "fallback_no_risk_move_ahead" if uncertainty_action == "MoveAhead" else "fallback_risk_token_present"
    )
    affordance_reason = affordance_aware_reason_code or (
        "fallback_no_risk_move_ahead" if affordance_action == "MoveAhead" else "fallback_risk_token_present"
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
        scene_graph_selected_action=graph_action,
        event_aware_rast_selected_action=event_action,
        uncertainty_aware_rast_selected_action=uncertainty_action,
        affordance_aware_rast_selected_action=affordance_action,
        rast_reason_code=rast_reason,
        object_list_reason_code=object_reason,
        flat_feature_reason_code=flat_reason,
        scene_graph_reason_code=graph_reason,
        event_aware_rast_reason_code=event_reason,
        uncertainty_aware_rast_reason_code=uncertainty_reason,
        affordance_aware_rast_reason_code=affordance_reason,
        rast_trigger_token_ids=["risk-token-1"] if rast_action != "MoveAhead" else [],
        rast_trigger_object_ids=["object-1"] if rast_action != "MoveAhead" else [],
        object_list_trigger_object_ids=["object-1"] if object_list_action != "MoveAhead" else [],
        flat_feature_trigger_object_ids=["object-1"] if flat_action != "MoveAhead" else [],
        scene_graph_trigger_object_ids=["object-1"] if graph_action != "MoveAhead" else [],
        event_aware_rast_trigger_event_types=event_aware_trigger_event_types or [],
        event_aware_rast_trigger_token_ids=["event-token-1"] if event_reason.startswith("event_") else [],
        uncertainty_aware_rast_trigger_token_ids=["unc-token-1"] if "uncertainty" in uncertainty_reason else [],
        affordance_aware_rast_trigger_token_ids=["aff-token-1"] if affordance_reason.startswith("affordance_") else [],
        event_policy_variant=event_policy_variant,
        risk_threshold=risk_threshold,
        near_miss_threshold=near_miss_threshold,
        position_noise_std=position_noise_std,
        distance_noise_std=distance_noise_std,
        visibility_flip_prob=visibility_flip_prob,
        baseline_disagreed=rast_action != object_list_action,
        rast_vs_object_list_disagreed=rast_action != object_list_action,
        rast_vs_flat_feature_disagreed=rast_action != flat_action,
        object_list_vs_flat_feature_disagreed=object_list_action != flat_action,
        rast_vs_event_aware_disagreed=rast_action != event_action,
        rast_vs_uncertainty_aware_disagreed=rast_action != uncertainty_action,
        rast_vs_affordance_aware_disagreed=rast_action != affordance_action,
        rast_vs_scene_graph_disagreed=rast_action != graph_action,
        scene_graph_vs_flat_feature_disagreed=graph_action != flat_action,
        entity_token_count=4,
        risk_token_count=1,
        relation_token_count=2,
        relation_types=["near_agent", "blocking_path"] if graph_action != "MoveAhead" else ["near_path", "target_reachable"],
        uncertainty_token_count=uncertainty_token_count,
        uncertainty_types=uncertainty_types or [],
        high_uncertainty_count=high_uncertainty_count,
        affordance_token_count=affordance_token_count,
        affordance_types=affordance_types or [],
        event_token_count=event_token_count,
        event_types=event_types or [],
        evidence_token_count=evidence_token_count,
        evidence_types=evidence_types or [],
        evidence_token_ids=[f"ev-{step}-{index}" for index in range(evidence_token_count)],
        risk_evidence_count=risk_evidence_count,
        uncertainty_evidence_count=uncertainty_evidence_count,
        event_evidence_count=event_evidence_count,
        decision_evidence_count=decision_evidence_count,
        update_mode=update_mode,
        changed_object_count=changed_object_count,
        affected_token_count=affected_token_count,
        full_recompute_latency_ms=full_recompute_latency_ms,
        incremental_update_latency_ms=incremental_update_latency_ms,
        incremental_update_benefit=incremental_update_benefit,
        token_generation_latency_ms=latency.token_generation,
        total_token_count=5 + event_token_count + uncertainty_token_count + affordance_token_count,
        object_list_count=4,
        flat_feature_row_count=4,
        scene_graph_node_count=5,
        scene_graph_edge_count=2,
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
    assert summary.rast_vs_event_aware_disagreement_count == 0
    assert summary.rast_vs_uncertainty_aware_disagreement_count == 0
    assert summary.rast_vs_affordance_aware_disagreement_count == 0
    assert summary.rast_vs_scene_graph_disagreement_count == 0
    assert summary.scene_graph_vs_flat_feature_disagreement_count == 2
    assert summary.rast_vs_scene_graph_same_action_different_reason_count == 4
    assert summary.rast_vs_scene_graph_same_action_different_reason_rate == 1.0
    assert summary.scene_graph_trigger_edge_count == 3
    assert summary.rast_trigger_risk_token_count == 3
    assert summary.event_aware_trigger_event_count == 0
    assert summary.flat_feature_action_counts == {"MoveAhead": 3, "RotateRight": 1}
    assert summary.scene_graph_action_counts == {"MoveAhead": 1, "RotateRight": 2, "Stop": 1}
    assert summary.event_aware_rast_action_counts == {"MoveAhead": 1, "RotateRight": 2, "Stop": 1}
    assert summary.uncertainty_aware_rast_action_counts == {"MoveAhead": 1, "RotateRight": 2, "Stop": 1}
    assert summary.affordance_aware_rast_action_counts == {"MoveAhead": 1, "RotateRight": 2, "Stop": 1}
    assert summary.entity_token_count_total == 16
    assert summary.risk_token_count_total == 4
    assert summary.relation_token_count_total == 8
    assert summary.relation_token_count_avg == 2.0
    assert summary.relation_type_counts == {
        "near_path": 1,
        "target_reachable": 1,
        "near_agent": 3,
        "blocking_path": 3,
    }
    assert summary.event_token_count_total == 0
    assert summary.event_type_counts == {}
    assert summary.uncertainty_token_count_total == 0
    assert summary.uncertainty_type_counts == {}
    assert summary.high_uncertainty_count_total == 0
    assert summary.flat_feature_row_count_total == 16
    assert summary.token_count_avg == 5.0
    assert summary.object_count_avg == 4.0
    assert summary.flat_feature_row_count_avg == 4.0
    assert summary.scene_graph_node_count_avg == 5.0
    assert summary.scene_graph_edge_count_avg == 2.0
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
    assert summary.scene_graph_reason_code_counts == {"graph_no_blocking_move_ahead": 1, "graph_blocking_path": 3}
    assert summary.event_aware_rast_reason_code_counts == {
        "fallback_no_risk_move_ahead": 1,
        "fallback_risk_token_present": 3,
    }
    assert summary.uncertainty_aware_rast_reason_code_counts == {
        "fallback_no_risk_move_ahead": 1,
        "fallback_risk_token_present": 3,
    }
    assert summary.affordance_aware_rast_reason_code_counts == {
        "fallback_no_risk_move_ahead": 1,
        "fallback_risk_token_present": 3,
    }
    assert summary.event_policy_variant == "full"
    assert summary.risk_threshold == 1.5
    assert summary.near_miss_threshold == 1.0
    assert summary.position_noise_std == 0.0
    assert summary.distance_noise_std == 0.0
    assert summary.visibility_flip_prob == 0.0
    assert summary.event_policy_variant_action_counts == {"full": {"MoveAhead": 1, "RotateRight": 2, "Stop": 1}}
    assert summary.event_policy_variant_reason_code_counts == {
        "full": {"fallback_no_risk_move_ahead": 1, "fallback_risk_token_present": 3}
    }
    assert summary.rast_trigger_token_count_total == 3
    assert summary.decision_trace_coverage == 1.0
    assert summary.event_triggered_action_count == 0
    assert summary.event_aware_decision_trace_coverage == 1.0
    assert summary.uncertainty_triggered_action_count == 0
    assert summary.uncertainty_aware_decision_trace_coverage == 1.0
    assert summary.affordance_triggered_action_count == 0
    assert summary.affordance_aware_decision_trace_coverage == 1.0
    assert summary.scene_graph_decision_trace_coverage == 1.0
    assert summary.update_mode == "full_recompute"
    assert summary.changed_object_count_avg == 0.0
    assert summary.incremental_update_benefit_avg == 0.0


def test_episode_summary_counts_same_action_different_reason_for_scene_graph() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            scene_graph_action="MoveAhead",
            rast_reason_code="no_risk_move_ahead",
            scene_graph_reason_code="graph_no_blocking_move_ahead",
        ),
        make_record(
            step=1,
            total_latency=10.0,
            rast_action="RotateRight",
            object_list_action="RotateRight",
            scene_graph_action="MoveAhead",
            rast_reason_code="risk_token_present",
            scene_graph_reason_code="graph_no_blocking_move_ahead",
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=2,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.rast_vs_scene_graph_disagreement_count == 1
    assert summary.rast_vs_scene_graph_same_action_different_reason_count == 1
    assert summary.rast_vs_scene_graph_same_action_different_reason_rate == 0.5


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


def test_episode_summary_counts_evidence_tokens_and_decision_coverage() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="RotateRight",
            object_list_action="MoveAhead",
            evidence_token_count=3,
            evidence_types=["risk_feature", "planner_decision", "planner_decision"],
            risk_evidence_count=1,
            decision_evidence_count=2,
        ),
        make_record(
            step=1,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            evidence_token_count=2,
            evidence_types=["uncertainty_feature", "event_diff"],
            uncertainty_evidence_count=1,
            event_evidence_count=1,
            decision_evidence_count=0,
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=2,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.evidence_token_count_total == 5
    assert summary.evidence_token_count_avg == 2.5
    assert summary.evidence_type_counts == {
        "risk_feature": 1,
        "planner_decision": 2,
        "uncertainty_feature": 1,
        "event_diff": 1,
    }
    assert summary.risk_evidence_count_total == 1
    assert summary.uncertainty_evidence_count_total == 1
    assert summary.event_evidence_count_total == 1
    assert summary.decision_evidence_count_total == 2
    assert summary.decision_evidence_coverage == 0.5


def test_episode_summary_counts_uncertainty_tokens_and_planner_disagreement() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            uncertainty_aware_action="Stop",
            uncertainty_aware_reason_code="high_uncertainty_near_path",
            uncertainty_token_count=2,
            uncertainty_types=["classification_uncertainty", "position_uncertainty"],
            high_uncertainty_count=1,
        ),
        make_record(
            step=1,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            uncertainty_aware_action="MoveAhead",
            uncertainty_aware_reason_code="fallback_no_risk_move_ahead",
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=2,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.uncertainty_token_count_total == 2
    assert summary.uncertainty_token_count_avg == 1.0
    assert summary.high_uncertainty_count_total == 1
    assert summary.uncertainty_type_counts == {"classification_uncertainty": 1, "position_uncertainty": 1}
    assert summary.rast_vs_uncertainty_aware_disagreement_count == 1
    assert summary.uncertainty_triggered_action_count == 1
    assert summary.uncertainty_aware_decision_trace_coverage == 1.0


def test_episode_summary_counts_affordance_tokens_and_planner_disagreement() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            affordance_aware_action="RotateRight",
            affordance_aware_reason_code="affordance_narrow_passage_slow_or_rotate",
            affordance_token_count=2,
            affordance_types=["narrow_passage", "passable"],
        ),
        make_record(
            step=1,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            affordance_aware_action="MoveAhead",
            affordance_aware_reason_code="affordance_passable_move_ahead",
            affordance_token_count=1,
            affordance_types=["passable"],
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=2,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.affordance_token_count_total == 3
    assert summary.affordance_token_count_avg == 1.5
    assert summary.affordance_type_counts == {"narrow_passage": 1, "passable": 2}
    assert summary.rast_vs_affordance_aware_disagreement_count == 1
    assert summary.affordance_triggered_action_count == 2
    assert summary.affordance_aware_decision_trace_coverage == 1.0


def test_episode_summary_counts_event_aware_disagreement_and_event_reasons() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="RotateRight",
            object_list_action="RotateRight",
            event_aware_action="Stop",
            event_aware_reason_code="event_risk_increased",
            event_aware_trigger_event_types=["risk_changed"],
            event_policy_variant="full",
        ),
        make_record(
            step=1,
            total_latency=10.0,
            rast_action="MoveAhead",
            object_list_action="MoveAhead",
            event_aware_action="MoveAhead",
            event_aware_reason_code="event_object_disappeared_clear_path",
            event_aware_trigger_event_types=["object_disappeared"],
            event_policy_variant="full",
        ),
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=2,
        collision_threshold=0.2,
        near_miss_threshold=1.0,
    )

    assert summary.rast_vs_event_aware_disagreement_count == 1
    assert summary.event_triggered_action_count == 2
    assert summary.event_aware_decision_trace_coverage == 1.0
    assert summary.event_aware_rast_reason_code_counts == {
        "event_risk_increased": 1,
        "event_object_disappeared_clear_path": 1,
    }


def test_episode_summary_records_event_policy_variant_and_noise_fields() -> None:
    records = [
        make_record(
            step=0,
            total_latency=10.0,
            rast_action="RotateRight",
            object_list_action="RotateRight",
            event_aware_action="Stop",
            event_aware_reason_code="event_risk_increased",
            event_policy_variant="no_risk_changed",
            risk_threshold=2.0,
            near_miss_threshold=0.75,
            position_noise_std=0.02,
            distance_noise_std=0.03,
            visibility_flip_prob=0.1,
        )
    ]

    summary = calculate_episode_summary(
        records,
        max_steps=1,
        collision_threshold=0.2,
        near_miss_threshold=0.75,
    )

    assert summary.event_policy_variant == "no_risk_changed"
    assert summary.risk_threshold == 2.0
    assert summary.near_miss_threshold == 0.75
    assert summary.position_noise_std == 0.02
    assert summary.distance_noise_std == 0.03
    assert summary.visibility_flip_prob == 0.1
    assert summary.event_policy_variant_action_counts == {"no_risk_changed": {"Stop": 1}}
    assert summary.event_policy_variant_reason_code_counts == {"no_risk_changed": {"event_risk_increased": 1}}


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

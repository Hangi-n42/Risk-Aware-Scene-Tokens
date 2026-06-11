import json
from pathlib import Path

from rast.evaluation.aggregate import aggregate_episode_summaries


def write_fake_summary(
    path: Path,
    *,
    success: bool,
    near_miss_count: int,
    event_token_count_total: int | None = None,
    event_type_counts: dict[str, int] | None = None,
    update_mode: str | None = None,
    include_decision_fields: bool = False,
    include_scene_graph_fields: bool = False,
    include_event_aware_fields: bool = False,
    include_sensitivity_fields: bool = False,
) -> None:
    payload = {
        "success": success,
        "goal_reached": False,
        "completed_steps": 10,
        "collision_count": 0,
        "near_miss_count": near_miss_count,
        "baseline_disagreement_count": 1,
        "rast_vs_object_list_disagreement_count": 1,
        "rast_vs_flat_feature_disagreement_count": 0,
        "object_list_vs_flat_feature_disagreement_count": 1,
        "token_count_avg": 2.0,
        "object_count_avg": 1.0,
        "flat_feature_row_count_avg": 1.0,
        "latency_avg_ms": 0.2,
        "latency_p50_ms": 0.2,
        "latency_p95_ms": 0.3,
        "token_generation_latency_avg_ms": 0.05,
        "planning_latency_avg_ms": 0.04,
        "total_latency_avg_ms": 0.2,
    }
    if event_token_count_total is not None:
        payload["event_token_count_total"] = event_token_count_total
        payload["event_token_count_avg"] = event_token_count_total / 10
        payload["event_type_counts"] = event_type_counts or {}
    if update_mode is not None:
        payload["update_mode"] = update_mode
        payload["changed_object_count_avg"] = 1.0
        payload["affected_token_count_avg"] = 2.0
        payload["full_recompute_latency_avg_ms"] = 0.2
        payload["incremental_update_latency_avg_ms"] = 0.1
        payload["incremental_update_benefit_avg"] = 0.5
    if include_decision_fields:
        payload["rast_reason_code_counts"] = {"high_risk_token": 2}
        payload["object_list_reason_code_counts"] = {"near_object_distance": 2}
        payload["flat_feature_reason_code_counts"] = {"within_risk_threshold": 2}
        payload["rast_trigger_token_count_total"] = 2
        payload["decision_trace_coverage"] = 1.0
    if include_scene_graph_fields:
        payload["relation_token_count_total"] = 4
        payload["relation_token_count_avg"] = 0.4
        payload["relation_type_counts"] = {"near_agent": 2, "blocking_path": 2}
        payload["scene_graph_action_counts"] = {"RotateRight": 2}
        payload["scene_graph_reason_code_counts"] = {"graph_blocking_path": 2}
        payload["scene_graph_node_count_avg"] = 3.0
        payload["scene_graph_edge_count_avg"] = 2.0
        payload["rast_vs_scene_graph_disagreement_count"] = 1
        payload["scene_graph_vs_flat_feature_disagreement_count"] = 1
        payload["scene_graph_decision_trace_coverage"] = 1.0
    if include_event_aware_fields:
        payload["event_aware_rast_action_counts"] = {"Stop": 1, "MoveAhead": 1}
        payload["event_aware_rast_reason_code_counts"] = {
            "event_risk_increased": 1,
            "fallback_no_risk_move_ahead": 1,
        }
        payload["rast_vs_event_aware_disagreement_count"] = 1
        payload["event_triggered_action_count"] = 1
        payload["event_aware_decision_trace_coverage"] = 1.0
    if include_sensitivity_fields:
        payload["event_policy_variant"] = "no_risk_changed"
        payload["risk_threshold"] = 2.0
        payload["near_miss_threshold"] = 0.75
        payload["position_noise_std"] = 0.02
        payload["distance_noise_std"] = 0.03
        payload["visibility_flip_prob"] = 0.1
        payload["event_policy_variant_action_counts"] = {"no_risk_changed": {"Stop": 1}}
        payload["event_policy_variant_reason_code_counts"] = {"no_risk_changed": {"event_risk_increased": 1}}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_aggregate_episode_summaries_writes_csv_and_json(tmp_path: Path) -> None:
    first_dir = tmp_path / "run_001"
    second_dir = tmp_path / "run_002"
    first_dir.mkdir()
    second_dir.mkdir()
    first_summary = first_dir / "episode_summary.json"
    second_summary = second_dir / "episode_summary.json"
    write_fake_summary(first_summary, success=True, near_miss_count=0)
    write_fake_summary(second_summary, success=False, near_miss_count=2)

    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "clear_path",
                "seed": 0,
                "apply_policy": "rast",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": str(first_summary),
                "episode_output_dir": str(first_dir),
                "status": "success",
            },
            {
                "suite_run_id": "suite_test",
                "scenario": "near_obstacle",
                "seed": 1,
                "apply_policy": "flat_feature",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": str(second_summary),
                "episode_output_dir": str(second_dir),
                "status": "success",
            },
        ],
        output_dir=tmp_path,
    )

    assert (tmp_path / "aggregate_results.csv").exists()
    assert (tmp_path / "aggregate_results.json").exists()
    assert rows[0]["scenario"] == "clear_path"
    assert rows[0]["seed"] == 0
    assert rows[0]["apply_policy"] == "rast"
    assert rows[0]["risk_threshold"] == 1.5
    assert rows[1]["near_miss_count"] == 2
    assert rows[0]["event_token_count_total"] == 0
    assert rows[0]["event_token_count_avg"] == 0.0
    assert rows[0]["event_type_counts"] == {}
    assert rows[0]["update_mode"] == "full_recompute"
    assert rows[0]["incremental_update_benefit_avg"] == 0.0
    assert rows[0]["rast_reason_code_counts"] == {}
    assert rows[0]["decision_trace_coverage"] == 0.0
    assert rows[0]["event_aware_rast_reason_code_counts"] == {}
    assert rows[0]["rast_vs_event_aware_disagreement_count"] == 0
    assert rows[0]["event_triggered_action_count"] == 0
    assert rows[0]["event_policy_variant"] == "full"
    assert rows[0]["position_noise_std"] == 0.0
    assert rows[0]["distance_noise_std"] == 0.0
    assert rows[0]["visibility_flip_prob"] == 0.0


def test_aggregate_episode_summaries_includes_event_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_event"
    run_dir.mkdir()
    summary_path = run_dir / "episode_summary.json"
    write_fake_summary(
        summary_path,
        success=True,
        near_miss_count=1,
        event_token_count_total=3,
        event_type_counts={"object_moved": 2, "risk_changed": 1},
    )

    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "object_moves",
                "seed": 0,
                "apply_policy": "rast",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": str(summary_path),
                "episode_output_dir": str(run_dir),
                "status": "success",
            }
        ],
        output_dir=tmp_path,
    )

    assert rows[0]["event_token_count_total"] == 3
    assert rows[0]["event_token_count_avg"] == 0.3
    assert rows[0]["event_type_counts"] == {"object_moved": 2, "risk_changed": 1}


def test_aggregate_episode_summaries_includes_incremental_update_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_incremental"
    run_dir.mkdir()
    summary_path = run_dir / "episode_summary.json"
    write_fake_summary(
        summary_path,
        success=True,
        near_miss_count=1,
        update_mode="incremental",
    )

    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "object_moves",
                "seed": 0,
                "apply_policy": "rast",
                "update_mode": "incremental",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": str(summary_path),
                "episode_output_dir": str(run_dir),
                "status": "success",
            }
        ],
        output_dir=tmp_path,
    )

    assert rows[0]["update_mode"] == "incremental"
    assert rows[0]["changed_object_count_avg"] == 1.0
    assert rows[0]["affected_token_count_avg"] == 2.0
    assert rows[0]["full_recompute_latency_avg_ms"] == 0.2
    assert rows[0]["incremental_update_latency_avg_ms"] == 0.1
    assert rows[0]["incremental_update_benefit_avg"] == 0.5


def test_aggregate_episode_summaries_includes_decision_trace_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_decision"
    run_dir.mkdir()
    summary_path = run_dir / "episode_summary.json"
    write_fake_summary(
        summary_path,
        success=True,
        near_miss_count=1,
        include_decision_fields=True,
    )

    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "planner_disagreement",
                "seed": 0,
                "apply_policy": "rast",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": str(summary_path),
                "episode_output_dir": str(run_dir),
                "status": "success",
            }
        ],
        output_dir=tmp_path,
    )

    assert rows[0]["rast_reason_code_counts"] == {"high_risk_token": 2}
    assert rows[0]["object_list_reason_code_counts"] == {"near_object_distance": 2}
    assert rows[0]["flat_feature_reason_code_counts"] == {"within_risk_threshold": 2}
    assert rows[0]["rast_trigger_token_count_total"] == 2
    assert rows[0]["decision_trace_coverage"] == 1.0


def test_aggregate_episode_summaries_includes_scene_graph_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_scene_graph"
    run_dir.mkdir()
    summary_path = run_dir / "episode_summary.json"
    write_fake_summary(
        summary_path,
        success=True,
        near_miss_count=1,
        include_scene_graph_fields=True,
    )

    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "near_obstacle",
                "seed": 0,
                "apply_policy": "scene_graph",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": str(summary_path),
                "episode_output_dir": str(run_dir),
                "status": "success",
            }
        ],
        output_dir=tmp_path,
    )

    assert rows[0]["relation_token_count_total"] == 4
    assert rows[0]["relation_token_count_avg"] == 0.4
    assert rows[0]["relation_type_counts"] == {"near_agent": 2, "blocking_path": 2}
    assert rows[0]["scene_graph_action_counts"] == {"RotateRight": 2}
    assert rows[0]["scene_graph_reason_code_counts"] == {"graph_blocking_path": 2}
    assert rows[0]["scene_graph_node_count_avg"] == 3.0
    assert rows[0]["scene_graph_edge_count_avg"] == 2.0
    assert rows[0]["rast_vs_scene_graph_disagreement_count"] == 1
    assert rows[0]["scene_graph_vs_flat_feature_disagreement_count"] == 1
    assert rows[0]["scene_graph_decision_trace_coverage"] == 1.0


def test_aggregate_episode_summaries_includes_event_aware_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_event_aware"
    run_dir.mkdir()
    summary_path = run_dir / "episode_summary.json"
    write_fake_summary(
        summary_path,
        success=True,
        near_miss_count=1,
        include_event_aware_fields=True,
    )

    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "risk_increases",
                "seed": 0,
                "apply_policy": "event_aware_rast",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": str(summary_path),
                "episode_output_dir": str(run_dir),
                "status": "success",
            }
        ],
        output_dir=tmp_path,
    )

    assert rows[0]["event_aware_rast_action_counts"] == {"Stop": 1, "MoveAhead": 1}
    assert rows[0]["event_aware_rast_reason_code_counts"] == {
        "event_risk_increased": 1,
        "fallback_no_risk_move_ahead": 1,
    }
    assert rows[0]["rast_vs_event_aware_disagreement_count"] == 1
    assert rows[0]["event_triggered_action_count"] == 1
    assert rows[0]["event_aware_decision_trace_coverage"] == 1.0


def test_aggregate_episode_summaries_includes_variant_threshold_and_noise_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_sensitivity"
    run_dir.mkdir()
    summary_path = run_dir / "episode_summary.json"
    write_fake_summary(
        summary_path,
        success=True,
        near_miss_count=1,
        include_sensitivity_fields=True,
    )

    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "risk_increases",
                "seed": 0,
                "apply_policy": "event_aware_rast",
                "event_policy_variant": "no_risk_changed",
                "risk_threshold": 2.0,
                "near_miss_threshold": 0.75,
                "collision_threshold": 0.2,
                "position_noise_std": 0.02,
                "distance_noise_std": 0.03,
                "visibility_flip_prob": 0.1,
                "summary_path": str(summary_path),
                "episode_output_dir": str(run_dir),
                "status": "success",
            }
        ],
        output_dir=tmp_path,
    )

    assert rows[0]["event_policy_variant"] == "no_risk_changed"
    assert rows[0]["risk_threshold"] == 2.0
    assert rows[0]["near_miss_threshold"] == 0.75
    assert rows[0]["position_noise_std"] == 0.02
    assert rows[0]["distance_noise_std"] == 0.03
    assert rows[0]["visibility_flip_prob"] == 0.1
    assert rows[0]["event_policy_variant_action_counts"] == {"no_risk_changed": {"Stop": 1}}
    assert rows[0]["event_policy_variant_reason_code_counts"] == {"no_risk_changed": {"event_risk_increased": 1}}


def test_aggregate_keeps_failed_run_metadata(tmp_path: Path) -> None:
    rows = aggregate_episode_summaries(
        [
            {
                "suite_run_id": "suite_test",
                "scenario": "broken_scenario",
                "seed": 0,
                "apply_policy": "rast",
                "risk_threshold": 1.5,
                "near_miss_threshold": 1.0,
                "collision_threshold": 0.2,
                "summary_path": "",
                "episode_output_dir": str(tmp_path / "broken"),
                "status": "failed",
                "error": "intentional failure",
            }
        ],
        output_dir=tmp_path,
    )

    assert rows[0]["status"] == "failed"
    assert rows[0]["scenario"] == "broken_scenario"
    assert rows[0]["error"] == "intentional failure"
    aggregate_json = json.loads((tmp_path / "aggregate_results.json").read_text(encoding="utf-8"))
    assert aggregate_json[0]["status"] == "failed"

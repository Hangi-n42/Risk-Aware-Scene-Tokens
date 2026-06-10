import json
from pathlib import Path

from experiments.run_windows_metadata_sim import run_simulation
from rast.planner.object_list_planner import ObjectListPlannerConfig, plan_from_object_list
from rast.planner.token_planner import plan_from_tokens
from rast.baselines.object_list import build_object_list
from rast.simulator.windows_scenarios import available_scenarios, build_windows_scenario
from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig


def first_step_tokens(scenario_name: str):
    scenario = build_windows_scenario(scenario_name)
    snapshot = scenario.simulator.snapshot(episode_id=f"test_{scenario_name}")
    return tokenize_snapshot(
        snapshot,
        risk_config=RiskTokenizerConfig(near_agent_threshold=scenario.risk_threshold),
    )


def test_scenario_suite_contains_required_names() -> None:
    assert set(available_scenarios()) >= {
        "clear_path",
        "near_obstacle",
        "far_obstacle",
        "unknown_near_path",
        "target_reachable",
        "planner_disagreement",
        "object_appears",
        "object_disappears",
        "object_moves",
        "risk_increases",
    }


def test_clear_path_has_no_first_step_risk_and_moves_ahead() -> None:
    scenario = build_windows_scenario("clear_path")
    snapshot = scenario.simulator.snapshot(episode_id="clear_path_test")
    result = tokenize_snapshot(
        snapshot,
        risk_config=RiskTokenizerConfig(near_agent_threshold=scenario.risk_threshold),
    )
    object_list = build_object_list(snapshot)

    assert result.risks == []
    assert plan_from_tokens(result.entities, result.risks).value == "MoveAhead"
    assert (
        plan_from_object_list(
            object_list,
            config=ObjectListPlannerConfig(near_object_threshold=scenario.object_list_threshold),
        ).value
        == "MoveAhead"
    )


def test_near_obstacle_generates_risk_token() -> None:
    result = first_step_tokens("near_obstacle")

    assert result.risks


def test_far_obstacle_has_no_high_risk_token() -> None:
    result = first_step_tokens("far_obstacle")

    assert not any(risk.severity == "high" for risk in result.risks)


def test_unknown_near_path_generates_unknown_risk_token() -> None:
    result = first_step_tokens("unknown_near_path")

    assert any(risk.entity_id.startswith("UnknownObject|near_path") for risk in result.risks)


def test_planner_disagreement_summary_counts_disagreement(tmp_path: Path) -> None:
    scenario = build_windows_scenario("planner_disagreement")
    output_path = tmp_path / "planner_disagreement" / "step_log.jsonl"

    run_simulation(
        sim=scenario.simulator,
        scenario_name=scenario.name,
        max_steps=3,
        risk_threshold=scenario.risk_threshold,
        object_list_threshold=scenario.object_list_threshold,
        collision_threshold=scenario.collision_threshold,
        near_miss_threshold=scenario.near_miss_threshold,
        output_path=output_path,
        goal=scenario.goal,
    )
    summary = json.loads((output_path.parent / "episode_summary.json").read_text(encoding="utf-8"))
    first_record = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])

    assert summary["baseline_disagreement_count"] > 0
    assert summary["rast_vs_object_list_disagreement_count"] > 0
    assert "rast_vs_flat_feature_disagreement_count" in summary
    assert "object_list_vs_flat_feature_disagreement_count" in summary
    assert first_record["rast_selected_action"]
    assert first_record["object_list_selected_action"]
    assert first_record["flat_feature_selected_action"]
    assert first_record["rast_reason_code"]
    assert first_record["object_list_reason_code"]
    assert first_record["flat_feature_reason_code"]
    assert "rast_decision" in first_record
    assert "object_list_decision" in first_record
    assert "flat_feature_decision" in first_record


def test_target_reachable_uses_goal_reached_success(tmp_path: Path) -> None:
    scenario = build_windows_scenario("target_reachable")
    output_path = tmp_path / "target_reachable" / "step_log.jsonl"

    run_simulation(
        sim=scenario.simulator,
        scenario_name=scenario.name,
        max_steps=20,
        risk_threshold=scenario.risk_threshold,
        object_list_threshold=scenario.object_list_threshold,
        collision_threshold=scenario.collision_threshold,
        near_miss_threshold=scenario.near_miss_threshold,
        output_path=output_path,
        goal=scenario.goal,
    )
    summary = json.loads((output_path.parent / "episode_summary.json").read_text(encoding="utf-8"))

    assert summary["success"] is True
    assert summary["success_definition"] == "goal_reached_and_no_collision"
    assert summary["goal_reached"] is True
    assert summary["final_distance_to_goal"] <= scenario.goal.success_distance

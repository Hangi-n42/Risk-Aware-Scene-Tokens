from pathlib import Path

from experiments.run_windows_metadata_sim import run_simulation
from rast.evaluation.jsonl_logger import JSONLLogger
from rast.planner.actions import Action
from rast.simulator.windows_metadata_sim import MetadataNoiseConfig, WindowsMetadataSim
from rast.simulator.windows_scenarios import build_windows_scenario
from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig


def test_move_ahead_changes_agent_position() -> None:
    sim = WindowsMetadataSim()
    before = sim.agent.position

    sim.step(Action.MOVE_AHEAD)

    after = sim.agent.position
    assert (after.x, after.y, after.z) != (before.x, before.y, before.z)


def test_near_object_generates_risk_token() -> None:
    sim = WindowsMetadataSim()
    snapshot = sim.snapshot(episode_id="windows_test_episode")

    result = tokenize_snapshot(snapshot, risk_config=RiskTokenizerConfig(near_agent_threshold=1.5))

    assert len(result.entities) >= 4
    assert result.risks
    assert any(risk.entity_id.startswith("Chair|windows|near") for risk in result.risks)


def test_windows_metadata_sim_runner_writes_jsonl(tmp_path: Path) -> None:
    output_path = tmp_path / "step_log.jsonl"

    records = run_simulation(max_steps=2, risk_threshold=1.5, output_path=output_path)
    rows = JSONLLogger(output_path).read_all()
    summary_json = tmp_path / "episode_summary.json"
    summary_csv = tmp_path / "episode_summary.csv"

    assert output_path.exists()
    assert summary_json.exists()
    assert summary_csv.exists()
    assert len(records) == 2
    assert len(rows) == 2
    assert rows[0]["run_id"] == "windows_metadata_sim"
    assert rows[0]["scene_id"] == "WindowsRoom1"
    assert rows[0]["baseline_type"] == "rast"
    assert rows[0]["rast_selected_action"]
    assert rows[0]["object_list_selected_action"]
    assert rows[0]["flat_feature_selected_action"]
    assert rows[0]["event_aware_rast_selected_action"]
    assert rows[0]["rast_decision"]["reason_code"]
    assert rows[0]["object_list_decision"]["reason_code"]
    assert rows[0]["flat_feature_decision"]["reason_code"]
    assert rows[0]["event_aware_rast_decision"]["reason_code"]
    assert rows[0]["rast_reason_code"]
    assert rows[0]["object_list_reason_code"]
    assert rows[0]["flat_feature_reason_code"]
    assert rows[0]["event_aware_rast_reason_code"]
    assert "rast_trigger_token_ids" in rows[0]
    assert "rast_trigger_object_ids" in rows[0]
    assert "object_list_trigger_object_ids" in rows[0]
    assert "flat_feature_trigger_object_ids" in rows[0]
    assert "event_aware_rast_trigger_event_types" in rows[0]
    assert "event_aware_rast_trigger_token_ids" in rows[0]
    assert rows[0]["flat_feature_row_count"] == rows[0]["object_list_count"]
    assert "event_token_count" in rows[0]
    assert "event_types" in rows[0]
    assert "evidence_token_count" in rows[0]
    assert "evidence_types" in rows[0]
    assert "evidence_token_ids" in rows[0]
    assert "decision_evidence_count" in rows[0]
    assert rows[0]["evidence_token_count"] >= rows[0]["decision_evidence_count"]
    assert "evidence_token_ids" in rows[0]["rast_decision"]
    assert rows[0]["update_mode"] == "full_recompute"
    assert "changed_object_count" in rows[0]
    assert "affected_token_count" in rows[0]
    assert "full_recompute_latency_ms" in rows[0]
    assert "incremental_update_latency_ms" in rows[0]
    assert "incremental_update_benefit" in rows[0]
    assert "rast_vs_flat_feature_disagreed" in rows[0]
    assert "object_list_vs_flat_feature_disagreed" in rows[0]
    assert "rast_vs_event_aware_disagreed" in rows[0]
    assert rows[0]["event_policy_variant"] == "full"
    assert rows[0]["risk_threshold"] == 1.5
    assert rows[0]["near_miss_threshold"] == 1.0
    assert rows[0]["position_noise_std"] == 0.0
    assert rows[0]["distance_noise_std"] == 0.0
    assert rows[0]["visibility_flip_prob"] == 0.0
    assert rows[0]["risk_token_count"] >= 1
    assert rows[0]["near_miss"] is True
    assert rows[0]["tokens"]


def test_windows_metadata_sim_runner_records_incremental_update_mode(tmp_path: Path) -> None:
    output_path = tmp_path / "incremental" / "step_log.jsonl"

    run_simulation(max_steps=2, risk_threshold=1.5, update_mode="incremental", output_path=output_path)
    rows = JSONLLogger(output_path).read_all()

    assert rows[0]["update_mode"] == "incremental"
    assert rows[0]["token_generation_latency_ms"] == rows[0]["latency"]["token_generation"]
    assert rows[0]["rast_decision"]["planner_name"] == "rast"
    assert rows[0]["rast_reason_code"]
    assert (output_path.parent / "episode_summary.json").exists()


def test_windows_metadata_sim_runner_supports_event_aware_apply_policy(tmp_path: Path) -> None:
    output_path = tmp_path / "event_aware" / "step_log.jsonl"
    scenario = build_windows_scenario("object_appears")

    records = run_simulation(
        sim=scenario.simulator,
        max_steps=3,
        risk_threshold=scenario.risk_threshold,
        scenario_name="object_appears",
        update_mode="incremental",
        apply_policy="event_aware_rast",
        output_path=output_path,
    )
    rows = JSONLLogger(output_path).read_all()

    assert records
    assert rows[0]["baseline_type"] == "rast"
    assert all(row["event_aware_rast_selected_action"] == row["selected_action"] for row in rows)
    assert any(row["event_aware_rast_reason_code"].startswith("event_") for row in rows)


def test_windows_metadata_sim_noise_is_seed_reproducible() -> None:
    noise_config = MetadataNoiseConfig(position_noise_std=0.1, distance_noise_std=0.1, seed=42)
    first = WindowsMetadataSim(noise_config=noise_config)
    second = WindowsMetadataSim(noise_config=noise_config)
    different_seed = WindowsMetadataSim(
        noise_config=MetadataNoiseConfig(position_noise_std=0.1, distance_noise_std=0.1, seed=43)
    )

    first_metadata = first.metadata()
    second_metadata = second.metadata()
    different_metadata = different_seed.metadata()

    assert first_metadata["objects"] == second_metadata["objects"]
    assert first_metadata["objects"][0]["objectId"] == different_metadata["objects"][0]["objectId"]
    assert first_metadata["objects"][0]["objectType"] == different_metadata["objects"][0]["objectType"]
    assert first_metadata["objects"][0]["position"] != different_metadata["objects"][0]["position"]

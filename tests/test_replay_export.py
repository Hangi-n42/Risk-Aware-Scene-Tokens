import json
from pathlib import Path

from experiments.run_windows_eval_suite import export_suite_replays
from rast.evaluation.replay import find_step_log, replay_cases_for_record, write_decision_replay


def test_replay_export_writes_markdown_and_json(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    step_log = run_dir / "step_log.jsonl"
    record = {
        "run_id": "run_001",
        "episode_id": "episode_001",
        "scene_id": "WindowsRoom1",
        "step": 1,
        "selected_action": "RotateRight",
        "rast_selected_action": "RotateRight",
        "object_list_selected_action": "MoveAhead",
        "baseline_disagreed": True,
        "near_miss": True,
        "risk_token_count": 1,
        "high_uncertainty_count": 1,
        "uncertainty_token_count": 1,
        "event_token_count": 1,
        "uncertainty_types": ["unknown_object"],
        "event_types": ["risk_changed"],
        "rast_reason_code": "high_risk_token",
        "uncertainty_aware_rast_reason_code": "unknown_object_uncertainty",
        "evidence_token_ids": ["ev_risk_1", "ev_decision_1"],
        "evidence_types": ["risk_feature", "planner_decision"],
        "risk_evidence_count": 1,
        "decision_evidence_count": 1,
        "metadata_snapshot_ref": "windows_metadata_sim:WindowsRoom1:step:1",
        "tokens": [{"type": "RiskToken", "severity": "high"}, {"type": "UncertaintyToken", "level": "high"}],
        "extra": {"scenario": "planner_disagreement"},
    }
    step_log.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    output_md = run_dir / "decision_replay.md"
    payload = write_decision_replay(step_log_path=step_log, output_md_path=output_md)

    assert find_step_log(run_dir) == step_log
    assert output_md.exists()
    assert output_md.with_suffix(".json").exists()
    assert payload["selected_step_count"] == 1
    markdown = output_md.read_text(encoding="utf-8")
    assert "RAST Decision Replay" in markdown
    assert "metadata simulator replay, not visual replay" in markdown
    assert "planner_disagreement" in markdown
    assert "ev_risk_1" in markdown


def test_replay_cases_include_affordance_aware_triggers() -> None:
    record = {
        "rast_vs_affordance_aware_disagreed": True,
        "affordance_aware_rast_reason_code": "affordance_avoid_required",
    }

    cases = replay_cases_for_record(record)

    assert "rast_vs_affordance_aware_disagreement" in cases
    assert "affordance_triggered_action" in cases


def test_export_suite_replays_writes_replay_index(tmp_path: Path) -> None:
    run_dir = tmp_path / "suite" / "run_001"
    run_dir.mkdir(parents=True)
    step_log = run_dir / "step_log.jsonl"
    record = {
        "run_id": "run_001",
        "episode_id": "episode_001",
        "scene_id": "WindowsRoom1",
        "step": 2,
        "selected_action": "RotateRight",
        "rast_selected_action": "MoveAhead",
        "affordance_aware_rast_selected_action": "RotateRight",
        "rast_vs_affordance_aware_disagreed": True,
        "affordance_aware_rast_reason_code": "affordance_avoid_required",
        "affordance_aware_rast_trigger_token_ids": ["affordance_1"],
        "evidence_token_ids": ["ev_affordance_1"],
        "evidence_types": ["planner_decision"],
        "extra": {"scenario": "avoid_required_blocking_path"},
    }
    step_log.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    run_metadata = [
        {
            "status": "success",
            "scenario": "avoid_required_blocking_path",
            "episode_output_dir": str(run_dir),
            "step_log_path": str(step_log),
        }
    ]

    index_path = export_suite_replays(
        run_metadata,
        suite_run_id="suite_test",
        output_dir=tmp_path / "suite" / "replays",
        max_replays=2,
    )

    assert index_path.exists()
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["replay_count"] == 2
    assert payload["entries"][0]["case_type"] == "rast_vs_affordance_aware_disagreement"
    assert Path(payload["entries"][0]["markdown_path"]).exists()
    assert Path(payload["entries"][0]["json_path"]).exists()

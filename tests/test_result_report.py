import csv
import json
from pathlib import Path

from rast.evaluation.report import generate_result_report, write_result_report


def write_fake_aggregate_results(path: Path) -> None:
    fieldnames = [
        "suite_run_id",
        "scenario",
        "seed",
        "apply_policy",
        "risk_threshold",
        "near_miss_threshold",
        "collision_threshold",
        "success",
        "goal_reached",
        "completed_steps",
        "collision_count",
        "near_miss_count",
        "baseline_disagreement_count",
        "rast_vs_object_list_disagreement_count",
        "rast_vs_flat_feature_disagreement_count",
        "object_list_vs_flat_feature_disagreement_count",
        "token_count_avg",
        "object_count_avg",
        "flat_feature_row_count_avg",
        "latency_avg_ms",
        "latency_p50_ms",
        "latency_p95_ms",
        "token_generation_latency_avg_ms",
        "planning_latency_avg_ms",
        "total_latency_avg_ms",
        "status",
    ]
    rows = [
        {
            "suite_run_id": "suite_test",
            "scenario": "clear_path",
            "seed": "0",
            "apply_policy": "rast",
            "risk_threshold": "1.5",
            "near_miss_threshold": "1.0",
            "collision_threshold": "0.2",
            "success": "True",
            "goal_reached": "False",
            "completed_steps": "10",
            "collision_count": "0",
            "near_miss_count": "0",
            "baseline_disagreement_count": "0",
            "rast_vs_object_list_disagreement_count": "0",
            "rast_vs_flat_feature_disagreement_count": "0",
            "object_list_vs_flat_feature_disagreement_count": "0",
            "token_count_avg": "2.0",
            "object_count_avg": "2.0",
            "flat_feature_row_count_avg": "2.0",
            "latency_avg_ms": "0.2",
            "latency_p50_ms": "0.2",
            "latency_p95_ms": "0.3",
            "token_generation_latency_avg_ms": "0.05",
            "planning_latency_avg_ms": "0.04",
            "total_latency_avg_ms": "0.2",
            "status": "success",
        },
        {
            "suite_run_id": "suite_test",
            "scenario": "planner_disagreement",
            "seed": "0",
            "apply_policy": "object_list",
            "risk_threshold": "1.5",
            "near_miss_threshold": "1.0",
            "collision_threshold": "0.2",
            "success": "True",
            "goal_reached": "False",
            "completed_steps": "10",
            "collision_count": "0",
            "near_miss_count": "3",
            "baseline_disagreement_count": "7",
            "rast_vs_object_list_disagreement_count": "7",
            "rast_vs_flat_feature_disagreement_count": "0",
            "object_list_vs_flat_feature_disagreement_count": "7",
            "token_count_avg": "2.0",
            "object_count_avg": "1.0",
            "flat_feature_row_count_avg": "1.0",
            "latency_avg_ms": "0.25",
            "latency_p50_ms": "0.24",
            "latency_p95_ms": "0.4",
            "token_generation_latency_avg_ms": "0.06",
            "planning_latency_avg_ms": "0.05",
            "total_latency_avg_ms": "0.25",
            "status": "success",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_generate_result_report_markdown_contains_required_sections_and_limits(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    write_fake_aggregate_results(results_path)

    markdown = generate_result_report(results_path=results_path)

    assert "WindowsMetadataSim" in markdown
    assert "deterministic metadata simulator" in markdown
    assert "does not support real-world performance claims" in markdown
    assert "## Suite Execution Metadata" in markdown
    assert "## Baselines" in markdown
    assert "## EventToken Summary" in markdown
    assert "## Incremental Update Summary" in markdown
    assert "## Decision Trace Summary" in markdown
    assert "## RelationToken Summary" in markdown
    assert "## UncertaintyToken Summary" in markdown
    assert "## EvidenceToken Summary" in markdown
    assert "## AffordanceToken Summary" in markdown
    assert "## Replay Trace Summary" in markdown
    assert "## Replay Artifact Summary" in markdown
    assert "## Representative Decision Trace Summary" in markdown
    assert "## Sampling Coverage and Stability Artifacts" in markdown
    assert "## Sample-size Convergence Artifact" in markdown
    assert "## Scene Graph Baseline Summary" in markdown
    assert "## Scene Graph vs RAST Differentiation Summary" in markdown
    assert "## Event-aware Planner Summary" in markdown
    assert "## Uncertainty-aware Planner Summary" in markdown
    assert "## Affordance-aware Planner Summary" in markdown
    assert "## Event-aware Ablation Summary" in markdown
    assert "## Threshold and Noise Sensitivity Summary" in markdown
    assert "Affordance-aware RAST" in markdown
    assert "affordance_token_count_total" in markdown
    assert "affordance_type_counts" in markdown
    assert "rast_vs_affordance_aware_disagreement_count" in markdown
    assert "affordance_triggered_action_count" in markdown
    assert "affordance_aware_decision_trace_coverage" in markdown
    assert "Event-aware RAST planner" in markdown
    assert "incremental update optimization is experimental" in markdown
    assert "rule-based planner explanations" in markdown
    assert "simplified graph" in markdown
    assert "same-action-different-reason" in markdown
    assert "learned relation extraction" in markdown
    assert "synthetic metadata uncertainty" in markdown
    assert "metadata pointers" in markdown
    assert "metadata/action trace reconstruction" in markdown
    assert "navigation affordance" in markdown
    assert "navigation affordance only" in markdown
    assert "real robot action feasibility" in markdown
    assert "EventToken, UncertaintyToken, EvidenceToken, AffordanceToken" in markdown
    assert "현재 결과는 EventToken의 감지와 기록 검증" not in markdown
    assert "현재 report는 EventToken이 step log와 episode summary" not in markdown
    assert "EvidenceToken이 risk/uncertainty/event/planner decision evidence" in markdown
    assert "decision replay markdown/json" in markdown
    assert "AffordanceToken이 navigation affordance" in markdown
    assert "Affordance-aware planner나 AffordanceToken이 task performance" in markdown
    assert "EvidenceToken이 real sensor evidence" in markdown
    assert "EvidenceToken, AffordanceToken, perception-bound adapter는 별도 Batch로 추가합니다." not in markdown
    assert "EvidenceToken 추가" not in markdown
    assert "AffordanceToken 추가" not in markdown
    assert "## Limitations" in markdown


def test_generate_result_report_can_link_sampling_artifacts(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    write_fake_aggregate_results(results_path)
    coverage_path = tmp_path / "sampling_coverage_report.md"
    stability_path = tmp_path / "seed_stability_report.md"
    convergence_path = tmp_path / "sample_size_convergence_report.md"
    coverage_path.write_text("# coverage\n", encoding="utf-8")
    stability_path.write_text("# stability\n", encoding="utf-8")
    convergence_path.write_text("# convergence\n", encoding="utf-8")

    markdown = generate_result_report(
        results_path=results_path,
        sampling_coverage_path=coverage_path,
        seed_stability_path=stability_path,
        sample_size_convergence_path=convergence_path,
    )

    assert "## Sampling Coverage and Stability Artifacts" in markdown
    assert "## Sample-size Convergence Artifact" in markdown
    assert str(coverage_path) in markdown
    assert str(stability_path) in markdown
    assert str(convergence_path) in markdown
    assert "sampled extended result의 coverage/stability" in markdown
    assert "sampling quality score" in markdown


def test_write_result_report_creates_output_file(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    output_path = tmp_path / "docs" / "result_report.md"
    write_fake_aggregate_results(results_path)

    write_result_report(results_path=results_path, output_path=output_path)

    assert output_path.exists()
    assert "RAST MVP-0 Result Report" in output_path.read_text(encoding="utf-8")


def test_generate_result_report_summarizes_event_fields(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results_with_events.csv"
    fieldnames = [
        "suite_run_id",
        "scenario",
        "seed",
        "apply_policy",
        "event_policy_variant",
        "risk_threshold",
        "near_miss_threshold",
        "collision_threshold",
        "position_noise_std",
        "distance_noise_std",
        "visibility_flip_prob",
        "success",
        "goal_reached",
        "completed_steps",
        "collision_count",
        "near_miss_count",
        "baseline_disagreement_count",
        "rast_vs_object_list_disagreement_count",
        "rast_vs_flat_feature_disagreement_count",
        "object_list_vs_flat_feature_disagreement_count",
        "token_count_avg",
        "object_count_avg",
        "flat_feature_row_count_avg",
        "event_token_count_total",
        "event_token_count_avg",
        "event_type_counts",
        "evidence_token_count_total",
        "evidence_token_count_avg",
        "evidence_type_counts",
        "risk_evidence_count_total",
        "uncertainty_evidence_count_total",
        "event_evidence_count_total",
        "decision_evidence_count_total",
        "decision_evidence_coverage",
        "update_mode",
        "changed_object_count_avg",
        "affected_token_count_avg",
        "full_recompute_latency_avg_ms",
        "incremental_update_latency_avg_ms",
        "incremental_update_benefit_avg",
        "rast_reason_code_counts",
        "object_list_reason_code_counts",
        "flat_feature_reason_code_counts",
        "event_aware_rast_action_counts",
        "event_aware_rast_reason_code_counts",
        "event_policy_variant_action_counts",
        "event_policy_variant_reason_code_counts",
        "rast_trigger_token_count_total",
        "decision_trace_coverage",
        "rast_vs_event_aware_disagreement_count",
        "event_triggered_action_count",
        "event_aware_decision_trace_coverage",
        "latency_avg_ms",
        "latency_p50_ms",
        "latency_p95_ms",
        "token_generation_latency_avg_ms",
        "planning_latency_avg_ms",
        "total_latency_avg_ms",
        "status",
    ]
    rows = [
        {
            "suite_run_id": "suite_test",
            "scenario": "object_appears",
            "seed": "0",
            "apply_policy": "rast",
            "event_policy_variant": "full",
            "risk_threshold": "1.5",
            "near_miss_threshold": "1.0",
            "collision_threshold": "0.2",
            "position_noise_std": "0.02",
            "distance_noise_std": "0.02",
            "visibility_flip_prob": "0.0",
            "success": "True",
            "goal_reached": "False",
            "completed_steps": "5",
            "collision_count": "0",
            "near_miss_count": "1",
            "baseline_disagreement_count": "0",
            "rast_vs_object_list_disagreement_count": "0",
            "rast_vs_flat_feature_disagreement_count": "0",
            "object_list_vs_flat_feature_disagreement_count": "0",
            "token_count_avg": "3.0",
            "object_count_avg": "2.0",
            "flat_feature_row_count_avg": "2.0",
            "event_token_count_total": "2",
            "event_token_count_avg": "0.4",
            "event_type_counts": '{"object_appeared": 1, "risk_changed": 1}',
            "evidence_token_count_total": "5",
            "evidence_token_count_avg": "1.0",
            "evidence_type_counts": '{"risk_feature": 1, "event_diff": 1, "planner_decision": 3}',
            "risk_evidence_count_total": "1",
            "uncertainty_evidence_count_total": "0",
            "event_evidence_count_total": "1",
            "decision_evidence_count_total": "3",
            "decision_evidence_coverage": "1.0",
            "update_mode": "incremental",
            "changed_object_count_avg": "1.0",
            "affected_token_count_avg": "2.0",
            "full_recompute_latency_avg_ms": "0.2",
            "incremental_update_latency_avg_ms": "0.1",
            "incremental_update_benefit_avg": "0.5",
            "rast_reason_code_counts": '{"high_risk_token": 1, "no_risk_move_ahead": 4}',
            "object_list_reason_code_counts": '{"near_object_distance": 1, "no_near_object_move_ahead": 4}',
            "flat_feature_reason_code_counts": '{"within_risk_threshold": 1, "no_risk_scalar_move_ahead": 4}',
            "event_aware_rast_action_counts": '{"Stop": 1, "MoveAhead": 4}',
            "event_aware_rast_reason_code_counts": '{"event_risk_increased": 1, "fallback_no_risk_move_ahead": 4}',
            "event_policy_variant_action_counts": '{"full": {"Stop": 1, "MoveAhead": 4}}',
            "event_policy_variant_reason_code_counts": '{"full": {"event_risk_increased": 1, "fallback_no_risk_move_ahead": 4}}',
            "rast_trigger_token_count_total": "1",
            "decision_trace_coverage": "1.0",
            "rast_vs_event_aware_disagreement_count": "1",
            "event_triggered_action_count": "1",
            "event_aware_decision_trace_coverage": "1.0",
            "latency_avg_ms": "0.3",
            "latency_p50_ms": "0.3",
            "latency_p95_ms": "0.4",
            "token_generation_latency_avg_ms": "0.08",
            "planning_latency_avg_ms": "0.05",
            "total_latency_avg_ms": "0.3",
            "status": "success",
        }
    ]
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    markdown = generate_result_report(results_path=results_path)

    assert "## EventToken Summary" in markdown
    assert "EventToken included in this report: yes" in markdown
    assert "semantic event" in markdown
    assert "object_appeared" in markdown
    assert "risk_changed" in markdown
    assert "## Event-aware Planner Summary" in markdown
    assert "## UncertaintyToken Summary" in markdown
    assert "## Uncertainty-aware Planner Summary" in markdown
    assert "## EvidenceToken Summary" in markdown
    assert "## AffordanceToken Summary" in markdown
    assert "## Replay Trace Summary" in markdown
    assert "## Event-aware Ablation Summary" in markdown
    assert "## Threshold and Noise Sensitivity Summary" in markdown
    assert "event_risk_increased" in markdown
    assert "full" in markdown
    assert "synthetic noise" in markdown
    assert "Event-aware planner는 deterministic rule-based policy" in markdown
    assert "## Incremental Update Summary" in markdown
    assert "incremental update optimization is experimental" in markdown
    assert "incremental" in markdown
    assert "## Decision Trace Summary" in markdown
    assert "## RelationToken Summary" in markdown
    assert "## Scene Graph Baseline Summary" in markdown
    assert "## Scene Graph vs RAST Differentiation Summary" in markdown
    assert "## Affordance-aware Planner Summary" in markdown
    assert "high_risk_token" in markdown
    assert "decision_trace_coverage" in markdown
    assert "planner_decision" in markdown
    assert "Decision evidence coverage" in markdown
    assert "metadata/action trace reconstruction" in markdown
    assert "EventToken affects only the separate Event-aware RAST experimental planner" in markdown
    assert "actual perception uncertainty calibration" in markdown or "실제 perception uncertainty calibration" in markdown


def test_generate_result_report_handles_replay_index(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    replay_index_path = tmp_path / "replays" / "replay_index.json"
    write_fake_aggregate_results(results_path)
    replay_index_path.parent.mkdir()
    replay_index_path.write_text(
        json.dumps(
            {
                "suite_run_id": "suite_test",
                "generated_at": "2026-06-12T00:00:00",
                "replay_count": 1,
                "entries": [
                    {
                        "scenario": "planner_disagreement",
                        "run_dir": "runs/example",
                        "case_type": "rast_vs_scene_graph_disagreement",
                        "step": 2,
                        "markdown_path": "runs/example/replays/planner_disagreement.md",
                        "json_path": "runs/example/replays/planner_disagreement.json",
                        "summary": "selected_action=RotateRight",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    markdown = generate_result_report(results_path=results_path, replay_index_path=replay_index_path)

    assert "## Replay Artifact Summary" in markdown
    assert "replay_index.json" in markdown
    assert "rast_vs_scene_graph_disagreement" in markdown
    assert "runs/example/replays/planner_disagreement.md" in markdown


def test_generate_result_report_without_replay_index_is_backward_compatible(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    write_fake_aggregate_results(results_path)

    markdown = generate_result_report(results_path=results_path)

    assert "## Replay Artifact Summary" in markdown
    assert "No replay artifact index was provided or found." in markdown


def test_generate_result_report_includes_suite_metadata_when_provided(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    metadata_path = tmp_path / "suite_metadata.json"
    write_fake_aggregate_results(results_path)
    metadata_path.write_text(
        json.dumps(
            {
                "suite_run_id": "sampled_suite",
                "config_path": "configs/windows_eval_suite_sampled.yaml",
                "config_name": "windows_eval_suite_sampled",
                "planned_runs_total": 8294400,
                "executed_runs": 500,
                "failed_runs": 0,
                "sampling_mode": "stratified",
                "sample_size": 500,
                "sample_seed": 42,
                "limit": None,
                "allow_large_run": False,
                "replay_export_enabled": True,
                "replay_index_path": "runs/example/replays/replay_index.json",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    markdown = generate_result_report(results_path=results_path, suite_metadata_path=metadata_path)

    assert "## Suite Execution Metadata" in markdown
    assert "planned_runs_total: 8294400" in markdown
    assert "executed_runs: 500" in markdown
    assert "sampling_mode: `stratified`" in markdown
    assert "sample_seed: `42`" in markdown
    assert "sampled subset of the extended grid" in markdown

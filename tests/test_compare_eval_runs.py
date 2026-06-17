import csv
import json
from pathlib import Path

from rast.evaluation.compare_runs import write_eval_comparison_report


def _write_fake_results(path: Path, suite_run_id: str, scenario: str, near_miss: int) -> None:
    fieldnames = [
        "suite_run_id",
        "scenario",
        "apply_policy",
        "success",
        "near_miss_count",
        "latency_avg_ms",
        "token_generation_latency_avg_ms",
        "planning_latency_avg_ms",
        "rast_vs_object_list_disagreement_count",
        "rast_vs_flat_feature_disagreement_count",
        "rast_vs_scene_graph_disagreement_count",
        "rast_vs_event_aware_disagreement_count",
        "rast_vs_uncertainty_aware_disagreement_count",
        "rast_vs_affordance_aware_disagreement_count",
        "event_triggered_action_count",
        "uncertainty_triggered_action_count",
        "affordance_triggered_action_count",
        "evidence_token_count_avg",
        "status",
    ]
    rows = [
        {
            "suite_run_id": suite_run_id,
            "scenario": scenario,
            "apply_policy": "rast",
            "success": "True",
            "near_miss_count": str(near_miss),
            "latency_avg_ms": "0.5",
            "token_generation_latency_avg_ms": "0.1",
            "planning_latency_avg_ms": "0.2",
            "rast_vs_object_list_disagreement_count": "1",
            "rast_vs_flat_feature_disagreement_count": "0",
            "rast_vs_scene_graph_disagreement_count": "2",
            "rast_vs_event_aware_disagreement_count": "1",
            "rast_vs_uncertainty_aware_disagreement_count": "1",
            "rast_vs_affordance_aware_disagreement_count": "3",
            "event_triggered_action_count": "1",
            "uncertainty_triggered_action_count": "1",
            "affordance_triggered_action_count": "2",
            "evidence_token_count_avg": "7",
            "status": "success",
        }
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_compare_eval_runs_writes_sampled_limitation_and_artifact_paths(tmp_path: Path) -> None:
    baseline_results = tmp_path / "baseline.csv"
    candidate_results = tmp_path / "candidate.csv"
    candidate_metadata = tmp_path / "candidate_metadata.json"
    coverage_path = tmp_path / "sampling_coverage_report.md"
    stability_path = tmp_path / "seed_stability_report.md"
    convergence_path = tmp_path / "sample_size_convergence_report.md"
    output = tmp_path / "eval_comparison_report.md"
    _write_fake_results(baseline_results, "baseline_suite", "clear_path", 0)
    _write_fake_results(candidate_results, "candidate_suite", "risk_increases", 2)
    candidate_metadata.write_text(
        json.dumps(
            {
                "suite_run_id": "candidate_suite",
                "sampling_mode": "stratified",
                "sample_size": 500,
                "sample_seed": 42,
                "replay_index_path": "",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    coverage_path.write_text("# coverage\n", encoding="utf-8")
    stability_path.write_text("# stability\n", encoding="utf-8")
    convergence_path.write_text("# convergence\n", encoding="utf-8")

    markdown = write_eval_comparison_report(
        baseline_results=baseline_results,
        baseline_summary=None,
        candidate_results=candidate_results,
        candidate_summary=None,
        candidate_metadata=candidate_metadata,
        candidate_coverage=coverage_path,
        candidate_seed_stability=stability_path,
        candidate_sample_size_convergence=convergence_path,
        output=output,
    )

    assert output.exists()
    assert "## Evaluation Comparison Summary" in markdown
    assert "## Metric Comparison" in markdown
    assert "## Scenario Coverage Comparison" in markdown
    assert "sampled extended result는 exhaustive grid result가 아닙니다" in markdown
    assert "sensitivity exploration" in markdown
    assert str(coverage_path) in markdown
    assert str(stability_path) in markdown
    assert str(convergence_path) in markdown

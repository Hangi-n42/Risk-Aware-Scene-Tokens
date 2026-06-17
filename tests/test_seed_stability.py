import csv
import json
from pathlib import Path

from rast.evaluation.seed_stability import (
    compute_seed_stability,
    generate_seed_stability_report,
    load_seed_sweep_index,
    metric_stability,
    write_seed_stability_report,
)


def _write_seed_results(path: Path, suite_run_id: str, scenario: str, near_miss: int, latency: float) -> None:
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
        "affordance_token_count_avg",
        "status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "suite_run_id": suite_run_id,
                "scenario": scenario,
                "apply_policy": "rast",
                "success": "True",
                "near_miss_count": str(near_miss),
                "latency_avg_ms": str(latency),
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
                "affordance_token_count_avg": "2",
                "status": "success",
            }
        )


def test_seed_sweep_index_schema_and_stability_report(tmp_path: Path) -> None:
    run_a = tmp_path / "seed_7"
    run_b = tmp_path / "seed_13"
    run_a.mkdir()
    run_b.mkdir()
    results_a = run_a / "aggregate_results.csv"
    results_b = run_b / "aggregate_results.csv"
    _write_seed_results(results_a, "suite_seed_7", "clear_path", 1, 0.5)
    _write_seed_results(results_b, "suite_seed_13", "risk_increases", 3, 0.9)
    replay_index = run_b / "replay_index.json"
    replay_index.write_text(json.dumps({"replay_count": 2}, ensure_ascii=False), encoding="utf-8")
    index_path = tmp_path / "seed_sweep_index.json"
    index_path.write_text(
        json.dumps(
            {
                "config_path": "configs/windows_eval_suite_extended.yaml",
                "sample_size": 100,
                "sampling_mode": "stratified",
                "seeds": [7, 13],
                "runs": [
                    {
                        "seed": 7,
                        "run_dir": str(run_a),
                        "aggregate_results": str(results_a),
                        "aggregate_summary": str(run_a / "aggregate_summary.csv"),
                        "suite_metadata": str(run_a / "suite_metadata.json"),
                        "replay_index": "",
                        "failed_runs": 0,
                    },
                    {
                        "seed": 13,
                        "run_dir": str(run_b),
                        "aggregate_results": str(results_b),
                        "aggregate_summary": str(run_b / "aggregate_summary.csv"),
                        "suite_metadata": str(run_b / "suite_metadata.json"),
                        "replay_index": str(replay_index),
                        "failed_runs": 0,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    index = load_seed_sweep_index(index_path)
    rows = compute_seed_stability(index)
    metrics = metric_stability(rows)
    markdown = generate_seed_stability_report(seed_sweep_index_path=index_path)
    output = tmp_path / "seed_stability_report.md"
    write_seed_stability_report(seed_sweep_index_path=index_path, output_path=output)

    assert index["seeds"] == [7, 13]
    assert rows[0]["seed"] == 7
    assert any(item["key"] == "latency_avg_ms" and item["range"] > 0 for item in metrics)
    assert "Seed Stability Summary" in markdown
    assert "Metric Stability Table" in markdown
    assert "High-Variance Metrics" in markdown
    assert output.exists()

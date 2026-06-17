import csv
import json
from pathlib import Path

from rast.evaluation.sample_size_convergence import (
    compute_sample_size_convergence,
    load_sample_size_sweep_index,
    write_sample_size_convergence_report,
)


def test_sample_size_convergence_computes_metric_stats_and_quality_scores(tmp_path: Path) -> None:
    index_path = _write_fake_sample_size_sweep(tmp_path)

    index = load_sample_size_sweep_index(index_path)
    summary = compute_sample_size_convergence(index)

    assert summary["sample_sizes"] == [100, 200]
    assert summary["sample_size_summaries"]["100"]["seed_count"] == 2
    latency_stats = summary["sample_size_summaries"]["100"]["metric_stats"]["latency_avg_ms"]
    assert latency_stats["mean"] > 0
    assert latency_stats["range"] >= 0
    scores = summary["sample_size_summaries"]["100"]["quality_scores"]
    assert 0 <= scores["coverage_score"] <= 1
    assert 0 <= scores["balance_score"] <= 1
    assert 0 <= scores["stability_score"] <= 1
    assert 0 <= scores["overall_sampling_quality_score"] <= 1


def test_event_policy_variant_balance_uses_event_aware_subset(tmp_path: Path) -> None:
    index_path = _write_fake_sample_size_sweep(tmp_path)
    summary = compute_sample_size_convergence(load_sample_size_sweep_index(index_path))

    event_axis = summary["sample_size_summaries"]["100"]["coverage_by_axis"]["event_policy_variant"]

    assert event_axis["coverage_rate_avg"] == 1.0
    assert event_axis["balance_avg"] == 1.0


def test_sample_size_convergence_report_is_written(tmp_path: Path) -> None:
    index_path = _write_fake_sample_size_sweep(tmp_path)
    output = tmp_path / "sample_size_convergence_report.md"

    summary = write_sample_size_convergence_report(
        sample_size_sweep_index_path=index_path,
        output_path=output,
    )

    assert output.exists()
    assert output.with_suffix(".json").exists()
    markdown = output.read_text(encoding="utf-8")
    assert "Sample-size Sweep Summary" in markdown
    assert "Sampling Quality Score" in markdown
    assert "full extended grid exhaustive result" in markdown
    assert summary["sample_size_summaries"]["200"]["seed_count"] == 2


def _write_fake_sample_size_sweep(tmp_path: Path) -> Path:
    runs = []
    for sample_size in (100, 200):
        for seed in (7, 13):
            run_dir = tmp_path / f"sample_{sample_size}_seed_{seed}"
            run_dir.mkdir()
            results = run_dir / "aggregate_results.csv"
            metadata = run_dir / "suite_metadata.json"
            replay = run_dir / "replay_index.json"
            _write_fake_results(results, sample_size=sample_size, seed=seed)
            _write_fake_metadata(metadata)
            replay.write_text(json.dumps({"replay_count": 3}, ensure_ascii=False), encoding="utf-8")
            runs.append(
                {
                    "sample_size": sample_size,
                    "seed": seed,
                    "run_dir": str(run_dir),
                    "aggregate_results": str(results),
                    "aggregate_summary": "",
                    "suite_metadata": str(metadata),
                    "replay_index": str(replay),
                    "failed_runs": 0,
                    "status": "success",
                }
            )
    index = {
        "sample_size_sweep_id": "sample_size_sweep_test",
        "config_path": "configs/windows_eval_suite_extended.yaml",
        "sampling_mode": "stratified",
        "sample_sizes": [100, 200],
        "seeds": [7, 13],
        "runs": runs,
    }
    index_path = tmp_path / "sample_size_sweep_index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index_path


def _write_fake_results(path: Path, *, sample_size: int, seed: int) -> None:
    fieldnames = [
        "suite_run_id",
        "scenario",
        "apply_policy",
        "update_mode",
        "event_policy_variant",
        "risk_threshold",
        "near_miss_threshold",
        "near_agent_relation_threshold",
        "near_path_relation_threshold",
        "blocking_relation_threshold",
        "classification_uncertainty_threshold",
        "position_variance_threshold",
        "occlusion_ratio_threshold",
        "sensor_agreement_threshold",
        "position_noise_std",
        "distance_noise_std",
        "visibility_flip_prob",
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
        "decision_trace_coverage",
        "status",
    ]
    rows = [
        _row(sample_size, seed, "clear_path", "rast", "full", "full_recompute", 1.0, 0),
        _row(sample_size, seed, "risk_increases", "event_aware_rast", "full", "incremental", 1.5, 1),
        _row(sample_size, seed, "object_moves", "event_aware_rast", "no_risk_changed", "incremental", 1.0, 2),
        _row(sample_size, seed, "object_appears", "event_aware_rast", "no_object_moved", "full_recompute", 1.5, 3),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _row(
    sample_size: int,
    seed: int,
    scenario: str,
    policy: str,
    variant: str,
    update_mode: str,
    risk_threshold: float,
    offset: int,
) -> dict[str, str]:
    base = sample_size / 100 + seed / 100 + offset / 10
    return {
        "suite_run_id": f"suite_{sample_size}_{seed}",
        "scenario": scenario,
        "apply_policy": policy,
        "update_mode": update_mode,
        "event_policy_variant": variant,
        "risk_threshold": str(risk_threshold),
        "near_miss_threshold": "0.75",
        "near_agent_relation_threshold": "1.0",
        "near_path_relation_threshold": "0.5",
        "blocking_relation_threshold": "0.35",
        "classification_uncertainty_threshold": "0.4",
        "position_variance_threshold": "0.03",
        "occlusion_ratio_threshold": "0.3",
        "sensor_agreement_threshold": "0.5",
        "position_noise_std": "0.0",
        "distance_noise_std": "0.0",
        "visibility_flip_prob": "0.0",
        "success": "True",
        "near_miss_count": str(offset),
        "latency_avg_ms": str(base),
        "token_generation_latency_avg_ms": str(base / 10),
        "planning_latency_avg_ms": str(base / 20),
        "rast_vs_object_list_disagreement_count": str(offset),
        "rast_vs_flat_feature_disagreement_count": str(offset % 2),
        "rast_vs_scene_graph_disagreement_count": str(offset % 3),
        "rast_vs_event_aware_disagreement_count": str(offset % 2),
        "rast_vs_uncertainty_aware_disagreement_count": str(offset % 2),
        "rast_vs_affordance_aware_disagreement_count": str(offset % 3),
        "event_triggered_action_count": str(offset),
        "uncertainty_triggered_action_count": str(offset % 2),
        "affordance_triggered_action_count": str(offset % 3),
        "evidence_token_count_avg": "7",
        "affordance_token_count_avg": "2",
        "decision_trace_coverage": "1.0",
        "status": "success",
    }


def _write_fake_metadata(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "suite_run_id": "suite_test",
                "axis_summary": {
                    "scenario_values": ["clear_path", "risk_increases", "object_moves", "object_appears"],
                    "apply_policy_values": ["rast", "event_aware_rast"],
                    "update_mode_values": ["full_recompute", "incremental"],
                    "event_policy_variant_values": ["full", "no_risk_changed", "no_object_moved"],
                    "risk_threshold_values": [1.0, 1.5],
                    "near_miss_threshold_values": [0.75],
                    "relation_threshold_values": {"near_agent": [1.0], "near_path": [0.5], "blocking": [0.35]},
                    "uncertainty_threshold_values": {
                        "classification_uncertainty": [0.4],
                        "position_variance": [0.03],
                        "occlusion_ratio": [0.3],
                        "sensor_agreement": [0.5],
                    },
                    "noise_values": [
                        {"position_noise_std": 0.0, "distance_noise_std": 0.0, "visibility_flip_prob": 0.0}
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

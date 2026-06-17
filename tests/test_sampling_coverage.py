import csv
import json
from pathlib import Path

from rast.evaluation.sampling_coverage import analyze_sampling_coverage, write_sampling_coverage_report


def test_sampling_coverage_analyzes_axis_distribution(tmp_path: Path) -> None:
    results = tmp_path / "aggregate_results.csv"
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
        "status",
    ]
    rows = [
        {
            "suite_run_id": "suite_sample",
            "scenario": "clear_path",
            "apply_policy": "rast",
            "update_mode": "full_recompute",
            "event_policy_variant": "full",
            "risk_threshold": "1.0",
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
            "status": "success",
        },
        {
            "suite_run_id": "suite_sample",
            "scenario": "near_obstacle",
            "apply_policy": "scene_graph",
            "update_mode": "incremental",
            "event_policy_variant": "full",
            "risk_threshold": "1.5",
            "near_miss_threshold": "1.0",
            "near_agent_relation_threshold": "1.5",
            "near_path_relation_threshold": "0.75",
            "blocking_relation_threshold": "0.5",
            "classification_uncertainty_threshold": "0.6",
            "position_variance_threshold": "0.05",
            "occlusion_ratio_threshold": "0.5",
            "sensor_agreement_threshold": "0.7",
            "position_noise_std": "0.02",
            "distance_noise_std": "0.02",
            "visibility_flip_prob": "0.05",
            "status": "success",
        },
    ]
    with results.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    metadata = tmp_path / "suite_metadata.json"
    metadata.write_text(
        json.dumps(
            {
                "suite_run_id": "suite_sample",
                "axis_summary": {
                    "scenario_values": ["clear_path", "near_obstacle", "risk_increases"],
                    "apply_policy_values": ["rast", "scene_graph"],
                    "update_mode_values": ["full_recompute", "incremental"],
                    "event_policy_variant_values": ["full"],
                    "risk_threshold_values": [1.0, 1.5, 2.0],
                    "near_miss_threshold_values": [0.75, 1.0],
                    "relation_threshold_values": {"near_agent": [1.0, 1.5], "near_path": [0.5, 0.75], "blocking": [0.35, 0.5]},
                    "uncertainty_threshold_values": {
                        "classification_uncertainty": [0.4, 0.6],
                        "position_variance": [0.03, 0.05],
                        "occlusion_ratio": [0.3, 0.5],
                        "sensor_agreement": [0.5, 0.7],
                    },
                    "noise_values": [
                        {"position_noise_std": 0.0, "distance_noise_std": 0.0, "visibility_flip_prob": 0.0},
                        {"position_noise_std": 0.02, "distance_noise_std": 0.02, "visibility_flip_prob": 0.05},
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    summary = analyze_sampling_coverage(results_path=results, metadata_path=metadata)

    assert summary["row_count"] == 2
    assert summary["axes"]["scenario"]["observed_counts"]["clear_path"] == 1
    assert "risk_increases" in summary["axes"]["scenario"]["missing_values"]
    assert summary["axes"]["risk_threshold"]["coverage_rate"] < 1.0


def test_sampling_coverage_writes_markdown_and_json(tmp_path: Path) -> None:
    results = tmp_path / "aggregate_results.csv"
    with results.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["suite_run_id", "scenario", "apply_policy", "status"])
        writer.writeheader()
        writer.writerow({"suite_run_id": "suite_sample", "scenario": "clear_path", "apply_policy": "rast", "status": "success"})

    output = tmp_path / "sampling_coverage_report.md"
    summary = write_sampling_coverage_report(results_path=results, output_path=output)

    assert summary["suite_run_id"] == "suite_sample"
    assert output.exists()
    assert output.with_suffix(".json").exists()
    markdown = output.read_text(encoding="utf-8")
    assert "RAST Sampling Coverage Report" in markdown
    assert "Axis Coverage" in markdown


def test_sampling_coverage_counts_event_policy_variant_only_for_event_aware_rows(tmp_path: Path) -> None:
    results = tmp_path / "aggregate_results.csv"
    fieldnames = ["suite_run_id", "scenario", "apply_policy", "event_policy_variant", "status"]
    rows = [
        {"suite_run_id": "suite_sample", "scenario": "clear_path", "apply_policy": "rast", "event_policy_variant": "full", "status": "success"},
        {
            "suite_run_id": "suite_sample",
            "scenario": "risk_increases",
            "apply_policy": "event_aware_rast",
            "event_policy_variant": "no_risk_changed",
            "status": "success",
        },
        {
            "suite_run_id": "suite_sample",
            "scenario": "object_moves",
            "apply_policy": "event_aware_rast",
            "event_policy_variant": "no_object_moved",
            "status": "success",
        },
    ]
    with results.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = analyze_sampling_coverage(results_path=results)
    variant_axis = summary["axes"]["event_policy_variant"]

    assert variant_axis["row_scope"] == "`apply_policy=event_aware_rast`"
    assert variant_axis["row_count"] == 2
    assert variant_axis["observed_counts"] == {"no_object_moved": 1, "no_risk_changed": 1}

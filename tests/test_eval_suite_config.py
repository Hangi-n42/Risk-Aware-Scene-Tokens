from pathlib import Path

from experiments.run_windows_eval_suite import count_suite_specs, load_suite_config


def test_extended_eval_suite_config_has_expected_grids() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_extended.yaml"))

    assert "clear_path" in config["scenarios"]
    assert "target_reachable_affordance" in config["scenarios"]
    assert config["risk_thresholds"] == [1.0, 1.5, 2.0]
    assert config["near_miss_thresholds"] == [0.75, 1.0]
    assert config["near_agent_relation_thresholds"] == [1.0, 1.5]
    assert config["near_path_relation_thresholds"] == [0.5, 0.75]
    assert config["blocking_relation_thresholds"] == [0.35, 0.5]
    assert config["classification_uncertainty_thresholds"] == [0.4, 0.6]
    assert config["position_variance_thresholds"] == [0.03, 0.05]
    assert config["occlusion_ratio_thresholds"] == [0.3, 0.5]
    assert config["sensor_agreement_thresholds"] == [0.5, 0.7]
    assert config["position_noise_std"] == [0.0, 0.02, 0.05]
    assert config["distance_noise_std"] == [0.0, 0.02, 0.05]
    assert config["visibility_flip_prob"] == [0.0, 0.05]


def test_sampled_eval_suite_config_is_parseable_and_documented() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_sampled.yaml"))

    assert config["suite_name"] == "windows_eval_suite_sampled"
    assert config["recommended_sample_size"] == 500
    assert config["recommended_sample_seed"] == 42
    assert config["risk_thresholds"] == [1.0, 1.5, 2.0]
    assert "affordance_aware_rast" in config["apply_policies"]


def test_extended_eval_suite_planned_run_count_is_counted_without_materializing_specs() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_extended.yaml"))

    planned_count = count_suite_specs(config)

    assert planned_count > 900

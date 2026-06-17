import json
import subprocess
import sys
from pathlib import Path

from experiments.run_windows_eval_suite import (
    count_suite_specs,
    execution_run_count,
    load_suite_config,
    sample_suite_specs,
    should_block_large_run,
    spec_identity,
)
from collections import Counter


def test_large_run_guard_blocks_unsampled_extended_run() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_extended.yaml"))
    planned_count = count_suite_specs(config)

    assert should_block_large_run(
        planned_runs_total=planned_count,
        dry_run=False,
        limit=None,
        sample_size=None,
        allow_large_run=False,
    )


def test_same_seed_and_sample_size_select_same_subset() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_extended.yaml"))

    first = sample_suite_specs(config, sample_size=20, sample_seed=42, sampling_mode="stratified")
    second = sample_suite_specs(config, sample_size=20, sample_seed=42, sampling_mode="stratified")

    assert [spec_identity(item) for item in first] == [spec_identity(item) for item in second]


def test_different_seed_can_select_different_subset() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_extended.yaml"))

    first = sample_suite_specs(config, sample_size=20, sample_seed=42, sampling_mode="stratified")
    second = sample_suite_specs(config, sample_size=20, sample_seed=7, sampling_mode="stratified")

    assert [spec_identity(item) for item in first] != [spec_identity(item) for item in second]


def test_random_sampling_is_seeded() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_extended.yaml"))

    first = sample_suite_specs(config, sample_size=15, sample_seed=42, sampling_mode="random")
    second = sample_suite_specs(config, sample_size=15, sample_seed=42, sampling_mode="random")

    assert [spec_identity(item) for item in first] == [spec_identity(item) for item in second]


def test_stratified_sampling_balances_event_policy_variants_within_event_aware_subset() -> None:
    config = load_suite_config(Path("configs/windows_eval_suite_extended.yaml"))

    sampled = sample_suite_specs(config, sample_size=500, sample_seed=42, sampling_mode="stratified")
    event_aware = [spec for spec in sampled if spec.apply_policy == "event_aware_rast"]
    counts = Counter(spec.event_policy_variant for spec in event_aware)

    assert set(counts) == set(config["event_policy_variants"])
    assert max(counts.values()) - min(counts.values()) <= 1


def test_limit_reduces_execution_run_count() -> None:
    assert execution_run_count(total_planned_runs=900, sample_size=None, limit=5) == 5
    assert execution_run_count(total_planned_runs=900, sample_size=100, limit=5) == 5


def test_runner_guard_returns_error_for_unsampled_extended_run(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "experiments/run_windows_eval_suite.py",
            "--config",
            "configs/windows_eval_suite_extended.yaml",
            "--output-dir",
            str(tmp_path / "runs"),
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "planned_runs_total" in result.stdout
    assert "너무 큽니다" in result.stdout


def test_runner_limit_writes_suite_metadata(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "experiments/run_windows_eval_suite.py",
            "--config",
            "configs/windows_eval_suite.yaml",
            "--limit",
            "1",
            "--output-dir",
            str(tmp_path / "runs"),
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    suite_dirs = list((tmp_path / "runs").glob("windows_eval_suite_*"))
    assert len(suite_dirs) == 1
    metadata_path = suite_dirs[0] / "suite_metadata.json"
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["planned_runs_total"] == 900
    assert metadata["executed_runs"] == 1
    assert metadata["limit"] == 1
    assert "axis_summary" in metadata

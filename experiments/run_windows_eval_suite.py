"""WindowsMetadataSim multi-run evaluation suite runner입니다."""

from __future__ import annotations

import argparse
import ast
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime
from itertools import islice, product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.run_windows_metadata_sim import run_simulation
from rast.evaluation.aggregate import aggregate_episode_summaries
from rast.evaluation.replay import (
    REPLAY_CASE_PRIORITY,
    load_step_log,
    replay_cases_for_record,
    write_single_step_replay,
)
from rast.evaluation.summarize import summarize_aggregate_results
from rast.simulator.windows_scenarios import build_windows_scenario


DEFAULT_CONFIG_PATH = ROOT / "configs" / "windows_eval_suite.yaml"
LARGE_RUN_GUARD_THRESHOLD = 50_000


@dataclass(frozen=True)
class SuiteRunSpec:
    """Evaluation suite의 단일 episode run 조합입니다."""

    scenario: str
    seed: int
    risk_threshold: float
    near_agent_relation_threshold: float
    near_path_relation_threshold: float
    blocking_relation_threshold: float
    near_miss_threshold: float
    collision_threshold: float
    apply_policy: str
    event_policy_variant: str
    update_mode: str
    position_noise_std: float
    distance_noise_std: float
    visibility_flip_prob: float
    classification_uncertainty_threshold: float
    position_variance_threshold: float
    occlusion_ratio_threshold: float
    sensor_agreement_threshold: float
    max_steps: int


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WindowsMetadataSim multi-run evaluation suite")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--sample-seed", type=int, default=42)
    parser.add_argument("--sampling-mode", choices=("stratified", "random"), default="stratified")
    parser.add_argument("--allow-large-run", action="store_true")
    parser.add_argument("--export-replays", action="store_true")
    parser.add_argument("--max-replays-per-suite", type=int, default=10)
    parser.add_argument("--replay-output-dir", default=None)
    args = parser.parse_args()

    config = load_suite_config(Path(args.config))
    suite_run_id = f"windows_eval_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_root = Path(str(args.output_dir or config.get("output_dir", "runs/windows_eval_suite")))
    suite_output_dir = output_root / suite_run_id
    config_path = Path(args.config)
    total_planned_runs = count_suite_specs(config)
    planned_runs = execution_run_count(
        total_planned_runs=total_planned_runs,
        sample_size=args.sample_size,
        limit=args.limit,
    )
    warning_threshold = int(config.get("large_run_warning_threshold", 5000))

    print(f"suite_run_id={suite_run_id}")
    print(f"planned_runs={planned_runs}")
    print(f"planned_runs_total={total_planned_runs}")
    if args.limit is not None:
        print(f"total_config_runs={total_planned_runs}")
    if planned_runs > warning_threshold:
        print(
            f"[warning] planned_runs={planned_runs} exceeds large_run_warning_threshold={warning_threshold}. "
            "실행은 계속 가능하지만 extended config는 dry-run으로 먼저 확인하는 것을 권장합니다."
        )
    if should_block_large_run(
        planned_runs_total=total_planned_runs,
        dry_run=args.dry_run,
        limit=args.limit,
        sample_size=args.sample_size,
        allow_large_run=args.allow_large_run,
    ):
        print(
            "[error] planned_runs_total이 너무 큽니다. --dry-run, --sample-size, --limit, "
            "또는 --allow-large-run 중 하나를 명시해야 실행합니다."
        )
        return 2
    if args.dry_run:
        print("dry_run=true")
        print("episodes_executed=0")
        suite_output_dir.mkdir(parents=True, exist_ok=True)
        write_suite_metadata(
            suite_output_dir / "suite_metadata.json",
            suite_run_id=suite_run_id,
            config=config,
            config_path=config_path,
            generated_at=datetime.now().isoformat(timespec="seconds"),
            planned_runs_total=total_planned_runs,
            executed_runs=0,
            failed_runs=0,
            dry_run=True,
            sample_size=args.sample_size,
            sample_seed=args.sample_seed,
            sampling_mode=args.sampling_mode,
            limit=args.limit,
            allow_large_run=args.allow_large_run,
            replay_export_enabled=args.export_replays,
            replay_index_path=None,
        )
        for index, spec in enumerate(
            islice(
                selected_specs_for_execution(
                    config,
                    sample_size=args.sample_size,
                    sample_seed=args.sample_seed,
                    sampling_mode=args.sampling_mode,
                    limit=args.limit,
                ),
                min(planned_runs, 5),
            )
        ):
            print(f"sample_{index:03d}: {spec}")
        print(f"suite_metadata: {(suite_output_dir / 'suite_metadata.json').resolve()}")
        return 0

    spec_iter = selected_specs_for_execution(
        config,
        sample_size=args.sample_size,
        sample_seed=args.sample_seed,
        sampling_mode=args.sampling_mode,
        limit=args.limit,
    )

    run_metadata: list[dict[str, Any]] = []
    for index, spec in enumerate(spec_iter):
        run_dir = suite_output_dir / run_directory_name(index, spec)
        run_dir.mkdir(parents=True, exist_ok=True)
        output_path = run_dir / "step_log.jsonl"
        metadata = base_run_metadata(
            suite_run_id=suite_run_id,
            spec=spec,
            episode_output_dir=run_dir,
        )
        metadata["step_log_path"] = str(output_path)
        try:
            scenario = build_windows_scenario(spec.scenario)
            run_simulation(
                sim=scenario.simulator,
                scenario_name=scenario.name,
                max_steps=spec.max_steps,
                risk_threshold=spec.risk_threshold,
                object_list_threshold=scenario.object_list_threshold,
                near_agent_relation_threshold=spec.near_agent_relation_threshold,
                near_path_relation_threshold=spec.near_path_relation_threshold,
                blocking_relation_threshold=spec.blocking_relation_threshold,
                collision_threshold=spec.collision_threshold,
                near_miss_threshold=spec.near_miss_threshold,
                update_mode=spec.update_mode,
                apply_policy=spec.apply_policy,
                event_policy_variant=spec.event_policy_variant,
                seed=spec.seed,
                position_noise_std=spec.position_noise_std,
                distance_noise_std=spec.distance_noise_std,
                visibility_flip_prob=spec.visibility_flip_prob,
                classification_uncertainty_threshold=spec.classification_uncertainty_threshold,
                position_variance_threshold=spec.position_variance_threshold,
                occlusion_ratio_threshold=spec.occlusion_ratio_threshold,
                sensor_agreement_threshold=spec.sensor_agreement_threshold,
                output_path=output_path,
                goal=scenario.goal,
            )
            metadata["status"] = "success"
            metadata["summary_path"] = str(run_dir / "episode_summary.json")
            print(
                f"[ok] {index + 1}/{planned_runs} {spec.scenario} seed={spec.seed} "
                f"policy={spec.apply_policy} event_policy={spec.event_policy_variant} update_mode={spec.update_mode}"
            )
        except Exception as exc:  # suite infrastructure는 실패 run을 aggregate에 남깁니다.
            metadata["status"] = "failed"
            metadata["error"] = str(exc)
            failure_path = run_dir / "failure.json"
            failure_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(
                f"[failed] {index + 1}/{planned_runs} {spec.scenario} seed={spec.seed} "
                f"event_policy={spec.event_policy_variant} update_mode={spec.update_mode}: {exc}"
            )
        run_metadata.append(metadata)

    rows = aggregate_episode_summaries(run_metadata, output_dir=suite_output_dir)
    summarize_aggregate_results(rows, output_dir=suite_output_dir)
    replay_index_path: Path | None = None
    if args.export_replays:
        replay_output_dir = (
            Path(args.replay_output_dir)
            if args.replay_output_dir is not None
            else suite_output_dir / "replays"
        )
        replay_index_path = export_suite_replays(
            run_metadata,
            suite_run_id=suite_run_id,
            output_dir=replay_output_dir,
            max_replays=args.max_replays_per_suite,
        )
        print(f"replay_index: {replay_index_path.resolve()}")
    failed_count = sum(1 for row in rows if row.get("status") != "success")
    suite_metadata_path = suite_output_dir / "suite_metadata.json"
    write_suite_metadata(
        suite_metadata_path,
        suite_run_id=suite_run_id,
        config=config,
        config_path=config_path,
        generated_at=datetime.now().isoformat(timespec="seconds"),
        planned_runs_total=total_planned_runs,
        executed_runs=len(run_metadata),
        failed_runs=failed_count,
        dry_run=False,
        sample_size=args.sample_size,
        sample_seed=args.sample_seed,
        sampling_mode=args.sampling_mode,
        limit=args.limit,
        allow_large_run=args.allow_large_run,
        replay_export_enabled=args.export_replays,
        replay_index_path=str(replay_index_path) if replay_index_path is not None else None,
    )
    print(f"aggregate_results: {(suite_output_dir / 'aggregate_results.csv').resolve()}")
    print(f"aggregate_summary: {(suite_output_dir / 'aggregate_summary.csv').resolve()}")
    print(f"suite_metadata: {suite_metadata_path.resolve()}")
    print(f"failed_runs={failed_count}")
    return 0


def build_suite_specs(config: dict[str, Any]) -> list[SuiteRunSpec]:
    """config의 scenario × seed × threshold × apply_policy 조합을 생성합니다."""

    return list(iter_suite_specs(config))


def selected_specs_for_execution(
    config: dict[str, Any],
    *,
    sample_size: int | None,
    sample_seed: int,
    sampling_mode: str,
    limit: int | None,
):
    """CLI 옵션에 맞춰 실행할 spec iterator/list를 반환합니다."""

    if sample_size is not None:
        specs = sample_suite_specs(
            config,
            sample_size=sample_size,
            sample_seed=sample_seed,
            sampling_mode=sampling_mode,
        )
        return iter(specs[:limit] if limit is not None else specs)
    if limit is not None:
        return islice(iter_suite_specs(config), limit)
    return iter_suite_specs(config)


def sample_suite_specs(
    config: dict[str, Any],
    *,
    sample_size: int,
    sample_seed: int = 42,
    sampling_mode: str = "stratified",
) -> list[SuiteRunSpec]:
    """extended grid에서 deterministic subset을 선택합니다."""

    total = count_suite_specs(config)
    target_size = max(0, min(sample_size, total))
    if target_size == 0:
        return []
    if target_size >= total and total <= LARGE_RUN_GUARD_THRESHOLD:
        return build_suite_specs(config)

    rng = random.Random(sample_seed)
    if sampling_mode == "random":
        return _random_sample_suite_specs(config, sample_size=target_size, rng=rng)
    if sampling_mode == "stratified":
        return _stratified_sample_suite_specs(config, sample_size=target_size, rng=rng)
    raise ValueError(f"지원하지 않는 sampling_mode입니다: {sampling_mode}")


def _random_sample_suite_specs(config: dict[str, Any], *, sample_size: int, rng: random.Random) -> list[SuiteRunSpec]:
    axes = _suite_axes(config)
    specs: list[SuiteRunSpec] = []
    seen: set[tuple[Any, ...]] = set()
    attempts = 0
    max_attempts = max(sample_size * 50, 1000)
    while len(specs) < sample_size and attempts < max_attempts:
        attempts += 1
        spec = _make_spec_from_axes(
            axes=axes,
            config=config,
            rng=rng,
            scenario=rng.choice(axes["scenarios"]),
            seed=rng.choice(axes["seeds"]),
            risk_threshold=rng.choice(axes["risk_thresholds"]),
            near_agent_relation=rng.choice(axes["near_agent_relation_thresholds"]),
            near_path_relation=rng.choice(axes["near_path_relation_thresholds"]),
            blocking_relation=rng.choice(axes["blocking_relation_thresholds"]),
            near_miss_threshold=rng.choice(axes["near_miss_thresholds"]),
            apply_policy=rng.choice(axes["apply_policies"]),
            update_mode=rng.choice(axes["update_modes"]),
            noise=rng.choice(axes["noise_settings"]),
            classification_uncertainty_threshold=rng.choice(axes["classification_uncertainty_thresholds"]),
            position_variance_threshold=rng.choice(axes["position_variance_thresholds"]),
            occlusion_ratio_threshold=rng.choice(axes["occlusion_ratio_thresholds"]),
            sensor_agreement_threshold=rng.choice(axes["sensor_agreement_thresholds"]),
            event_policy_variant=None,
        )
        identity = spec_identity(spec)
        if identity in seen:
            continue
        seen.add(identity)
        specs.append(spec)
    return specs


def _stratified_sample_suite_specs(
    config: dict[str, Any],
    *,
    sample_size: int,
    rng: random.Random,
) -> list[SuiteRunSpec]:
    axes = _suite_axes(config)
    scenario_cycle = _shuffled(axes["scenarios"], rng)
    policy_cycle = _shuffled(axes["apply_policies"], rng)
    update_cycle = _shuffled(axes["update_modes"], rng)
    risk_cycle = _shuffled(axes["risk_thresholds"], rng)
    noise_cycle = _shuffled(axes["noise_settings"], rng)
    event_variant_cycle = _shuffled(axes["event_policy_variants"], rng)
    specs: list[SuiteRunSpec] = []
    seen: set[tuple[Any, ...]] = set()
    index = 0
    event_aware_index = 0
    max_attempts = max(sample_size * 100, 1000)
    while len(specs) < sample_size and index < max_attempts:
        scenario = scenario_cycle[index % len(scenario_cycle)]
        apply_policy = policy_cycle[(index // len(scenario_cycle)) % len(policy_cycle)]
        update_mode = update_cycle[(index // max(1, len(scenario_cycle) * len(policy_cycle))) % len(update_cycle)]
        risk_threshold = risk_cycle[index % len(risk_cycle)]
        noise = noise_cycle[(index // max(1, len(risk_cycle))) % len(noise_cycle)]
        event_policy_variant = None
        if apply_policy == "event_aware_rast":
            # event-aware planner 안에서는 variant 축도 deterministic하게 순환시킵니다.
            event_policy_variant = event_variant_cycle[event_aware_index % len(event_variant_cycle)]
            event_aware_index += 1
        spec = _make_spec_from_axes(
            axes=axes,
            config=config,
            rng=rng,
            scenario=scenario,
            seed=rng.choice(axes["seeds"]),
            risk_threshold=risk_threshold,
            near_agent_relation=rng.choice(axes["near_agent_relation_thresholds"]),
            near_path_relation=rng.choice(axes["near_path_relation_thresholds"]),
            blocking_relation=rng.choice(axes["blocking_relation_thresholds"]),
            near_miss_threshold=rng.choice(axes["near_miss_thresholds"]),
            apply_policy=apply_policy,
            update_mode=update_mode,
            noise=noise,
            classification_uncertainty_threshold=rng.choice(axes["classification_uncertainty_thresholds"]),
            position_variance_threshold=rng.choice(axes["position_variance_thresholds"]),
            occlusion_ratio_threshold=rng.choice(axes["occlusion_ratio_thresholds"]),
            sensor_agreement_threshold=rng.choice(axes["sensor_agreement_thresholds"]),
            event_policy_variant=event_policy_variant,
        )
        identity = spec_identity(spec)
        if identity not in seen:
            seen.add(identity)
            specs.append(spec)
        index += 1
    return specs


def _make_spec_from_axes(
    *,
    axes: dict[str, list[Any]],
    config: dict[str, Any],
    rng: random.Random,
    scenario: str,
    seed: int,
    risk_threshold: float,
    near_agent_relation: float | None,
    near_path_relation: float | None,
    blocking_relation: float | None,
    near_miss_threshold: float,
    apply_policy: str,
    update_mode: str,
    noise: dict[str, float],
    classification_uncertainty_threshold: float,
    position_variance_threshold: float,
    occlusion_ratio_threshold: float,
    sensor_agreement_threshold: float,
    event_policy_variant: str | None = None,
) -> SuiteRunSpec:
    scenario_defaults = build_windows_scenario(scenario)
    variants = axes["event_policy_variants"] if apply_policy == "event_aware_rast" else ["full"]
    resolved_event_policy_variant = event_policy_variant if event_policy_variant is not None else rng.choice(variants)
    return SuiteRunSpec(
        scenario=scenario,
        seed=int(seed),
        risk_threshold=float(risk_threshold),
        near_agent_relation_threshold=(
            scenario_defaults.resolved_near_agent_relation_threshold
            if near_agent_relation is None
            else float(near_agent_relation)
        ),
        near_path_relation_threshold=(
            scenario_defaults.resolved_near_path_relation_threshold
            if near_path_relation is None
            else float(near_path_relation)
        ),
        blocking_relation_threshold=(
            scenario_defaults.resolved_blocking_relation_threshold
            if blocking_relation is None
            else float(blocking_relation)
        ),
        near_miss_threshold=float(near_miss_threshold),
        collision_threshold=float(config.get("collision_threshold", 0.2)),
        apply_policy=apply_policy,
        event_policy_variant=resolved_event_policy_variant,
        update_mode=update_mode,
        position_noise_std=float(noise.get("position_noise_std", 0.0)),
        distance_noise_std=float(noise.get("distance_noise_std", 0.0)),
        visibility_flip_prob=float(noise.get("visibility_flip_prob", 0.0)),
        classification_uncertainty_threshold=float(classification_uncertainty_threshold),
        position_variance_threshold=float(position_variance_threshold),
        occlusion_ratio_threshold=float(occlusion_ratio_threshold),
        sensor_agreement_threshold=float(sensor_agreement_threshold),
        max_steps=int(config.get("max_steps", 10)),
    )


def _shuffled(items: list[Any], rng: random.Random) -> list[Any]:
    copied = list(items)
    rng.shuffle(copied)
    return copied


def spec_identity(spec: SuiteRunSpec) -> tuple[Any, ...]:
    return (
        spec.scenario,
        spec.seed,
        spec.risk_threshold,
        spec.near_agent_relation_threshold,
        spec.near_path_relation_threshold,
        spec.blocking_relation_threshold,
        spec.near_miss_threshold,
        spec.collision_threshold,
        spec.apply_policy,
        spec.event_policy_variant,
        spec.update_mode,
        spec.position_noise_std,
        spec.distance_noise_std,
        spec.visibility_flip_prob,
        spec.classification_uncertainty_threshold,
        spec.position_variance_threshold,
        spec.occlusion_ratio_threshold,
        spec.sensor_agreement_threshold,
        spec.max_steps,
    )


def execution_run_count(
    *,
    total_planned_runs: int,
    sample_size: int | None,
    limit: int | None,
) -> int:
    count = min(total_planned_runs, sample_size) if sample_size is not None else total_planned_runs
    return min(count, limit) if limit is not None else count


def should_block_large_run(
    *,
    planned_runs_total: int,
    dry_run: bool,
    limit: int | None,
    sample_size: int | None,
    allow_large_run: bool,
    threshold: int = LARGE_RUN_GUARD_THRESHOLD,
) -> bool:
    return (
        planned_runs_total > threshold
        and not dry_run
        and limit is None
        and sample_size is None
        and not allow_large_run
    )


def count_suite_specs(config: dict[str, Any]) -> int:
    """extended config도 메모리에 올리지 않고 planned run 수만 계산합니다."""

    axes = _suite_axes(config)
    policy_variant_count = sum(
        len(axes["event_policy_variants"]) if policy == "event_aware_rast" else 1
        for policy in axes["apply_policies"]
    )
    return (
        len(axes["scenarios"])
        * len(axes["seeds"])
        * len(axes["risk_thresholds"])
        * len(axes["near_agent_relation_thresholds"])
        * len(axes["near_path_relation_thresholds"])
        * len(axes["blocking_relation_thresholds"])
        * len(axes["near_miss_thresholds"])
        * policy_variant_count
        * len(axes["update_modes"])
        * len(axes["noise_settings"])
        * len(axes["classification_uncertainty_thresholds"])
        * len(axes["position_variance_thresholds"])
        * len(axes["occlusion_ratio_thresholds"])
        * len(axes["sensor_agreement_thresholds"])
    )


def iter_suite_specs(config: dict[str, Any]):
    """SuiteRunSpec을 streaming 방식으로 생성합니다."""

    axes = _suite_axes(config)
    max_steps = int(config.get("max_steps", 10))
    collision_threshold = float(config.get("collision_threshold", 0.2))

    for (
        scenario,
        seed,
        risk_threshold,
        near_agent_relation,
        near_path_relation,
        blocking_relation,
        near_miss_threshold,
        apply_policy,
        update_mode,
        noise,
        classification_uncertainty_threshold,
        position_variance_threshold,
        occlusion_ratio_threshold,
        sensor_agreement_threshold,
    ) in product(
        axes["scenarios"],
        axes["seeds"],
        axes["risk_thresholds"],
        axes["near_agent_relation_thresholds"],
        axes["near_path_relation_thresholds"],
        axes["blocking_relation_thresholds"],
        axes["near_miss_thresholds"],
        axes["apply_policies"],
        axes["update_modes"],
        axes["noise_settings"],
        axes["classification_uncertainty_thresholds"],
        axes["position_variance_thresholds"],
        axes["occlusion_ratio_thresholds"],
        axes["sensor_agreement_thresholds"],
    ):
        scenario_defaults = build_windows_scenario(scenario)
        resolved_near_agent_relation = (
            scenario_defaults.resolved_near_agent_relation_threshold
            if near_agent_relation is None
            else near_agent_relation
        )
        resolved_near_path_relation = (
            scenario_defaults.resolved_near_path_relation_threshold
            if near_path_relation is None
            else near_path_relation
        )
        resolved_blocking_relation = (
            scenario_defaults.resolved_blocking_relation_threshold
            if blocking_relation is None
            else blocking_relation
        )
        variants = axes["event_policy_variants"] if apply_policy == "event_aware_rast" else ["full"]
        for event_policy_variant in variants:
            yield SuiteRunSpec(
                scenario=scenario,
                seed=seed,
                risk_threshold=risk_threshold,
                near_agent_relation_threshold=resolved_near_agent_relation,
                near_path_relation_threshold=resolved_near_path_relation,
                blocking_relation_threshold=resolved_blocking_relation,
                near_miss_threshold=near_miss_threshold,
                collision_threshold=collision_threshold,
                apply_policy=apply_policy,
                event_policy_variant=event_policy_variant,
                update_mode=update_mode,
                position_noise_std=float(noise.get("position_noise_std", 0.0)),
                distance_noise_std=float(noise.get("distance_noise_std", 0.0)),
                visibility_flip_prob=float(noise.get("visibility_flip_prob", 0.0)),
                classification_uncertainty_threshold=classification_uncertainty_threshold,
                position_variance_threshold=position_variance_threshold,
                occlusion_ratio_threshold=occlusion_ratio_threshold,
                sensor_agreement_threshold=sensor_agreement_threshold,
                max_steps=max_steps,
            )


def _suite_axes(config: dict[str, Any]) -> dict[str, list[Any]]:
    """suite config의 반복 축을 표준 list로 정규화합니다."""

    scenarios = [str(item) for item in _as_list(config.get("scenarios", ["clear_path"]))]
    seeds = [int(item) for item in _as_list(config.get("seeds", [0]))]
    risk_thresholds = [float(item) for item in _as_list(config.get("risk_thresholds", [1.5]))]
    near_agent_relation_thresholds = _optional_float_list(config.get("near_agent_relation_thresholds", []))
    near_path_relation_thresholds = _optional_float_list(config.get("near_path_relation_thresholds", []))
    near_miss_thresholds = [float(item) for item in _as_list(config.get("near_miss_thresholds", [1.0]))]
    blocking_relation_thresholds = _optional_float_list(config.get("blocking_relation_thresholds", []))
    apply_policies = [str(item) for item in _as_list(config.get("apply_policies", ["rast"]))]
    event_policy_variants = [str(item) for item in _as_list(config.get("event_policy_variants", ["full"]))]
    update_modes = [str(item) for item in _as_list(config.get("update_modes", ["full_recompute"]))]
    noise_settings = _noise_settings_from_config(config)
    return {
        "scenarios": scenarios,
        "seeds": seeds,
        "risk_thresholds": risk_thresholds,
        "near_agent_relation_thresholds": near_agent_relation_thresholds,
        "near_path_relation_thresholds": near_path_relation_thresholds,
        "blocking_relation_thresholds": blocking_relation_thresholds,
        "near_miss_thresholds": near_miss_thresholds,
        "apply_policies": apply_policies,
        "event_policy_variants": event_policy_variants,
        "update_modes": update_modes,
        "noise_settings": noise_settings,
        "classification_uncertainty_thresholds": _float_axis(
            config,
            plural_key="classification_uncertainty_thresholds",
            singular_key="classification_uncertainty_threshold",
            default=0.5,
        ),
        "position_variance_thresholds": _float_axis(
            config,
            plural_key="position_variance_thresholds",
            singular_key="position_variance_threshold",
            default=0.2,
        ),
        "occlusion_ratio_thresholds": _float_axis(
            config,
            plural_key="occlusion_ratio_thresholds",
            singular_key="occlusion_ratio_threshold",
            default=0.5,
        ),
        "sensor_agreement_thresholds": _float_axis(
            config,
            plural_key="sensor_agreement_thresholds",
            singular_key="sensor_agreement_threshold",
            default=0.6,
        ),
    }


def base_run_metadata(*, suite_run_id: str, spec: SuiteRunSpec, episode_output_dir: Path) -> dict[str, Any]:
    """aggregate row에 필요한 run metadata를 구성합니다."""

    return {
        "suite_run_id": suite_run_id,
        "scenario": spec.scenario,
        "seed": spec.seed,
        "apply_policy": spec.apply_policy,
        "event_policy_variant": spec.event_policy_variant,
        "update_mode": spec.update_mode,
        "risk_threshold": spec.risk_threshold,
        "near_agent_relation_threshold": spec.near_agent_relation_threshold,
        "near_path_relation_threshold": spec.near_path_relation_threshold,
        "blocking_relation_threshold": spec.blocking_relation_threshold,
        "near_miss_threshold": spec.near_miss_threshold,
        "collision_threshold": spec.collision_threshold,
        "position_noise_std": spec.position_noise_std,
        "distance_noise_std": spec.distance_noise_std,
        "visibility_flip_prob": spec.visibility_flip_prob,
        "classification_uncertainty_threshold": spec.classification_uncertainty_threshold,
        "position_variance_threshold": spec.position_variance_threshold,
        "occlusion_ratio_threshold": spec.occlusion_ratio_threshold,
        "sensor_agreement_threshold": spec.sensor_agreement_threshold,
        "episode_output_dir": str(episode_output_dir),
        "summary_path": str(episode_output_dir / "episode_summary.json"),
        "status": "pending",
        "error": "",
    }


def build_suite_metadata(
    *,
    suite_run_id: str,
    config: dict[str, Any],
    config_path: Path,
    generated_at: str,
    planned_runs_total: int,
    executed_runs: int,
    failed_runs: int,
    dry_run: bool,
    sample_size: int | None,
    sample_seed: int,
    sampling_mode: str,
    limit: int | None,
    allow_large_run: bool,
    replay_export_enabled: bool,
    replay_index_path: str | None,
) -> dict[str, Any]:
    """suite 실행 조건과 축 요약을 metadata로 구성합니다."""

    axes = _suite_axes(config)
    return {
        "suite_run_id": suite_run_id,
        "config_path": str(config_path),
        "config_name": str(config.get("suite_name") or config_path.stem),
        "generated_at": generated_at,
        "planned_runs_total": planned_runs_total,
        "executed_runs": executed_runs,
        "failed_runs": failed_runs,
        "dry_run": dry_run,
        "sample_size": sample_size,
        "sample_seed": sample_seed,
        "sampling_mode": sampling_mode,
        "limit": limit,
        "allow_large_run": allow_large_run,
        "axis_summary": {
            "scenario_count": len(axes["scenarios"]),
            "scenario_values": axes["scenarios"],
            "apply_policy_count": len(axes["apply_policies"]),
            "apply_policy_values": axes["apply_policies"],
            "update_mode_count": len(axes["update_modes"]),
            "update_mode_values": axes["update_modes"],
            "event_policy_variant_count": len(axes["event_policy_variants"]),
            "event_policy_variant_values": axes["event_policy_variants"],
            "risk_threshold_values": axes["risk_thresholds"],
            "near_miss_threshold_values": axes["near_miss_thresholds"],
            "relation_threshold_values": {
                "near_agent": axes["near_agent_relation_thresholds"],
                "near_path": axes["near_path_relation_thresholds"],
                "blocking": axes["blocking_relation_thresholds"],
            },
            "uncertainty_threshold_values": {
                "classification_uncertainty": axes["classification_uncertainty_thresholds"],
                "position_variance": axes["position_variance_thresholds"],
                "occlusion_ratio": axes["occlusion_ratio_thresholds"],
                "sensor_agreement": axes["sensor_agreement_thresholds"],
            },
            "noise_values": axes["noise_settings"],
        },
        "replay_export_enabled": replay_export_enabled,
        "replay_index_path": replay_index_path,
    }


def write_suite_metadata(path: str | Path, **kwargs: Any) -> dict[str, Any]:
    """suite_metadata.json을 저장하고 payload를 반환합니다."""

    payload = build_suite_metadata(**kwargs)
    metadata_path = Path(path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def export_suite_replays(
    run_metadata: list[dict[str, Any]],
    *,
    suite_run_id: str,
    output_dir: str | Path,
    max_replays: int,
) -> Path:
    """suite 전체에서 대표 replay step을 뽑아 index와 artifact를 저장합니다."""

    replay_dir = Path(output_dir)
    replay_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[dict[str, Any]] = []
    priority = {case: index for index, case in enumerate(REPLAY_CASE_PRIORITY)}

    for metadata in run_metadata:
        if metadata.get("status") != "success":
            continue
        step_log_path = Path(str(metadata.get("step_log_path") or Path(str(metadata.get("episode_output_dir", ""))) / "step_log.jsonl"))
        if not step_log_path.exists():
            continue
        try:
            records = load_step_log(step_log_path)
        except (OSError, json.JSONDecodeError):
            continue
        for record in records:
            cases = replay_cases_for_record(record)
            for case_type in cases:
                if case_type not in priority:
                    continue
                candidates.append(
                    {
                        "priority": priority[case_type],
                        "case_type": case_type,
                        "record": record,
                        "scenario": metadata.get("scenario", (record.get("extra") or {}).get("scenario", "")),
                        "run_dir": str(metadata.get("episode_output_dir", "")),
                        "step_log_path": str(step_log_path),
                    }
                )

    candidates.sort(
        key=lambda item: (
            item["priority"],
            str(item["scenario"]),
            str(item["run_dir"]),
            int(item["record"].get("step", 0) or 0),
        )
    )
    selected = select_replay_candidates(candidates, max_replays=max_replays)
    entries: list[dict[str, Any]] = []
    used_names: set[str] = set()
    for index, candidate in enumerate(selected):
        record = candidate["record"]
        scenario = _safe_name(str(candidate["scenario"] or "scenario"))
        case_type = _safe_name(str(candidate["case_type"]))
        step = int(record.get("step", 0) or 0)
        base_name = f"{scenario}_{case_type}_step{step}"
        name = base_name
        if name in used_names:
            name = f"{base_name}_{index:02d}"
        used_names.add(name)
        md_path = replay_dir / f"{name}.md"
        json_path = replay_dir / f"{name}.json"
        payload = write_single_step_replay(
            record=record,
            case_type=str(candidate["case_type"]),
            output_md_path=md_path,
            output_json_path=json_path,
            suite_run_id=suite_run_id,
            run_dir=str(candidate["run_dir"]),
        )
        entries.append(
            {
                "scenario": candidate["scenario"],
                "run_dir": candidate["run_dir"],
                "case_type": candidate["case_type"],
                "step": step,
                "markdown_path": str(md_path),
                "json_path": str(json_path),
                "summary": _replay_entry_summary(payload),
            }
        )

    index_payload = {
        "suite_run_id": suite_run_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "replay_count": len(entries),
        "entries": entries,
    }
    index_path = replay_dir / "replay_index.json"
    index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index_path


def select_replay_candidates(candidates: list[dict[str, Any]], *, max_replays: int) -> list[dict[str, Any]]:
    """우선순위를 지키면서 case type 다양성을 먼저 확보합니다."""

    if max_replays <= 0:
        return []
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str, int]] = set()
    seen_case_types: set[str] = set()

    for candidate in candidates:
        case_type = str(candidate["case_type"])
        if case_type in seen_case_types:
            continue
        selected.append(candidate)
        seen_case_types.add(case_type)
        selected_keys.add(_candidate_key(candidate))
        if len(selected) >= max_replays:
            return selected

    for candidate in candidates:
        key = _candidate_key(candidate)
        if key in selected_keys:
            continue
        selected.append(candidate)
        selected_keys.add(key)
        if len(selected) >= max_replays:
            break
    return selected


def _candidate_key(candidate: dict[str, Any]) -> tuple[str, str, int]:
    record = candidate["record"]
    return (str(candidate["run_dir"]), str(candidate["case_type"]), int(record.get("step", 0) or 0))


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)


def _replay_entry_summary(payload: dict[str, Any]) -> str:
    steps = payload.get("steps", [])
    if not steps:
        return "No step payload."
    step = steps[0]
    reasons = step.get("reason_codes", {})
    action = step.get("selected_action", "")
    return f"selected_action={action}; reason_codes={json.dumps(reasons, ensure_ascii=False, sort_keys=True)}"


def run_directory_name(index: int, spec: SuiteRunSpec) -> str:
    """파일시스템에 안전한 run directory 이름을 만듭니다."""

    risk = str(spec.risk_threshold).replace(".", "p")
    near = str(spec.near_miss_threshold).replace(".", "p")
    rel_agent = str(spec.near_agent_relation_threshold).replace(".", "p")
    rel_path = str(spec.near_path_relation_threshold).replace(".", "p")
    rel_block = str(spec.blocking_relation_threshold).replace(".", "p")
    pos_noise = str(spec.position_noise_std).replace(".", "p")
    dist_noise = str(spec.distance_noise_std).replace(".", "p")
    vis_noise = str(spec.visibility_flip_prob).replace(".", "p")
    return (
        f"{index:04d}_scenario-{spec.scenario}_seed-{spec.seed}_"
        f"risk-{risk}_rel-{rel_agent}-{rel_path}-{rel_block}_near-{near}_"
        f"policy-{spec.apply_policy}_event-{spec.event_policy_variant}_"
        f"noise-p{pos_noise}-d{dist_noise}-v{vis_noise}_update-{spec.update_mode}"
    )


def load_suite_config(path: Path) -> dict[str, Any]:
    """PyYAML이 있으면 사용하고, 없으면 현재 suite config에 필요한 subset만 파싱합니다."""

    if not path.exists():
        raise FileNotFoundError(f"evaluation suite config를 찾을 수 없습니다: {path}")
    try:
        import yaml  # type: ignore
    except ImportError:
        return load_simple_yaml_subset(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_simple_yaml_subset(path: Path) -> dict[str, Any]:
    """top-level scalar와 inline list만 지원하는 작은 fallback parser입니다."""

    config: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        config[key.strip()] = parse_scalar_or_inline_list(value)
    return config


def parse_scalar_or_inline_list(value: str) -> Any:
    """YAML subset의 scalar와 `[a, b]` 형태 list를 파싱합니다."""

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        pass
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar_or_inline_list(item.strip()) for item in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "none"}:
        return None
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value.strip('"').strip("'")


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _optional_float_list(value: Any) -> list[float | None]:
    """빈 relation threshold list는 scenario별 기본값 사용을 의미합니다."""

    if value in (None, ""):
        return [None]
    items = _as_list(value)
    if not items:
        return [None]
    normalized: list[float | None] = []
    for item in items:
        if item in (None, "", "null", "None", "scenario_default"):
            normalized.append(None)
        else:
            normalized.append(float(item))
    return normalized


def _float_axis(config: dict[str, Any], *, plural_key: str, singular_key: str, default: float) -> list[float]:
    """singular/plural threshold config를 모두 지원합니다."""

    if plural_key in config:
        value = config.get(plural_key)
    else:
        value = config.get(singular_key, default)
    return [float(item) for item in _as_list(value)]


def _noise_settings_from_config(config: dict[str, Any]) -> list[dict[str, float]]:
    """기존 noise_settings와 extended noise grid를 모두 지원합니다."""

    if "noise_settings" in config:
        return _noise_settings(config.get("noise_settings"))
    position_values = [float(item) for item in _as_list(config.get("position_noise_std", [0.0]))]
    distance_values = [float(item) for item in _as_list(config.get("distance_noise_std", [0.0]))]
    visibility_values = [float(item) for item in _as_list(config.get("visibility_flip_prob", [0.0]))]
    return [
        {
            "position_noise_std": position_noise_std,
            "distance_noise_std": distance_noise_std,
            "visibility_flip_prob": visibility_flip_prob,
        }
        for position_noise_std, distance_noise_std, visibility_flip_prob in product(
            position_values,
            distance_values,
            visibility_values,
        )
    ]


def _noise_settings(value: Any) -> list[dict[str, float]]:
    """suite config의 noise_settings를 표준 dict 목록으로 정규화합니다."""

    if value in (None, ""):
        return [{"position_noise_std": 0.0, "distance_noise_std": 0.0, "visibility_flip_prob": 0.0}]
    settings: list[dict[str, float]] = []
    for item in _as_list(value):
        if not isinstance(item, dict):
            raise ValueError("noise_settings 항목은 dict여야 합니다.")
        settings.append(
            {
                "position_noise_std": float(item.get("position_noise_std", 0.0)),
                "distance_noise_std": float(item.get("distance_noise_std", 0.0)),
                "visibility_flip_prob": float(item.get("visibility_flip_prob", 0.0)),
            }
        )
    return settings


if __name__ == "__main__":
    raise SystemExit(main())

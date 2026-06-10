"""WindowsMetadataSim multi-run evaluation suite runner입니다."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.run_windows_metadata_sim import run_simulation
from rast.evaluation.aggregate import aggregate_episode_summaries
from rast.evaluation.summarize import summarize_aggregate_results
from rast.simulator.windows_scenarios import build_windows_scenario


DEFAULT_CONFIG_PATH = ROOT / "configs" / "windows_eval_suite.yaml"


@dataclass(frozen=True)
class SuiteRunSpec:
    """Evaluation suite의 단일 episode run 조합입니다."""

    scenario: str
    seed: int
    risk_threshold: float
    near_miss_threshold: float
    collision_threshold: float
    apply_policy: str
    update_mode: str
    max_steps: int


def main() -> int:
    parser = argparse.ArgumentParser(description="Run WindowsMetadataSim multi-run evaluation suite")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    config = load_suite_config(Path(args.config))
    suite_run_id = f"windows_eval_suite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_root = Path(str(args.output_dir or config.get("output_dir", "runs/windows_eval_suite")))
    suite_output_dir = output_root / suite_run_id
    specs = build_suite_specs(config)
    if args.limit is not None:
        specs = specs[: args.limit]

    print(f"suite_run_id={suite_run_id}")
    print(f"planned_runs={len(specs)}")
    if args.dry_run:
        for index, spec in enumerate(specs):
            print(f"{index:03d}: {spec}")
        return 0

    run_metadata: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        run_dir = suite_output_dir / run_directory_name(index, spec)
        run_dir.mkdir(parents=True, exist_ok=True)
        output_path = run_dir / "step_log.jsonl"
        metadata = base_run_metadata(
            suite_run_id=suite_run_id,
            spec=spec,
            episode_output_dir=run_dir,
        )
        try:
            scenario = build_windows_scenario(spec.scenario)
            run_simulation(
                sim=scenario.simulator,
                scenario_name=scenario.name,
                max_steps=spec.max_steps,
                risk_threshold=spec.risk_threshold,
                object_list_threshold=scenario.object_list_threshold,
                collision_threshold=spec.collision_threshold,
                near_miss_threshold=spec.near_miss_threshold,
                update_mode=spec.update_mode,
                apply_policy=spec.apply_policy,
                output_path=output_path,
                goal=scenario.goal,
            )
            metadata["status"] = "success"
            metadata["summary_path"] = str(run_dir / "episode_summary.json")
            print(
                f"[ok] {index + 1}/{len(specs)} {spec.scenario} seed={spec.seed} "
                f"policy={spec.apply_policy} update_mode={spec.update_mode}"
            )
        except Exception as exc:  # suite infrastructure는 실패 run을 aggregate에 남깁니다.
            metadata["status"] = "failed"
            metadata["error"] = str(exc)
            failure_path = run_dir / "failure.json"
            failure_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(
                f"[failed] {index + 1}/{len(specs)} {spec.scenario} seed={spec.seed} "
                f"update_mode={spec.update_mode}: {exc}"
            )
        run_metadata.append(metadata)

    rows = aggregate_episode_summaries(run_metadata, output_dir=suite_output_dir)
    summarize_aggregate_results(rows, output_dir=suite_output_dir)
    failed_count = sum(1 for row in rows if row.get("status") != "success")
    print(f"aggregate_results: {(suite_output_dir / 'aggregate_results.csv').resolve()}")
    print(f"aggregate_summary: {(suite_output_dir / 'aggregate_summary.csv').resolve()}")
    print(f"failed_runs={failed_count}")
    return 0


def build_suite_specs(config: dict[str, Any]) -> list[SuiteRunSpec]:
    """config의 scenario × seed × threshold × apply_policy 조합을 생성합니다."""

    scenarios = [str(item) for item in _as_list(config.get("scenarios", ["clear_path"]))]
    seeds = [int(item) for item in _as_list(config.get("seeds", [0]))]
    risk_thresholds = [float(item) for item in _as_list(config.get("risk_thresholds", [1.5]))]
    near_miss_thresholds = [float(item) for item in _as_list(config.get("near_miss_thresholds", [1.0]))]
    apply_policies = [str(item) for item in _as_list(config.get("apply_policies", ["rast"]))]
    update_modes = [str(item) for item in _as_list(config.get("update_modes", ["full_recompute"]))]
    collision_threshold = float(config.get("collision_threshold", 0.2))
    max_steps = int(config.get("max_steps", 10))

    return [
        SuiteRunSpec(
            scenario=scenario,
            seed=seed,
            risk_threshold=risk_threshold,
            near_miss_threshold=near_miss_threshold,
            collision_threshold=collision_threshold,
            apply_policy=apply_policy,
            update_mode=update_mode,
            max_steps=max_steps,
        )
        for scenario, seed, risk_threshold, near_miss_threshold, apply_policy, update_mode in product(
            scenarios,
            seeds,
            risk_thresholds,
            near_miss_thresholds,
            apply_policies,
            update_modes,
        )
    ]


def base_run_metadata(*, suite_run_id: str, spec: SuiteRunSpec, episode_output_dir: Path) -> dict[str, Any]:
    """aggregate row에 필요한 run metadata를 구성합니다."""

    return {
        "suite_run_id": suite_run_id,
        "scenario": spec.scenario,
        "seed": spec.seed,
        "apply_policy": spec.apply_policy,
        "update_mode": spec.update_mode,
        "risk_threshold": spec.risk_threshold,
        "near_miss_threshold": spec.near_miss_threshold,
        "collision_threshold": spec.collision_threshold,
        "episode_output_dir": str(episode_output_dir),
        "summary_path": str(episode_output_dir / "episode_summary.json"),
        "status": "pending",
        "error": "",
    }


def run_directory_name(index: int, spec: SuiteRunSpec) -> str:
    """파일시스템에 안전한 run directory 이름을 만듭니다."""

    risk = str(spec.risk_threshold).replace(".", "p")
    near = str(spec.near_miss_threshold).replace(".", "p")
    return (
        f"{index:04d}_scenario-{spec.scenario}_seed-{spec.seed}_"
        f"risk-{risk}_near-{near}_policy-{spec.apply_policy}_update-{spec.update_mode}"
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

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar_or_inline_list(item.strip()) for item in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
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


if __name__ == "__main__":
    raise SystemExit(main())

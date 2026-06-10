"""RAST MVP-0 vertical slice runner입니다.

full experiment runner가 아니라 smoke/integration 확인용입니다. 동일 metadata에서
Object List baseline과 RAST token path를 함께 생성해 information-bound 흐름을 보존합니다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.baselines.object_list import build_object_list
from rast.evaluation.jsonl_logger import JSONLLogger
from rast.evaluation.latency import LatencyTimer
from rast.evaluation.records import StepLogRecord
from rast.planner.object_list_planner import ObjectListPlannerConfig, plan_from_object_list
from rast.planner.token_planner import plan_from_tokens
from rast.simulator.ai2thor_env import AI2THOREnvironmentError, AI2THORNotAvailableError, create_controller, reset_scene, step_action
from rast.simulator.observation_adapter import event_to_observation_snapshot, metadata_to_observation_snapshot
from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig


DEFAULT_CONFIG_PATH = ROOT / "configs" / "mvp0.yaml"
DEFAULT_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "sample_ai2thor_metadata.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="RAST MVP-0 vertical slice runner")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--use-fixture", action="store_true", help="AI2-THOR 대신 fixture metadata를 사용합니다.")
    parser.add_argument("--cloud-rendering", action="store_true", help="AI2-THOR CloudRendering platform을 사용합니다.")
    args = parser.parse_args()

    config = load_flat_yaml(Path(args.config))
    scene = str(config.get("scene", "FloorPlan1"))
    max_steps = int(config.get("max_steps", 1))
    output_dir = Path(str(config.get("output_dir", "runs/mvp0_vertical_slice")))
    risk_threshold = float(config.get("risk_threshold", 1.5))
    use_fixture = bool(args.use_fixture or config.get("use_fixture", False))
    use_fixture_fallback = bool(config.get("use_fixture_fallback", True))
    cloud_rendering = bool(args.cloud_rendering or config.get("cloud_rendering", False))

    output_path = output_dir / "step_log.jsonl"
    logger = JSONLLogger(output_path)

    if use_fixture:
        records = run_fixture_path(
            logger=logger,
            fixture_path=DEFAULT_FIXTURE_PATH,
            scene=scene,
            max_steps=max_steps,
            risk_threshold=risk_threshold,
        )
    else:
        try:
            records = run_ai2thor_path(
                logger=logger,
                scene=scene,
                max_steps=max_steps,
                risk_threshold=risk_threshold,
                cloud_rendering=cloud_rendering,
            )
        except (AI2THORNotAvailableError, AI2THOREnvironmentError) as exc:
            if not use_fixture_fallback:
                raise
            print(f"AI2-THOR 경로를 사용할 수 없어 fixture fallback으로 전환합니다: {exc}", file=sys.stderr)
            records = run_fixture_path(
                logger=logger,
                fixture_path=DEFAULT_FIXTURE_PATH,
                scene=scene,
                max_steps=max_steps,
                risk_threshold=risk_threshold,
            )

    print(f"records={len(records)} log={output_path.resolve()}")
    if records:
        last = records[-1]
        print(
            f"last_step={last.step} scene={last.scene_id} action={last.selected_action} "
            f"total_ms={last.latency.total:.3f} tokens={len(last.tokens)}"
        )
    return 0


def run_fixture_path(
    *,
    logger: JSONLLogger,
    fixture_path: Path,
    scene: str,
    max_steps: int,
    risk_threshold: float,
) -> list[StepLogRecord]:
    """fixture metadata를 사용해 simulator 없이 vertical slice를 실행합니다."""

    del scene  # fixture의 scene id를 source of truth로 사용합니다.
    metadata = json.loads(fixture_path.read_text(encoding="utf-8"))
    records: list[StepLogRecord] = []
    for step in range(max_steps):
        record = build_record_from_metadata(
            metadata=metadata,
            step=step,
            run_id="mvp0_vertical_slice_fixture",
            episode_id="fixture_episode",
            metadata_snapshot_ref=str(fixture_path),
            risk_threshold=risk_threshold,
            action_latency_ms=0.0,
        )
        logger.append(record)
        records.append(record)
    return records


def run_ai2thor_path(
    *,
    logger: JSONLLogger,
    scene: str,
    max_steps: int,
    risk_threshold: float,
    cloud_rendering: bool,
) -> list[StepLogRecord]:
    """AI2-THOR가 설치된 환경에서 실제 event.metadata path를 실행합니다."""

    controller = create_controller(scene=scene, cloud_rendering=cloud_rendering)
    event = reset_scene(controller, scene=scene)
    records: list[StepLogRecord] = []
    for step in range(max_steps):
        timer = LatencyTimer()
        with timer.stage("observation"):
            snapshot = event_to_observation_snapshot(
                event,
                step=step,
                episode_id="mvp0_vertical_slice_ai2thor_episode",
                metadata_snapshot_ref=f"{scene}:step:{step}",
            )
        timer.record_stage("perception", 0.0)
        with timer.stage("token_generation"):
            token_result = tokenize_snapshot(
                snapshot,
                risk_config=RiskTokenizerConfig(near_agent_threshold=risk_threshold),
            )
        with timer.stage("planning"):
            object_list = build_object_list(snapshot)
            rast_action = plan_from_tokens(token_result.entities, token_result.risks)
            object_list_action = plan_from_object_list(
                object_list,
                config=ObjectListPlannerConfig(near_object_threshold=risk_threshold),
            )
        with timer.stage("action"):
            event = step_action(controller, rast_action)

        record = StepLogRecord.from_parts(
            run_id="mvp0_vertical_slice_ai2thor",
            episode_id="mvp0_vertical_slice_ai2thor_episode",
            scene_id=snapshot.scene_id,
            step=step,
            baseline_type="rast",
            latency=timer.to_record(),
            selected_action=rast_action.value,
            tokens=token_result.tokens,
            metadata_snapshot_ref=snapshot.metadata_snapshot_ref,
            extra={
                "phase": "oracle_tokenization",
                "perception_latency_note": "0.0ms placeholder; 실제 perception model latency가 아닙니다.",
                "object_list_action": object_list_action.value,
                "object_list_count": len(object_list),
                "entity_count": len(token_result.entities),
                "risk_count": len(token_result.risks),
            },
        )
        logger.append(record)
        records.append(record)
    return records


def build_record_from_metadata(
    *,
    metadata: dict[str, Any],
    step: int,
    run_id: str,
    episode_id: str,
    metadata_snapshot_ref: str,
    risk_threshold: float,
    action_latency_ms: float,
) -> StepLogRecord:
    """metadata-like dict 한 개를 MVP-0 JSONL step record로 변환합니다."""

    timer = LatencyTimer()
    with timer.stage("observation"):
        snapshot = metadata_to_observation_snapshot(
            metadata,
            step=step,
            episode_id=episode_id,
            metadata_snapshot_ref=metadata_snapshot_ref,
        )
    # Phase 1 Oracle Tokenization: 실제 RGB-D perception latency를 측정한 값이 아닙니다.
    timer.record_stage("perception", 0.0)
    with timer.stage("token_generation"):
        token_result = tokenize_snapshot(snapshot, risk_config=RiskTokenizerConfig(near_agent_threshold=risk_threshold))
    with timer.stage("planning"):
        object_list = build_object_list(snapshot)
        rast_action = plan_from_tokens(token_result.entities, token_result.risks)
        object_list_action = plan_from_object_list(
            object_list,
            config=ObjectListPlannerConfig(near_object_threshold=risk_threshold),
        )
    timer.record_stage("action", action_latency_ms)

    return StepLogRecord.from_parts(
        run_id=run_id,
        episode_id=episode_id,
        scene_id=snapshot.scene_id,
        step=step,
        baseline_type="rast",
        latency=timer.to_record(),
        selected_action=rast_action.value,
        tokens=token_result.tokens,
        metadata_snapshot_ref=snapshot.metadata_snapshot_ref,
        extra={
            "phase": "oracle_tokenization",
            "perception_latency_note": "0.0ms placeholder; 실제 perception model latency가 아닙니다.",
            "object_list_action": object_list_action.value,
            "object_list_count": len(object_list),
            "entity_count": len(token_result.entities),
            "risk_count": len(token_result.risks),
        },
    )


def load_flat_yaml(path: Path) -> dict[str, Any]:
    """외부 YAML dependency 없이 mvp0.yaml의 flat key/value만 읽습니다."""

    if not path.exists():
        return {}
    config: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        config[key.strip()] = parse_scalar(raw_value.strip())
    return config


def parse_scalar(value: str) -> Any:
    """작은 config 파일에 필요한 bool/int/float/string만 처리합니다."""

    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value.strip('"').strip("'")


if __name__ == "__main__":
    raise SystemExit(main())

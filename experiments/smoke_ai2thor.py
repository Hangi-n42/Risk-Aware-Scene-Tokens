"""AI2-THOR smoke/integration script입니다.

pytest 기본 실행에는 포함하지 않습니다. Phase 1 Oracle Tokenization 경로를
실제 AI2-THOR event.metadata와 연결할 수 있는지 확인하는 용도입니다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
from rast.simulator.observation_adapter import event_to_observation_snapshot
from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="RAST MVP-0 AI2-THOR smoke script")
    parser.add_argument("--scene", default="FloorPlan1")
    parser.add_argument("--max-steps", type=int, default=3)
    parser.add_argument("--risk-threshold", type=float, default=1.5)
    parser.add_argument("--output", default="runs/smoke_ai2thor/step_log.jsonl")
    parser.add_argument("--cloud-rendering", action="store_true", help="AI2-THOR CloudRendering platform을 사용합니다.")
    args = parser.parse_args()

    logger = JSONLLogger(args.output)
    risk_config = RiskTokenizerConfig(near_agent_threshold=args.risk_threshold)
    object_planner_config = ObjectListPlannerConfig(near_object_threshold=args.risk_threshold)

    try:
        controller = create_controller(scene=args.scene, cloud_rendering=args.cloud_rendering)
        event = reset_scene(controller, scene=args.scene)
    except (AI2THORNotAvailableError, AI2THOREnvironmentError) as exc:
        print(f"AI2-THOR smoke를 실행할 수 없습니다: {exc}", file=sys.stderr)
        return 2

    run_id = "smoke_ai2thor"
    episode_id = f"{run_id}_{args.scene}"

    for step in range(args.max_steps):
        timer = LatencyTimer()
        with timer.stage("observation"):
            snapshot = event_to_observation_snapshot(
                event,
                step=step,
                episode_id=episode_id,
                metadata_snapshot_ref=f"{args.scene}:step:{step}",
            )
        # Phase 1은 simulator metadata 기반 oracle tokenization입니다. 실제 perception latency가 아닙니다.
        timer.record_stage("perception", 0.0)
        with timer.stage("token_generation"):
            token_result = tokenize_snapshot(snapshot, risk_config=risk_config)
        with timer.stage("planning"):
            object_list = build_object_list(snapshot)
            selected_action = plan_from_tokens(token_result.entities, token_result.risks)
            object_list_action = plan_from_object_list(object_list, config=object_planner_config)
        with timer.stage("action"):
            event = step_action(controller, selected_action)

        latency = timer.to_record()
        record = StepLogRecord.from_parts(
            run_id=run_id,
            episode_id=episode_id,
            scene_id=snapshot.scene_id,
            step=step,
            baseline_type="rast",
            latency=latency,
            selected_action=selected_action.value,
            tokens=token_result.tokens,
            metadata_snapshot_ref=snapshot.metadata_snapshot_ref,
            extra={
                "phase": "oracle_tokenization",
                "perception_latency_note": "0.0ms placeholder; 실제 perception model latency가 아닙니다.",
                "entity_count": len(token_result.entities),
                "risk_count": len(token_result.risks),
                "object_list_count": len(object_list),
                "object_list_action": object_list_action.value,
            },
        )
        logger.append(record)
        print(
            f"step={step} scene={snapshot.scene_id} objects={len(snapshot.objects)} "
            f"tokens={len(token_result.tokens)} risks={len(token_result.risks)} "
            f"action={selected_action.value} total_ms={latency.total:.3f}"
        )

    print(f"JSONL log: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

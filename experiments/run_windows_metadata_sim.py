"""WindowsMetadataSim 기반 controlled scenario evaluation harness입니다."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rast.baselines.audit import flat_feature_table_audit, object_list_audit, rast_audit
from rast.baselines.flat_feature_table import build_flat_feature_table
from rast.baselines.object_list import ObjectListItem, build_object_list
from rast.baselines.scene_graph import build_scene_graph
from rast.evaluation.jsonl_logger import JSONLLogger
from rast.evaluation.latency import LatencyTimer, incremental_update_benefit
from rast.evaluation.metrics import calculate_episode_summary
from rast.evaluation.records import StepLogRecord
from rast.planner.affordance_aware_token_planner import plan_from_affordance_aware_tokens
from rast.planner.event_aware_token_planner import VALID_EVENT_POLICY_VARIANTS, plan_from_event_aware_tokens
from rast.planner.flat_feature_planner import plan_from_flat_features
from rast.planner.object_list_planner import ObjectListPlannerConfig, plan_from_object_list
from rast.planner.scene_graph_planner import plan_from_scene_graph
from rast.planner.token_planner import plan_from_tokens
from rast.planner.uncertainty_aware_token_planner import plan_from_uncertainty_aware_tokens
from rast.schemas.common import Vector3
from rast.schemas.metrics import EpisodeSummary, GoalSpec
from rast.simulator.windows_metadata_sim import MetadataNoiseConfig, WindowsMetadataSim, vector_distance
from rast.simulator.windows_scenarios import available_scenarios, build_windows_scenario
from rast.token_memory.memory import TokenMemory
from rast.token_memory.incremental_update import VALID_UPDATE_MODES
from rast.tokenizer.affordance_tokenizer import AffordanceTokenizerConfig
from rast.tokenizer.event_tokenizer import EventTokenizerConfig
from rast.tokenizer.evidence_tokenizer import attach_decision_evidence_ids, build_evidence_tokens, count_evidence_types
from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.relation_tokenizer import RelationTokenizerConfig
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig
from rast.tokenizer.uncertainty_tokenizer import UncertaintyTokenizerConfig


DEFAULT_CONFIG_PATH = ROOT / "configs" / "windows_metadata_sim.yaml"
DEFAULT_COLLISION_THRESHOLD = 0.2
DEFAULT_NEAR_MISS_THRESHOLD = 1.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAST MVP-0 controlled scenario harness with WindowsMetadataSim")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--scenario", choices=available_scenarios(), default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--risk-threshold", type=float, default=None)
    parser.add_argument("--object-list-threshold", type=float, default=None)
    parser.add_argument("--near-agent-relation-threshold", type=float, default=None)
    parser.add_argument("--near-path-relation-threshold", type=float, default=None)
    parser.add_argument("--blocking-relation-threshold", type=float, default=None)
    parser.add_argument("--collision-threshold", type=float, default=None)
    parser.add_argument("--near-miss-threshold", type=float, default=None)
    parser.add_argument("--event-movement-threshold", type=float, default=None)
    parser.add_argument("--risk-score-delta-threshold", type=float, default=None)
    parser.add_argument("--classification-uncertainty-threshold", type=float, default=None)
    parser.add_argument("--position-variance-threshold", type=float, default=None)
    parser.add_argument("--occlusion-ratio-threshold", type=float, default=None)
    parser.add_argument("--sensor-agreement-threshold", type=float, default=None)
    parser.add_argument("--update-mode", choices=VALID_UPDATE_MODES, default=None)
    parser.add_argument(
        "--apply-policy",
        choices=(
            "rast",
            "object_list",
            "flat_feature",
            "scene_graph",
            "event_aware_rast",
            "uncertainty_aware_rast",
            "affordance_aware_rast",
        ),
        default=None,
    )
    parser.add_argument("--event-policy-variant", choices=VALID_EVENT_POLICY_VARIANTS, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--position-noise-std", type=float, default=None)
    parser.add_argument("--distance-noise-std", type=float, default=None)
    parser.add_argument("--visibility-flip-prob", type=float, default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    config = load_yaml_config(Path(args.config))
    scenario_name = str(args.scenario or config.get("scenario", "clear_path"))
    scenario = build_windows_scenario(scenario_name)
    use_config_defaults = args.scenario is None

    max_steps_default = config.get("max_steps", scenario.max_steps) if use_config_defaults else scenario.max_steps
    max_steps = int(args.max_steps if args.max_steps is not None else max_steps_default)
    risk_threshold = float(
        args.risk_threshold
        if args.risk_threshold is not None
        else (config.get("risk_threshold", scenario.risk_threshold) if use_config_defaults else scenario.risk_threshold)
    )
    object_list_threshold = float(
        args.object_list_threshold
        if args.object_list_threshold is not None
        else (
            config.get("object_list_threshold", scenario.object_list_threshold)
            if use_config_defaults
            else scenario.object_list_threshold
        )
    )
    near_agent_relation_threshold = float(
        args.near_agent_relation_threshold
        if args.near_agent_relation_threshold is not None
        else (
            config.get("near_agent_relation_threshold", scenario.resolved_near_agent_relation_threshold)
            if use_config_defaults
            else scenario.resolved_near_agent_relation_threshold
        )
    )
    near_path_relation_threshold = float(
        args.near_path_relation_threshold
        if args.near_path_relation_threshold is not None
        else (
            config.get("near_path_relation_threshold", scenario.resolved_near_path_relation_threshold)
            if use_config_defaults
            else scenario.resolved_near_path_relation_threshold
        )
    )
    blocking_relation_threshold = float(
        args.blocking_relation_threshold
        if args.blocking_relation_threshold is not None
        else (
            config.get("blocking_relation_threshold", scenario.resolved_blocking_relation_threshold)
            if use_config_defaults
            else scenario.resolved_blocking_relation_threshold
        )
    )
    collision_threshold = float(
        args.collision_threshold
        if args.collision_threshold is not None
        else (
            config.get("collision_threshold", scenario.collision_threshold)
            if use_config_defaults
            else scenario.collision_threshold
        )
    )
    near_miss_threshold = float(
        args.near_miss_threshold
        if args.near_miss_threshold is not None
        else (
            config.get("near_miss_threshold", scenario.near_miss_threshold)
            if use_config_defaults
            else scenario.near_miss_threshold
        )
    )
    event_movement_threshold = float(
        args.event_movement_threshold
        if args.event_movement_threshold is not None
        else config.get("event_movement_threshold", 0.1)
    )
    risk_score_delta_threshold = float(
        args.risk_score_delta_threshold
        if args.risk_score_delta_threshold is not None
        else config.get("risk_score_delta_threshold", 0.1)
    )
    classification_uncertainty_threshold = float(
        args.classification_uncertainty_threshold
        if args.classification_uncertainty_threshold is not None
        else config.get("classification_uncertainty_threshold", 0.5)
    )
    position_variance_threshold = float(
        args.position_variance_threshold
        if args.position_variance_threshold is not None
        else config.get("position_variance_threshold", 0.2)
    )
    occlusion_ratio_threshold = float(
        args.occlusion_ratio_threshold
        if args.occlusion_ratio_threshold is not None
        else config.get("occlusion_ratio_threshold", 0.5)
    )
    sensor_agreement_threshold = float(
        args.sensor_agreement_threshold
        if args.sensor_agreement_threshold is not None
        else config.get("sensor_agreement_threshold", 0.6)
    )
    apply_policy = str(
        args.apply_policy
        if args.apply_policy is not None
        else (config.get("apply_policy", scenario.apply_policy) if use_config_defaults else scenario.apply_policy)
    )
    update_mode = str(args.update_mode if args.update_mode is not None else config.get("update_mode", "full_recompute"))
    event_policy_variant = str(args.event_policy_variant or config.get("event_policy_variant", "full"))
    seed = int(args.seed if args.seed is not None else config.get("seed", 0))
    position_noise_std = float(
        args.position_noise_std if args.position_noise_std is not None else config.get("position_noise_std", 0.0)
    )
    distance_noise_std = float(
        args.distance_noise_std if args.distance_noise_std is not None else config.get("distance_noise_std", 0.0)
    )
    visibility_flip_prob = float(
        args.visibility_flip_prob
        if args.visibility_flip_prob is not None
        else config.get("visibility_flip_prob", 0.0)
    )

    output_root = Path(str(args.output_dir or config.get("output_dir", "runs/windows_metadata_sim")))
    output_path = (
        Path(args.output)
        if args.output
        else output_root / scenario_name / update_mode / f"event_policy-{event_policy_variant}" / "step_log.jsonl"
    )

    records = run_simulation(
        sim=scenario.simulator,
        scenario_name=scenario_name,
        max_steps=max_steps,
        risk_threshold=risk_threshold,
        object_list_threshold=object_list_threshold,
        near_agent_relation_threshold=near_agent_relation_threshold,
        near_path_relation_threshold=near_path_relation_threshold,
        blocking_relation_threshold=blocking_relation_threshold,
        collision_threshold=collision_threshold,
        near_miss_threshold=near_miss_threshold,
        event_movement_threshold=event_movement_threshold,
        risk_score_delta_threshold=risk_score_delta_threshold,
        classification_uncertainty_threshold=classification_uncertainty_threshold,
        position_variance_threshold=position_variance_threshold,
        occlusion_ratio_threshold=occlusion_ratio_threshold,
        sensor_agreement_threshold=sensor_agreement_threshold,
        update_mode=update_mode,
        apply_policy=apply_policy,
        event_policy_variant=event_policy_variant,
        seed=seed,
        position_noise_std=position_noise_std,
        distance_noise_std=distance_noise_std,
        visibility_flip_prob=visibility_flip_prob,
        output_path=output_path,
        goal=scenario.goal,
    )
    summary_path = output_path.parent / "episode_summary.json"
    print(f"Scenario: {scenario_name}")
    print(f"JSONL log: {output_path.resolve()}")
    print(f"Episode summary: {summary_path.resolve()}")
    print(f"records={len(records)}")
    return 0


def run_simulation(
    *,
    sim: WindowsMetadataSim | None = None,
    max_steps: int,
    risk_threshold: float,
    output_path: str | Path,
    scenario_name: str = "custom",
    object_list_threshold: float | None = None,
    near_agent_relation_threshold: float | None = None,
    near_path_relation_threshold: float | None = None,
    blocking_relation_threshold: float | None = None,
    collision_threshold: float = DEFAULT_COLLISION_THRESHOLD,
    near_miss_threshold: float = DEFAULT_NEAR_MISS_THRESHOLD,
    event_movement_threshold: float = 0.1,
    risk_score_delta_threshold: float = 0.1,
    classification_uncertainty_threshold: float = 0.5,
    position_variance_threshold: float = 0.2,
    occlusion_ratio_threshold: float = 0.5,
    sensor_agreement_threshold: float = 0.6,
    update_mode: str = "full_recompute",
    apply_policy: str = "rast",
    event_policy_variant: str = "full",
    seed: int = 0,
    position_noise_std: float = 0.0,
    distance_noise_std: float = 0.0,
    visibility_flip_prob: float = 0.0,
    goal: GoalSpec | None = None,
) -> list[StepLogRecord]:
    """WindowsMetadataSim에서 controlled episode를 실행하고 step log와 summary를 저장합니다."""

    if max_steps <= 0:
        raise ValueError("max_steps는 0보다 커야 합니다.")
    if risk_threshold <= 0:
        raise ValueError("risk_threshold는 0보다 커야 합니다.")
    object_threshold = object_list_threshold if object_list_threshold is not None else risk_threshold
    relation_near_agent_threshold = (
        near_agent_relation_threshold if near_agent_relation_threshold is not None else risk_threshold
    )
    relation_near_path_threshold = near_path_relation_threshold if near_path_relation_threshold is not None else 0.5
    relation_blocking_threshold = blocking_relation_threshold if blocking_relation_threshold is not None else risk_threshold
    if object_threshold <= 0:
        raise ValueError("object_list_threshold는 0보다 커야 합니다.")
    if relation_near_agent_threshold <= 0:
        raise ValueError("near_agent_relation_threshold는 0보다 커야 합니다.")
    if relation_near_path_threshold < 0:
        raise ValueError("near_path_relation_threshold는 0 이상이어야 합니다.")
    if relation_blocking_threshold <= 0:
        raise ValueError("blocking_relation_threshold는 0보다 커야 합니다.")
    if collision_threshold <= 0:
        raise ValueError("collision_threshold는 0보다 커야 합니다.")
    if near_miss_threshold <= collision_threshold:
        raise ValueError("near_miss_threshold는 collision_threshold보다 커야 합니다.")
    if event_movement_threshold < 0:
        raise ValueError("event_movement_threshold는 0 이상이어야 합니다.")
    if risk_score_delta_threshold < 0:
        raise ValueError("risk_score_delta_threshold는 0 이상이어야 합니다.")
    if update_mode not in VALID_UPDATE_MODES:
        allowed = ", ".join(VALID_UPDATE_MODES)
        raise ValueError(f"update_mode는 다음 중 하나여야 합니다: {allowed}")
    if apply_policy not in {
        "rast",
        "object_list",
        "flat_feature",
        "scene_graph",
        "event_aware_rast",
        "uncertainty_aware_rast",
        "affordance_aware_rast",
    }:
        raise ValueError(
            "apply_policy는 'rast', 'object_list', 'flat_feature', 'scene_graph', "
            "'event_aware_rast', 'uncertainty_aware_rast' 중 하나여야 합니다."
        )
    if not 0 <= classification_uncertainty_threshold <= 1:
        raise ValueError("classification_uncertainty_threshold는 0과 1 사이여야 합니다.")
    if position_variance_threshold < 0:
        raise ValueError("position_variance_threshold는 0 이상이어야 합니다.")
    if not 0 <= occlusion_ratio_threshold <= 1:
        raise ValueError("occlusion_ratio_threshold는 0과 1 사이여야 합니다.")
    if not 0 <= sensor_agreement_threshold <= 1:
        raise ValueError("sensor_agreement_threshold는 0과 1 사이여야 합니다.")

    if event_policy_variant not in VALID_EVENT_POLICY_VARIANTS:
        allowed = ", ".join(VALID_EVENT_POLICY_VARIANTS)
        raise ValueError(f"지원하지 않는 event_policy_variant입니다: {event_policy_variant}. 허용값: {allowed}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    simulator = sim or WindowsMetadataSim()
    simulator.noise_config = MetadataNoiseConfig(
        position_noise_std=position_noise_std,
        distance_noise_std=distance_noise_std,
        visibility_flip_prob=visibility_flip_prob,
        seed=seed,
    )
    logger = JSONLLogger(output)
    risk_config = RiskTokenizerConfig(near_agent_threshold=risk_threshold)
    relation_config = RelationTokenizerConfig(
        near_agent_threshold=relation_near_agent_threshold,
        near_path_lateral_threshold=relation_near_path_threshold,
        blocking_path_distance_threshold=relation_blocking_threshold,
        target_reachable_distance=max(relation_blocking_threshold, risk_threshold, near_miss_threshold, 1.5),
    )
    event_config = EventTokenizerConfig(
        movement_threshold=event_movement_threshold,
        risk_score_delta_threshold=risk_score_delta_threshold,
    )
    uncertainty_config = UncertaintyTokenizerConfig(
        classification_uncertainty_threshold=classification_uncertainty_threshold,
        position_variance_threshold=position_variance_threshold,
        occlusion_ratio_threshold=occlusion_ratio_threshold,
        sensor_agreement_threshold=sensor_agreement_threshold,
        path_lateral_threshold=relation_near_path_threshold,
        risk_threshold=risk_threshold,
    )
    affordance_config = AffordanceTokenizerConfig(
        path_lateral_threshold=relation_near_path_threshold,
        path_lookahead=relation_config.path_lookahead,
        narrow_passage_width_threshold=1.0,
        passable_gap_width_threshold=1.2,
        collision_clearance=collision_threshold,
    )
    full_token_memory = TokenMemory()
    incremental_token_memory = TokenMemory()
    object_list_config = ObjectListPlannerConfig(near_object_threshold=object_threshold)
    episode_id = f"windows_metadata_sim_{scenario_name}"
    run_id = "windows_metadata_sim"
    records: list[StepLogRecord] = []
    goal_reached = False

    simulator.reset()
    full_token_memory.reset()
    incremental_token_memory.reset()
    final_distance_to_goal = goal_distance(simulator, goal) if goal is not None else None
    for step in range(max_steps):
        timer = LatencyTimer()
        with timer.stage("observation"):
            snapshot = simulator.snapshot(episode_id=episode_id)
        # 이 경로는 deterministic metadata simulator입니다. 실제 3D rendering/perception latency가 아닙니다.
        timer.record_stage("perception", 0.0)
        full_start = perf_counter()
        full_token_result = tokenize_snapshot(
            snapshot,
            risk_config=risk_config,
            token_memory=full_token_memory,
            event_config=event_config,
            relation_config=relation_config,
            uncertainty_config=uncertainty_config,
            affordance_config=affordance_config,
            goal=goal,
            enable_relations=True,
            enable_events=True,
            enable_uncertainty=True,
            enable_affordances=True,
            update_mode="full_recompute",
        )
        full_recompute_latency_ms = (perf_counter() - full_start) * 1000.0

        incremental_start = perf_counter()
        incremental_token_result = tokenize_snapshot(
            snapshot,
            risk_config=risk_config,
            token_memory=incremental_token_memory,
            event_config=event_config,
            relation_config=relation_config,
            uncertainty_config=uncertainty_config,
            affordance_config=affordance_config,
            goal=goal,
            enable_relations=True,
            enable_events=True,
            enable_uncertainty=True,
            enable_affordances=True,
            update_mode="incremental",
        )
        incremental_update_latency_ms = (perf_counter() - incremental_start) * 1000.0
        token_result = full_token_result if update_mode == "full_recompute" else incremental_token_result
        selected_token_generation_latency = (
            full_recompute_latency_ms if update_mode == "full_recompute" else incremental_update_latency_ms
        )
        benefit = incremental_update_benefit(
            full_recompute_latency_ms=full_recompute_latency_ms,
            incremental_update_latency_ms=incremental_update_latency_ms,
        )
        timer.record_stage("token_generation", selected_token_generation_latency)
        with timer.stage("planning"):
            object_list = build_object_list(snapshot)
            flat_features = build_flat_feature_table(snapshot, risk_threshold=risk_threshold)
            scene_graph = build_scene_graph(snapshot, token_result.relations, goal=goal)
            rast_decision = plan_from_tokens(token_result.entities, token_result.risks)
            object_list_decision = plan_from_object_list(object_list, config=object_list_config)
            flat_feature_decision = plan_from_flat_features(flat_features)
            scene_graph_decision = plan_from_scene_graph(scene_graph)
            event_aware_decision = plan_from_event_aware_tokens(
                token_result.entities,
                token_result.risks,
                token_result.events,
                policy_variant=event_policy_variant,
            )
            uncertainty_aware_decision = plan_from_uncertainty_aware_tokens(
                token_result.entities,
                token_result.risks,
                token_result.uncertainties,
                token_result.events,
            )
            affordance_aware_decision = plan_from_affordance_aware_tokens(
                token_result.entities,
                token_result.risks,
                token_result.relations,
                token_result.affordances,
                token_result.events,
                token_result.uncertainties,
            )
            evidence_tokens = build_evidence_tokens(
                snapshot,
                risks=token_result.risks,
                uncertainties=token_result.uncertainties,
                events=token_result.events,
                decisions=[
                    rast_decision,
                    object_list_decision,
                    flat_feature_decision,
                    scene_graph_decision,
                    event_aware_decision,
                    uncertainty_aware_decision,
                    affordance_aware_decision,
                ],
            )
            (
                rast_decision,
                object_list_decision,
                flat_feature_decision,
                scene_graph_decision,
                event_aware_decision,
                uncertainty_aware_decision,
                affordance_aware_decision,
            ) = attach_decision_evidence_ids(
                [
                    rast_decision,
                    object_list_decision,
                    flat_feature_decision,
                    scene_graph_decision,
                    event_aware_decision,
                    uncertainty_aware_decision,
                    affordance_aware_decision,
                ],
                evidence_tokens,
            )
            evidence_type_counts = count_evidence_types(evidence_tokens)
            rast_action = rast_decision.action
            object_list_action = object_list_decision.action
            flat_feature_action = flat_feature_decision.action
            scene_graph_action = scene_graph_decision.action
            event_aware_action = event_aware_decision.action
            uncertainty_aware_action = uncertainty_aware_decision.action
            affordance_aware_action = affordance_aware_decision.action

        min_distance = min_object_distance(object_list)
        collision = min_distance is not None and min_distance <= collision_threshold
        near_miss = min_distance is not None and collision_threshold < min_distance <= near_miss_threshold
        if apply_policy == "rast":
            action_to_apply = rast_action
        elif apply_policy == "object_list":
            action_to_apply = object_list_action
        elif apply_policy == "flat_feature":
            action_to_apply = flat_feature_action
        elif apply_policy == "scene_graph":
            action_to_apply = scene_graph_action
        elif apply_policy == "uncertainty_aware_rast":
            action_to_apply = uncertainty_aware_action
        elif apply_policy == "affordance_aware_rast":
            action_to_apply = affordance_aware_action
        else:
            action_to_apply = event_aware_action
        with timer.stage("action"):
            simulator.step(action_to_apply)

        if goal is not None:
            final_distance_to_goal = goal_distance(simulator, goal)
            goal_reached = final_distance_to_goal is not None and final_distance_to_goal <= goal.success_distance

        latency = timer.to_record()
        record = StepLogRecord.from_parts(
            run_id=run_id,
            episode_id=episode_id,
            scene_id=snapshot.scene_id,
            step=step,
            baseline_type="rast",
            latency=latency,
            selected_action=action_to_apply.value,
            tokens=[*token_result.tokens, *evidence_tokens],
            rast_selected_action=rast_action.value,
            object_list_selected_action=object_list_action.value,
            flat_feature_selected_action=flat_feature_action.value,
            scene_graph_selected_action=scene_graph_action.value,
            event_aware_rast_selected_action=event_aware_action.value,
            uncertainty_aware_rast_selected_action=uncertainty_aware_action.value,
            affordance_aware_rast_selected_action=affordance_aware_action.value,
            rast_decision=rast_decision,
            object_list_decision=object_list_decision,
            flat_feature_decision=flat_feature_decision,
            scene_graph_decision=scene_graph_decision,
            event_aware_rast_decision=event_aware_decision,
            uncertainty_aware_rast_decision=uncertainty_aware_decision,
            affordance_aware_rast_decision=affordance_aware_decision,
            rast_reason_code=rast_decision.reason_code,
            object_list_reason_code=object_list_decision.reason_code,
            flat_feature_reason_code=flat_feature_decision.reason_code,
            scene_graph_reason_code=scene_graph_decision.reason_code,
            event_aware_rast_reason_code=event_aware_decision.reason_code,
            uncertainty_aware_rast_reason_code=uncertainty_aware_decision.reason_code,
            affordance_aware_rast_reason_code=affordance_aware_decision.reason_code,
            rast_trigger_token_ids=rast_decision.trigger_token_ids,
            rast_trigger_object_ids=rast_decision.trigger_object_ids,
            object_list_trigger_object_ids=object_list_decision.trigger_object_ids,
            flat_feature_trigger_object_ids=flat_feature_decision.trigger_object_ids,
            scene_graph_trigger_object_ids=scene_graph_decision.trigger_object_ids,
            event_aware_rast_trigger_event_types=list(
                event_aware_decision.trigger_features.get("event_types") or []
            ),
            event_aware_rast_trigger_token_ids=event_aware_decision.trigger_token_ids,
            uncertainty_aware_rast_trigger_token_ids=uncertainty_aware_decision.trigger_token_ids,
            affordance_aware_rast_trigger_token_ids=affordance_aware_decision.trigger_token_ids,
            event_policy_variant=event_policy_variant,
            risk_threshold=risk_threshold,
            near_agent_relation_threshold=relation_near_agent_threshold,
            near_path_relation_threshold=relation_near_path_threshold,
            blocking_relation_threshold=relation_blocking_threshold,
            near_miss_threshold=near_miss_threshold,
            position_noise_std=position_noise_std,
            distance_noise_std=distance_noise_std,
            visibility_flip_prob=visibility_flip_prob,
            baseline_disagreed=rast_action != object_list_action,
            rast_vs_object_list_disagreed=rast_action != object_list_action,
            rast_vs_flat_feature_disagreed=rast_action != flat_feature_action,
            object_list_vs_flat_feature_disagreed=object_list_action != flat_feature_action,
            rast_vs_event_aware_disagreed=rast_action != event_aware_action,
            rast_vs_uncertainty_aware_disagreed=rast_action != uncertainty_aware_action,
            rast_vs_affordance_aware_disagreed=rast_action != affordance_aware_action,
            rast_vs_scene_graph_disagreed=rast_action != scene_graph_action,
            scene_graph_vs_flat_feature_disagreed=scene_graph_action != flat_feature_action,
            entity_token_count=len(token_result.entities),
            risk_token_count=len(token_result.risks),
            relation_token_count=len(token_result.relations),
            relation_types=[relation.relation for relation in token_result.relations],
            uncertainty_token_count=len(token_result.uncertainties),
            uncertainty_types=[token.uncertainty_type for token in token_result.uncertainties],
            high_uncertainty_count=sum(1 for token in token_result.uncertainties if token.level == "high"),
            affordance_token_count=len(token_result.affordances),
            affordance_types=[token.affordance for token in token_result.affordances],
            event_token_count=len(token_result.events),
            event_types=[event.event_type for event in token_result.events],
            evidence_token_count=len(evidence_tokens),
            evidence_types=[token.evidence_type for token in evidence_tokens],
            evidence_token_ids=[token.token_id for token in evidence_tokens],
            risk_evidence_count=evidence_type_counts.get("risk_feature", 0),
            uncertainty_evidence_count=evidence_type_counts.get("uncertainty_feature", 0),
            event_evidence_count=evidence_type_counts.get("event_diff", 0),
            decision_evidence_count=evidence_type_counts.get("planner_decision", 0),
            total_token_count=len(token_result.tokens),
            object_list_count=len(object_list),
            flat_feature_row_count=len(flat_features),
            scene_graph_node_count=scene_graph.node_count,
            scene_graph_edge_count=scene_graph.edge_count,
            update_mode=update_mode,
            changed_object_count=token_result.changed_object_count,
            affected_token_count=token_result.affected_token_count,
            full_recompute_latency_ms=full_recompute_latency_ms,
            incremental_update_latency_ms=incremental_update_latency_ms,
            incremental_update_benefit=benefit,
            token_generation_latency_ms=selected_token_generation_latency,
            near_miss=near_miss,
            collision=collision,
            min_object_distance=min_distance,
            phase="windows_metadata_sim_oracle",
            metadata_snapshot_ref=f"windows_metadata_sim:{snapshot.scene_id}:step:{step}",
            extra={
                "phase_note": "deterministic metadata simulator; real 3D rendering/perception 결과가 아닙니다.",
                "scenario": scenario_name,
                "apply_policy": apply_policy,
                "event_policy_variant": event_policy_variant,
                "seed": seed,
                "risk_threshold": risk_threshold,
                "object_list_threshold": object_threshold,
                "near_agent_relation_threshold": relation_near_agent_threshold,
                "near_path_relation_threshold": relation_near_path_threshold,
                "blocking_relation_threshold": relation_blocking_threshold,
                "collision_threshold": collision_threshold,
                "near_miss_threshold": near_miss_threshold,
                "event_movement_threshold": event_movement_threshold,
                "risk_score_delta_threshold": risk_score_delta_threshold,
                "classification_uncertainty_threshold": classification_uncertainty_threshold,
                "position_variance_threshold": position_variance_threshold,
                "occlusion_ratio_threshold": occlusion_ratio_threshold,
                "sensor_agreement_threshold": sensor_agreement_threshold,
                "position_noise_std": position_noise_std,
                "distance_noise_std": distance_noise_std,
                "visibility_flip_prob": visibility_flip_prob,
                "update_mode": update_mode,
                "incremental_measurement_note": (
                    "full_recompute and incremental candidates are both measured on the same metadata snapshot; "
                    "selected token_generation latency is recorded in LatencyRecord."
                ),
                "incremental_matches_full_entity_risk": token_results_match_entity_risk(
                    full_token_result,
                    incremental_token_result,
                ),
                "information_bound_audit": [
                    rast_audit(input_unit_count=len(token_result.tokens)).to_dict(),
                    object_list_audit(input_unit_count=len(object_list)).to_dict(),
                    flat_feature_table_audit(input_unit_count=len(flat_features)).to_dict(),
                    {
                        "baseline_type": "scene_graph",
                        "input_unit_count": scene_graph.edge_count,
                        "accessible_fields": [
                            "agent_node",
                            "object_nodes",
                            "goal_node",
                            "near_agent",
                            "near_path",
                            "blocking_path",
                            "target_reachable",
                        ],
                        "forbidden_fields": ["risk_type", "severity", "recommended_policy", "risk_score"],
                    },
                ],
            },
        )
        logger.append(record)
        records.append(record)
        print(
            f"step={step} tokens={len(token_result.tokens)} risks={len(token_result.risks)} "
            f"relations={len(token_result.relations)} "
            f"uncertainties={len(token_result.uncertainties)} "
            f"affordances={len(token_result.affordances)} "
            f"events={len(token_result.events)} "
            f"evidence={len(evidence_tokens)} "
            f"update_mode={update_mode} changed={token_result.changed_object_count} "
            f"affected={token_result.affected_token_count} "
            f"rast={rast_action.value} object_list={object_list_action.value} "
            f"flat_feature={flat_feature_action.value} "
            f"scene_graph={scene_graph_action.value} "
            f"event_aware={event_aware_action.value} "
            f"uncertainty_aware={uncertainty_aware_action.value} "
            f"affordance_aware={affordance_aware_action.value} "
            f"event_policy={event_policy_variant} "
            f"rast_reason={rast_decision.reason_code} "
            f"scene_graph_reason={scene_graph_decision.reason_code} "
            f"event_aware_reason={event_aware_decision.reason_code} "
            f"uncertainty_aware_reason={uncertainty_aware_decision.reason_code} "
            f"affordance_aware_reason={affordance_aware_decision.reason_code} "
            f"applied={action_to_apply.value} collision={collision} near_miss={near_miss} "
            f"goal_reached={goal_reached} total_ms={latency.total:.3f} "
            f"full_ms={full_recompute_latency_ms:.3f} incremental_ms={incremental_update_latency_ms:.3f}"
        )

        if goal_reached:
            break

    summary = calculate_episode_summary(
        records,
        max_steps=max_steps,
        collision_threshold=collision_threshold,
        near_miss_threshold=near_miss_threshold,
        goal=goal,
        goal_reached=goal_reached,
        final_distance_to_goal=final_distance_to_goal,
    )
    write_episode_summary(summary, output.parent)
    return records


def write_episode_summary(summary: EpisodeSummary, output_dir: Path) -> None:
    """episode summary를 JSON과 CSV 한 줄로 저장합니다."""

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "episode_summary.json").write_text(summary.to_json() + "\n", encoding="utf-8")

    payload = summary.to_dict()
    csv_payload = {
        key: json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value
        for key, value in payload.items()
    }
    csv_path = output_dir / "episode_summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_payload.keys()))
        writer.writeheader()
        writer.writerow(csv_payload)


def token_results_match_entity_risk(first: Any, second: Any) -> bool:
    """full/incremental 결과가 같은 Entity/Risk 대상 집합을 냈는지 확인합니다."""

    first_entities = {entity.entity_id for entity in first.entities}
    second_entities = {entity.entity_id for entity in second.entities}
    first_risks = {(risk.entity_id, risk.severity) for risk in first.risks}
    second_risks = {(risk.entity_id, risk.severity) for risk in second.risks}
    return first_entities == second_entities and first_risks == second_risks


def min_object_distance(object_list: list[ObjectListItem]) -> float | None:
    """Object List baseline representation에서 가장 가까운 object 거리를 계산합니다."""

    if not object_list:
        return None
    return min(item.distance_to_agent for item in object_list)


def goal_distance(sim: WindowsMetadataSim, goal: GoalSpec | None) -> float | None:
    """현재 agent pose 기준으로 goal까지의 거리를 계산합니다."""

    if goal is None:
        return None
    target = goal_target_position(sim, goal)
    if target is None:
        return None
    return vector_distance(sim.agent.position, target)


def goal_target_position(sim: WindowsMetadataSim, goal: GoalSpec) -> Vector3 | None:
    """GoalSpec에서 실제 target position을 찾습니다."""

    if goal.goal_type == "reach_position":
        return goal.target_position
    for item in sim.objects:
        if goal.target_object_id is not None and item.object_id == goal.target_object_id:
            return item.position
        if goal.target_category is not None and item.object_type == goal.target_category:
            return item.position
    return None


def load_yaml_config(path: Path) -> dict[str, Any]:
    """PyYAML이 있으면 nested config를 읽고, 없으면 flat key만 읽습니다."""

    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return load_flat_config(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_flat_config(path: Path) -> dict[str, Any]:
    """외부 YAML dependency가 없을 때 필요한 최상위 scalar만 읽습니다."""

    config: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line or line.startswith("-"):
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value and "{" not in value and "[" not in value:
            config[key.strip()] = parse_scalar(value)
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

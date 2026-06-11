"""RAST MVP-0 episode evaluation metric schema입니다."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from rast.schemas.common import RASTBaseModel, Vector3


class GoalSpec(RASTBaseModel):
    """MVP-0 episode success 계산을 위한 최소 goal 정의입니다."""

    goal_type: Literal["reach_position", "reach_object"] = Field(description="지원하는 goal type입니다.")
    target_position: Vector3 | None = Field(default=None, description="reach_position goal의 목표 위치입니다.")
    target_object_id: str | None = Field(default=None, description="reach_object goal의 목표 object id입니다.")
    target_category: str | None = Field(default=None, description="reach_object goal의 목표 category입니다.")
    success_distance: float = Field(default=0.3, gt=0, description="goal reached로 볼 agent-target 거리입니다.")


class StepMetrics(RASTBaseModel):
    """JSONL step record에서 episode summary 계산에 필요한 값만 분리한 schema입니다."""

    run_id: str = Field(description="실험 run id입니다.")
    episode_id: str = Field(description="episode id입니다.")
    scene_id: str = Field(description="scene id입니다.")
    step: int = Field(ge=0, description="episode step index입니다.")

    rast_selected_action: str = Field(description="RAST token planner action입니다.")
    object_list_selected_action: str = Field(description="Object List planner action입니다.")
    flat_feature_selected_action: str = Field(default="", description="Flat Feature planner action입니다.")
    scene_graph_selected_action: str = Field(default="", description="Scene Graph planner action입니다.")
    event_aware_rast_selected_action: str = Field(default="", description="Event-aware RAST planner action입니다.")

    rast_reason_code: str = Field(default="", description="RAST planner reason_code입니다.")
    object_list_reason_code: str = Field(default="", description="Object List planner reason_code입니다.")
    flat_feature_reason_code: str = Field(default="", description="Flat Feature planner reason_code입니다.")
    scene_graph_reason_code: str = Field(default="", description="Scene Graph planner reason_code입니다.")
    event_aware_rast_reason_code: str = Field(default="", description="Event-aware RAST planner reason_code입니다.")
    rast_trigger_token_ids: list[str] = Field(default_factory=list, description="RAST trigger token id 목록입니다.")
    rast_trigger_object_ids: list[str] = Field(default_factory=list, description="RAST trigger object id 목록입니다.")
    object_list_trigger_object_ids: list[str] = Field(default_factory=list, description="Object List trigger object id 목록입니다.")
    flat_feature_trigger_object_ids: list[str] = Field(default_factory=list, description="Flat Feature trigger object id 목록입니다.")
    scene_graph_trigger_object_ids: list[str] = Field(default_factory=list, description="Scene Graph trigger object id 목록입니다.")
    event_aware_rast_trigger_event_types: list[str] = Field(default_factory=list, description="Event-aware RAST trigger event type 목록입니다.")
    event_aware_rast_trigger_token_ids: list[str] = Field(default_factory=list, description="Event-aware RAST trigger token id 목록입니다.")

    baseline_disagreed: bool = Field(description="호환용 RAST vs Object List disagreement입니다.")
    rast_vs_object_list_disagreed: bool = Field(description="RAST와 Object List action이 다른지 여부입니다.")
    rast_vs_flat_feature_disagreed: bool = Field(description="RAST와 Flat Feature action이 다른지 여부입니다.")
    object_list_vs_flat_feature_disagreed: bool = Field(description="Object List와 Flat Feature action이 다른지 여부입니다.")
    rast_vs_event_aware_disagreed: bool = Field(default=False, description="RAST와 Event-aware RAST action이 다른지 여부입니다.")
    rast_vs_scene_graph_disagreed: bool = Field(default=False, description="RAST와 Scene Graph action이 다른지 여부입니다.")
    scene_graph_vs_flat_feature_disagreed: bool = Field(default=False, description="Scene Graph와 Flat Feature action이 다른지 여부입니다.")

    entity_token_count: int = Field(ge=0, description="step별 EntityToken 수입니다.")
    risk_token_count: int = Field(ge=0, description="step별 RiskToken 수입니다.")
    relation_token_count: int = Field(default=0, ge=0, description="step별 RelationToken 수입니다.")
    relation_types: list[str] = Field(default_factory=list, description="step에서 생성된 RelationToken relation 목록입니다.")
    event_token_count: int = Field(default=0, ge=0, description="step별 EventToken 수입니다.")
    event_types: list[str] = Field(default_factory=list, description="step에서 감지된 EventToken type 목록입니다.")
    total_token_count: int = Field(ge=0, description="step별 전체 RAST token 수입니다.")
    object_list_count: int = Field(ge=0, description="Object List input unit 수입니다.")
    flat_feature_row_count: int = Field(ge=0, description="Flat Feature Table row 수입니다.")
    scene_graph_node_count: int = Field(default=0, ge=0, description="Scene Graph node 수입니다.")
    scene_graph_edge_count: int = Field(default=0, ge=0, description="Scene Graph edge 수입니다.")

    near_miss: bool = Field(description="near-miss hook 결과입니다.")
    collision: bool = Field(description="collision hook 결과입니다.")
    min_object_distance: float | None = Field(default=None, ge=0, description="가장 가까운 object까지의 거리입니다.")

    token_generation_latency_ms: float = Field(ge=0, description="선택된 update mode의 token_generation latency입니다.")
    planning_latency_ms: float = Field(ge=0, description="planning latency입니다.")
    total_latency_ms: float = Field(ge=0, description="total latency입니다.")

    update_mode: Literal["full_recompute", "incremental"] = Field(default="full_recompute", description="Token update mode입니다.")
    changed_object_count: int = Field(default=0, ge=0, description="semantic diff에서 바뀐 object 수입니다.")
    affected_token_count: int = Field(default=0, ge=0, description="incremental update에서 영향을 받은 token 수입니다.")
    full_recompute_latency_ms: float = Field(default=0.0, ge=0, description="full recompute tokenization latency(ms)입니다.")
    incremental_update_latency_ms: float = Field(default=0.0, ge=0, description="incremental update tokenization latency(ms)입니다.")
    incremental_update_benefit: float = Field(default=0.0, description="full recompute 대비 incremental latency benefit입니다.")
    event_policy_variant: str = Field(default="full", description="Event-aware planner policy ablation variant입니다.")
    risk_threshold: float | None = Field(default=None, ge=0, description="RiskToken 생성 threshold입니다.")
    near_miss_threshold: float | None = Field(default=None, ge=0, description="Near-miss threshold입니다.")
    position_noise_std: float = Field(default=0.0, ge=0, description="Synthetic metadata position noise 표준편차입니다.")
    distance_noise_std: float = Field(default=0.0, ge=0, description="Synthetic metadata distance noise 표준편차입니다.")
    visibility_flip_prob: float = Field(default=0.0, ge=0, le=1, description="Synthetic metadata visibility flip 확률입니다.")


class EpisodeSummary(RASTBaseModel):
    """단일 deterministic metadata episode의 집계 결과입니다."""

    run_id: str = Field(description="실험 run id입니다.")
    episode_id: str = Field(description="episode id입니다.")
    scene_id: str = Field(description="scene id입니다.")
    max_steps: int = Field(ge=0, description="요청한 최대 step 수입니다.")
    completed_steps: int = Field(ge=0, description="실제로 완료한 step 수입니다.")
    success: bool = Field(description="episode success 여부입니다.")
    success_definition: str = Field(description="success 계산 기준입니다.")
    goal_reached: bool = Field(default=False, description="goal이 설정된 경우 goal reached 여부입니다.")
    final_distance_to_goal: float | None = Field(default=None, ge=0, description="episode 종료 시 goal까지의 거리입니다.")

    collision_count: int = Field(ge=0, description="episode collision count입니다.")
    near_miss_count: int = Field(ge=0, description="episode near-miss count입니다.")

    rast_action_counts: dict[str, int] = Field(description="RAST planner action별 count입니다.")
    object_list_action_counts: dict[str, int] = Field(description="Object List planner action별 count입니다.")
    flat_feature_action_counts: dict[str, int] = Field(default_factory=dict, description="Flat Feature planner action별 count입니다.")
    scene_graph_action_counts: dict[str, int] = Field(default_factory=dict, description="Scene Graph planner action별 count입니다.")
    event_aware_rast_action_counts: dict[str, int] = Field(default_factory=dict, description="Event-aware RAST planner action별 count입니다.")

    rast_reason_code_counts: dict[str, int] = Field(default_factory=dict, description="RAST planner reason_code별 count입니다.")
    object_list_reason_code_counts: dict[str, int] = Field(default_factory=dict, description="Object List planner reason_code별 count입니다.")
    flat_feature_reason_code_counts: dict[str, int] = Field(default_factory=dict, description="Flat Feature planner reason_code별 count입니다.")
    scene_graph_reason_code_counts: dict[str, int] = Field(default_factory=dict, description="Scene Graph planner reason_code별 count입니다.")
    event_aware_rast_reason_code_counts: dict[str, int] = Field(default_factory=dict, description="Event-aware RAST planner reason_code별 count입니다.")
    event_policy_variant_action_counts: dict[str, dict[str, int]] = Field(default_factory=dict, description="Event policy variant별 action count입니다.")
    event_policy_variant_reason_code_counts: dict[str, dict[str, int]] = Field(default_factory=dict, description="Event policy variant별 reason_code count입니다.")
    rast_trigger_token_count_total: int = Field(default=0, ge=0, description="RAST decision trigger token 총 개수입니다.")
    decision_trace_coverage: float = Field(default=0.0, ge=0, le=1, description="reason_code가 기록된 step 비율입니다.")

    baseline_disagreement_count: int = Field(ge=0, description="호환용 RAST vs Object List disagreement count입니다.")
    rast_vs_object_list_disagreement_count: int = Field(ge=0, description="RAST vs Object List disagreement count입니다.")
    rast_vs_flat_feature_disagreement_count: int = Field(ge=0, description="RAST vs Flat Feature disagreement count입니다.")
    object_list_vs_flat_feature_disagreement_count: int = Field(ge=0, description="Object List vs Flat Feature disagreement count입니다.")
    rast_vs_event_aware_disagreement_count: int = Field(default=0, ge=0, description="RAST vs Event-aware RAST disagreement count입니다.")
    rast_vs_scene_graph_disagreement_count: int = Field(default=0, ge=0, description="RAST vs Scene Graph disagreement count입니다.")
    scene_graph_vs_flat_feature_disagreement_count: int = Field(default=0, ge=0, description="Scene Graph vs Flat Feature disagreement count입니다.")
    event_triggered_action_count: int = Field(default=0, ge=0, description="Event-aware planner가 event 기반 reason_code로 action을 고른 step 수입니다.")
    event_aware_decision_trace_coverage: float = Field(default=0.0, ge=0, le=1, description="Event-aware planner reason_code가 기록된 step 비율입니다.")
    scene_graph_decision_trace_coverage: float = Field(default=0.0, ge=0, le=1, description="Scene Graph planner reason_code가 기록된 step 비율입니다.")

    entity_token_count_total: int = Field(ge=0, description="episode 전체 EntityToken 수입니다.")
    risk_token_count_total: int = Field(ge=0, description="episode 전체 RiskToken 수입니다.")
    relation_token_count_total: int = Field(default=0, ge=0, description="episode 전체 RelationToken 수입니다.")
    relation_token_count_avg: float = Field(default=0.0, ge=0, description="step당 평균 RelationToken 수입니다.")
    relation_type_counts: dict[str, int] = Field(default_factory=dict, description="RelationToken relation별 count입니다.")
    event_token_count_total: int = Field(default=0, ge=0, description="episode 전체 EventToken 수입니다.")
    event_token_count_avg: float = Field(default=0.0, ge=0, description="step당 평균 EventToken 수입니다.")
    event_type_counts: dict[str, int] = Field(default_factory=dict, description="EventToken type별 count입니다.")
    flat_feature_row_count_total: int = Field(ge=0, description="episode 전체 Flat Feature row 수입니다.")

    token_count_avg: float = Field(ge=0, description="step당 평균 RAST token 수입니다.")
    object_count_avg: float = Field(ge=0, description="step당 평균 Object List input unit 수입니다.")
    flat_feature_row_count_avg: float = Field(ge=0, description="step당 평균 Flat Feature row 수입니다.")
    scene_graph_node_count_avg: float = Field(default=0.0, ge=0, description="step당 평균 Scene Graph node 수입니다.")
    scene_graph_edge_count_avg: float = Field(default=0.0, ge=0, description="step당 평균 Scene Graph edge 수입니다.")

    latency_avg_ms: float = Field(ge=0, description="step당 평균 total latency입니다.")
    latency_p50_ms: float = Field(ge=0, description="total latency p50입니다.")
    latency_p95_ms: float = Field(ge=0, description="total latency p95입니다.")
    token_generation_latency_avg_ms: float = Field(ge=0, description="선택된 update mode의 token_generation latency 평균입니다.")
    planning_latency_avg_ms: float = Field(ge=0, description="planning latency 평균입니다.")
    total_latency_avg_ms: float = Field(ge=0, description="total latency 평균입니다.")
    risk_triggered_action_count: int = Field(ge=0, description="RiskToken이 있고 RAST가 MoveAhead가 아닌 action을 낸 step 수입니다.")

    update_mode: Literal["full_recompute", "incremental"] = Field(default="full_recompute", description="Token update mode입니다.")
    changed_object_count_avg: float = Field(default=0.0, ge=0, description="step당 평균 changed object 수입니다.")
    affected_token_count_avg: float = Field(default=0.0, ge=0, description="step당 평균 affected token 수입니다.")
    full_recompute_latency_avg_ms: float = Field(default=0.0, ge=0, description="full recompute tokenization latency 평균(ms)입니다.")
    incremental_update_latency_avg_ms: float = Field(default=0.0, ge=0, description="incremental update tokenization latency 평균(ms)입니다.")
    incremental_update_benefit_avg: float = Field(default=0.0, description="full recompute 대비 incremental benefit 평균입니다.")
    event_policy_variant: str = Field(default="full", description="Event-aware planner policy ablation variant입니다.")
    risk_threshold: float | None = Field(default=None, ge=0, description="RiskToken 생성 threshold입니다.")
    near_miss_threshold: float | None = Field(default=None, ge=0, description="Near-miss threshold입니다.")
    position_noise_std: float = Field(default=0.0, ge=0, description="Synthetic metadata position noise 표준편차입니다.")
    distance_noise_std: float = Field(default=0.0, ge=0, description="Synthetic metadata distance noise 표준편차입니다.")
    visibility_flip_prob: float = Field(default=0.0, ge=0, le=1, description="Synthetic metadata visibility flip 확률입니다.")

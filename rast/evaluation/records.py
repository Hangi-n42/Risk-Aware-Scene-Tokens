"""MVP-0 JSONL step log record schema입니다."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from rast.schemas.common import RASTBaseModel, SCHEMA_VERSION
from rast.schemas.latency import LatencyRecord


class StepLogRecord(RASTBaseModel):
    """각 step의 representation, planner decision, latency, metric hook을 기록합니다."""

    run_id: str = Field(description="실험 run id입니다.")
    episode_id: str = Field(description="Episode id입니다.")
    scene_id: str = Field(description="Simulator scene id입니다.")
    step: int = Field(ge=0, description="Episode step index입니다.")
    baseline_type: str = Field(description="대표 실행 경로입니다. 예: rast, object_list, flat_feature.")
    schema_version: str = Field(default=SCHEMA_VERSION, description="RAST schema version입니다.")
    latency: LatencyRecord = Field(description="Stage별 latency breakdown입니다.")
    selected_action: str = Field(description="실제로 simulator에 적용한 action입니다.")
    tokens: list[dict[str, Any]] = Field(default_factory=list, description="직렬화된 RAST token 목록입니다.")

    rast_selected_action: str | None = Field(default=None, description="RAST token planner action입니다.")
    object_list_selected_action: str | None = Field(default=None, description="Object List planner action입니다.")
    flat_feature_selected_action: str | None = Field(default=None, description="Flat Feature planner action입니다.")
    scene_graph_selected_action: str | None = Field(default=None, description="Scene Graph planner action입니다.")
    event_aware_rast_selected_action: str | None = Field(default=None, description="Event-aware RAST planner action입니다.")

    rast_decision: dict[str, Any] = Field(default_factory=dict, description="RAST planner decision trace입니다.")
    object_list_decision: dict[str, Any] = Field(default_factory=dict, description="Object List planner decision trace입니다.")
    flat_feature_decision: dict[str, Any] = Field(default_factory=dict, description="Flat Feature planner decision trace입니다.")
    scene_graph_decision: dict[str, Any] = Field(default_factory=dict, description="Scene Graph planner decision trace입니다.")
    event_aware_rast_decision: dict[str, Any] = Field(default_factory=dict, description="Event-aware RAST planner decision trace입니다.")

    rast_reason_code: str = Field(default="", description="RAST planner reason_code입니다.")
    object_list_reason_code: str = Field(default="", description="Object List planner reason_code입니다.")
    flat_feature_reason_code: str = Field(default="", description="Flat Feature planner reason_code입니다.")
    scene_graph_reason_code: str = Field(default="", description="Scene Graph planner reason_code입니다.")
    event_aware_rast_reason_code: str = Field(default="", description="Event-aware RAST planner reason_code입니다.")

    rast_trigger_token_ids: list[str] = Field(default_factory=list, description="RAST action trigger token id 목록입니다.")
    rast_trigger_object_ids: list[str] = Field(default_factory=list, description="RAST action trigger object id 목록입니다.")
    object_list_trigger_object_ids: list[str] = Field(default_factory=list, description="Object List trigger object id 목록입니다.")
    flat_feature_trigger_object_ids: list[str] = Field(default_factory=list, description="Flat Feature trigger object id 목록입니다.")
    scene_graph_trigger_object_ids: list[str] = Field(default_factory=list, description="Scene Graph trigger object id 목록입니다.")
    event_aware_rast_trigger_event_types: list[str] = Field(
        default_factory=list,
        description="Event-aware RAST trigger event type 목록입니다.",
    )
    event_aware_rast_trigger_token_ids: list[str] = Field(
        default_factory=list,
        description="Event-aware RAST trigger token id 목록입니다.",
    )

    baseline_disagreed: bool | None = Field(default=None, description="호환용 RAST vs Object List disagreement입니다.")
    rast_vs_object_list_disagreed: bool | None = Field(default=None, description="RAST와 Object List action이 다른지 여부입니다.")
    rast_vs_flat_feature_disagreed: bool | None = Field(default=None, description="RAST와 Flat Feature action이 다른지 여부입니다.")
    object_list_vs_flat_feature_disagreed: bool | None = Field(
        default=None,
        description="Object List와 Flat Feature action이 다른지 여부입니다.",
    )
    rast_vs_event_aware_disagreed: bool | None = Field(default=None, description="RAST와 Event-aware RAST action이 다른지 여부입니다.")
    rast_vs_scene_graph_disagreed: bool | None = Field(default=None, description="RAST와 Scene Graph action이 다른지 여부입니다.")
    scene_graph_vs_flat_feature_disagreed: bool | None = Field(
        default=None,
        description="Scene Graph와 Flat Feature action이 다른지 여부입니다.",
    )

    entity_token_count: int = Field(default=0, ge=0, description="EntityToken 개수입니다.")
    risk_token_count: int = Field(default=0, ge=0, description="RiskToken 개수입니다.")
    relation_token_count: int = Field(default=0, ge=0, description="RelationToken 개수입니다.")
    relation_types: list[str] = Field(default_factory=list, description="step에서 생성된 RelationToken type 목록입니다.")
    event_token_count: int = Field(default=0, ge=0, description="EventToken 개수입니다.")
    event_types: list[str] = Field(default_factory=list, description="step에서 감지된 EventToken type 목록입니다.")
    total_token_count: int = Field(default=0, ge=0, description="전체 RAST token 개수입니다.")
    object_list_count: int = Field(default=0, ge=0, description="Object List baseline input unit 개수입니다.")
    flat_feature_row_count: int = Field(default=0, ge=0, description="Flat Feature Table row 개수입니다.")
    scene_graph_node_count: int = Field(default=0, ge=0, description="Scene Graph node 개수입니다.")
    scene_graph_edge_count: int = Field(default=0, ge=0, description="Scene Graph edge 개수입니다.")

    update_mode: str = Field(default="full_recompute", description="Token update mode입니다.")
    changed_object_count: int = Field(default=0, ge=0, description="semantic diff에서 바뀐 object 수입니다.")
    affected_token_count: int = Field(default=0, ge=0, description="incremental update에서 영향을 받은 token 수입니다.")
    full_recompute_latency_ms: float = Field(default=0.0, ge=0, description="full recompute tokenization latency(ms)입니다.")
    incremental_update_latency_ms: float = Field(default=0.0, ge=0, description="incremental update tokenization latency(ms)입니다.")
    incremental_update_benefit: float = Field(default=0.0, description="full recompute 대비 incremental latency benefit입니다.")
    token_generation_latency_ms: float = Field(default=0.0, ge=0, description="선택된 update mode의 token generation latency(ms)입니다.")

    near_miss: bool | None = Field(default=None, description="near-miss hook 결과입니다.")
    collision: bool = Field(default=False, description="collision hook 결과입니다.")
    min_object_distance: float | None = Field(default=None, ge=0, description="Agent와 가장 가까운 object까지의 거리입니다.")
    phase: str | None = Field(default=None, description="실험 phase입니다. 예: windows_metadata_sim_oracle.")

    observation_ref: str | None = Field(default=None, description="Raw observation pointer입니다.")
    metadata_snapshot_ref: str | None = Field(default=None, description="Metadata snapshot pointer입니다.")
    extra: dict[str, Any] = Field(default_factory=dict, description="후속 batch 확장을 위한 부가 정보입니다.")

    event_policy_variant: str = Field(default="full", description="Event-aware RAST policy ablation variant입니다.")
    risk_threshold: float | None = Field(default=None, ge=0, description="RiskToken 생성에 사용한 threshold입니다.")
    near_miss_threshold: float | None = Field(default=None, ge=0, description="Near-miss 계산에 사용한 threshold입니다.")
    position_noise_std: float = Field(default=0.0, ge=0, description="metadata position synthetic noise 표준편차입니다.")
    distance_noise_std: float = Field(default=0.0, ge=0, description="metadata distance synthetic noise 표준편차입니다.")
    visibility_flip_prob: float = Field(default=0.0, ge=0, le=1, description="metadata visibility flip 확률입니다.")

    @classmethod
    def from_parts(
        cls,
        *,
        run_id: str,
        episode_id: str,
        scene_id: str,
        step: int,
        baseline_type: str,
        latency: LatencyRecord,
        selected_action: str,
        tokens: list[Any] | None = None,
        **kwargs: Any,
    ) -> "StepLogRecord":
        """Pydantic token 또는 dict token을 JSONL 저장용 record로 묶습니다."""

        serialized_tokens = [_to_plain_dict(token) for token in (tokens or [])]
        kwargs.setdefault("rast_selected_action", selected_action)
        kwargs.setdefault("token_generation_latency_ms", latency.token_generation)
        _populate_decision_fields(kwargs, "rast")
        _populate_decision_fields(kwargs, "object_list")
        _populate_decision_fields(kwargs, "flat_feature")
        _populate_decision_fields(kwargs, "scene_graph")
        _populate_decision_fields(kwargs, "event_aware_rast")

        rast_action = kwargs.get("rast_selected_action") or selected_action
        object_list_action = kwargs.get("object_list_selected_action")
        flat_feature_action = kwargs.get("flat_feature_selected_action")
        scene_graph_action = kwargs.get("scene_graph_selected_action")
        event_aware_action = kwargs.get("event_aware_rast_selected_action")

        if object_list_action is not None and kwargs.get("rast_vs_object_list_disagreed") is None:
            kwargs["rast_vs_object_list_disagreed"] = rast_action != object_list_action
        if flat_feature_action is not None and kwargs.get("rast_vs_flat_feature_disagreed") is None:
            kwargs["rast_vs_flat_feature_disagreed"] = rast_action != flat_feature_action
        if (
            object_list_action is not None
            and flat_feature_action is not None
            and kwargs.get("object_list_vs_flat_feature_disagreed") is None
        ):
            kwargs["object_list_vs_flat_feature_disagreed"] = object_list_action != flat_feature_action
        if event_aware_action is not None and kwargs.get("rast_vs_event_aware_disagreed") is None:
            kwargs["rast_vs_event_aware_disagreed"] = rast_action != event_aware_action
        if scene_graph_action is not None and kwargs.get("rast_vs_scene_graph_disagreed") is None:
            kwargs["rast_vs_scene_graph_disagreed"] = rast_action != scene_graph_action
        if (
            scene_graph_action is not None
            and flat_feature_action is not None
            and kwargs.get("scene_graph_vs_flat_feature_disagreed") is None
        ):
            kwargs["scene_graph_vs_flat_feature_disagreed"] = scene_graph_action != flat_feature_action
        if kwargs.get("baseline_disagreed") is None:
            kwargs["baseline_disagreed"] = kwargs.get("rast_vs_object_list_disagreed")

        return cls(
            run_id=run_id,
            episode_id=episode_id,
            scene_id=scene_id,
            step=step,
            baseline_type=baseline_type,
            latency=latency,
            selected_action=selected_action,
            tokens=serialized_tokens,
            **kwargs,
        )


def _to_plain_dict(value: Any) -> dict[str, Any]:
    """Pydantic 모델과 일반 dict를 JSONL payload로 변환합니다."""

    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        return value
    raise TypeError(f"JSONL payload로 직렬화할 수 없는 값입니다: {type(value)!r}")


def _populate_decision_fields(kwargs: dict[str, Any], planner_prefix: str) -> None:
    """PlannerDecision이 들어오면 action, reason_code, trigger field를 자동으로 채웁니다."""

    decision_key = f"{planner_prefix}_decision"
    decision = kwargs.get(decision_key)
    if decision is None:
        return
    decision_payload = _to_plain_dict(decision)
    kwargs[decision_key] = decision_payload

    action = decision_payload.get("action")
    selected_action_key = f"{planner_prefix}_selected_action"
    if action is not None and kwargs.get(selected_action_key) is None:
        kwargs[selected_action_key] = str(action)

    reason_code_key = f"{planner_prefix}_reason_code"
    if kwargs.get(reason_code_key) in (None, ""):
        kwargs[reason_code_key] = str(decision_payload.get("reason_code") or "")

    trigger_object_ids = list(decision_payload.get("trigger_object_ids") or [])
    trigger_token_ids = list(decision_payload.get("trigger_token_ids") or [])
    if planner_prefix == "rast":
        kwargs.setdefault("rast_trigger_token_ids", trigger_token_ids)
        kwargs.setdefault("rast_trigger_object_ids", trigger_object_ids)
    elif planner_prefix == "object_list":
        kwargs.setdefault("object_list_trigger_object_ids", trigger_object_ids)
    elif planner_prefix == "flat_feature":
        kwargs.setdefault("flat_feature_trigger_object_ids", trigger_object_ids)
    elif planner_prefix == "scene_graph":
        kwargs.setdefault("scene_graph_trigger_object_ids", trigger_object_ids)
    elif planner_prefix == "event_aware_rast":
        trigger_features = decision_payload.get("trigger_features") or {}
        kwargs.setdefault("event_aware_rast_trigger_token_ids", trigger_token_ids)
        kwargs.setdefault("event_aware_rast_trigger_event_types", list(trigger_features.get("event_types") or []))

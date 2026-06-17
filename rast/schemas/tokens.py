"""RAST MVP-0에서 사용하는 planner-facing token schema입니다."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from rast.schemas.common import RASTBaseModel, SCHEMA_VERSION, BBox2D, Vector3


class BaseToken(RASTBaseModel):
    """모든 RAST token이 공유하는 최소 envelope입니다."""

    token_id: str = Field(description="Token stream 내 고유 식별자입니다.")
    type: str = Field(description="Token type 이름입니다.")
    schema_version: str = Field(default=SCHEMA_VERSION, description="RAST schema version입니다.")
    timestamp: int | float | None = Field(default=None, description="생성 step 또는 timestamp입니다.")


class EntityToken(BaseToken):
    """객체, 위치, 거리, confidence를 planner-facing 형태로 표현합니다."""

    type: Literal["EntityToken"] = "EntityToken"
    entity_id: str = Field(description="원본 object id 또는 entity id입니다.")
    category: str = Field(description="객체 category입니다.")
    position: Vector3 = Field(description="객체 중심 위치입니다.")
    distance_to_agent: float = Field(ge=0, description="Agent와 객체 사이 거리입니다.")
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "Phase 1 oracle metadata 기본 confidence입니다. 실제 perception confidence가 아니며 "
            "Phase 2에서 perception model confidence로 대체해야 합니다."
        ),
    )
    velocity: Vector3 | None = Field(default=None, description="추정 속도입니다.")
    bbox_2d: BBox2D | None = Field(default=None, description="근거 이미지 영역입니다.")
    size: Vector3 | None = Field(default=None, description="객체 크기입니다.")
    semantic_attributes: dict[str, Any] = Field(default_factory=dict, description="추가 semantic 속성입니다.")
    is_visible: bool | None = Field(default=None, description="현재 observation에서 보이는지 여부입니다.")
    source: str = Field(default="oracle_metadata", description="Token 생성 source입니다.")


class RiskToken(BaseToken):
    """충돌, near-path obstacle 등 safety cue를 명시적으로 표현합니다."""

    type: Literal["RiskToken"] = "RiskToken"
    risk_type: str = Field(description="예: near_path_obstacle, collision_risk입니다.")
    severity: str = Field(description="예: low, medium, high입니다.")
    entity_id: str = Field(description="위험과 연결된 entity id입니다.")
    affected_area: dict[str, Any] = Field(description="영향을 받는 path segment 또는 공간 영역입니다.")
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "Phase 1 oracle metadata 기반 confidence입니다. 실제 perception confidence가 아니며 "
            "후속 perception-bound extractor에서 갱신되어야 합니다."
        ),
    )
    risk_score: float | None = Field(default=None, ge=0, le=1, description="정규화된 위험 점수입니다.")
    recommended_policy: str | None = Field(default=None, description="Planner가 참고할 수 있는 보수적 행동 힌트입니다.")
    time_to_collision: float | None = Field(default=None, ge=0, description="추정 충돌까지 남은 시간입니다.")
    path_segment_id: str | None = Field(default=None, description="관련 path segment id입니다.")
    evidence_token_id: str | None = Field(default=None, description="관련 EvidenceToken id입니다.")
    risk_features: dict[str, Any] = Field(default_factory=dict, description="risk score 계산에 사용한 feature 기록입니다.")


class RelationToken(BaseToken):
    """Navigation planning에 필요한 agent-object relation을 명시적으로 표현합니다."""

    type: Literal["RelationToken"] = "RelationToken"
    subject_id: str = Field(description="Relation의 주체 id입니다. MVP에서는 주로 agent를 사용합니다.")
    relation: Literal["near_agent", "near_path", "blocking_path", "target_reachable"] = Field(
        description="Navigation relation type입니다."
    )
    object_id: str = Field(description="Relation의 대상 object 또는 goal id입니다.")
    timestamp: int | float = Field(description="RelationToken이 생성된 step 또는 timestamp입니다.")
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "Phase 1 oracle metadata 기반 relation confidence입니다. 실제 learned relation confidence가 아니며 "
            "후속 perception-bound extractor에서 별도 추정해야 합니다."
        ),
    )
    distance_margin: float | None = Field(
        default=None,
        description="Relation threshold까지의 여유 거리입니다. 양수면 threshold 안쪽에 있음을 의미합니다.",
    )
    path_segment_id: str | None = Field(default=None, description="Relation이 참조하는 path proxy segment id입니다.")
    relation_features: dict[str, Any] = Field(default_factory=dict, description="Relation 계산에 사용한 feature 기록입니다.")


class EventToken(BaseToken):
    """이전 step과 현재 step 사이의 semantic scene change를 표현합니다."""

    type: Literal["EventToken"] = "EventToken"
    event_type: Literal["object_appeared", "object_disappeared", "object_moved", "risk_changed"] = Field(
        description="감지된 semantic event type입니다."
    )
    entity_id: str = Field(description="event와 연결된 entity id입니다.")
    previous_state: dict[str, Any] = Field(description="이전 step의 entity/risk 상태입니다.")
    current_state: dict[str, Any] = Field(description="현재 step의 entity/risk 상태입니다.")
    severity: str = Field(description="event 중요도입니다. MVP에서는 low, medium, high 문자열을 사용합니다.")
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "Phase 1 oracle metadata 기반 event confidence입니다. 실제 perception confidence가 아니며 "
            "Phase 2 perception-bound extractor에서 별도 산정해야 합니다."
        ),
    )


class UncertaintyToken(BaseToken):
    """분류, 위치, occlusion, sensor agreement 관련 불확실성을 명시적으로 표현합니다."""

    type: Literal["UncertaintyToken"] = "UncertaintyToken"
    uncertainty_type: Literal[
        "classification_uncertainty",
        "position_uncertainty",
        "partial_occlusion",
        "low_sensor_agreement",
        "unknown_object",
    ] = Field(description="Planner가 구분해 볼 uncertainty type입니다.")
    entity_id: str = Field(description="불확실성과 연결된 entity id입니다.")
    level: Literal["low", "medium", "high"] = Field(description="불확실성 수준입니다.")
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "Phase 1 synthetic metadata 기반 confidence입니다. 실제 perception uncertainty calibration이 아니며 "
            "후속 perception-bound extractor에서 별도 보정해야 합니다."
        ),
    )
    variance: float | None = Field(default=None, ge=0, description="position uncertainty 등에 사용하는 variance proxy입니다.")
    possible_categories: list[str] = Field(default_factory=list, description="classification uncertainty 후보 category입니다.")
    occluded_by: str | None = Field(default=None, description="occlusion을 유발한 object id입니다.")
    recommended_action: Literal[
        "proceed",
        "slow_down",
        "inspect_before_passing",
        "replan_around",
        "treat_as_risk",
    ] | None = Field(default=None, description="Planner가 참고할 수 있는 보수적 행동 힌트입니다.")
    sensor_agreement: float | None = Field(default=None, ge=0, le=1, description="synthetic sensor agreement proxy입니다.")
    uncertainty_features: dict[str, Any] = Field(default_factory=dict, description="uncertainty rule 계산에 사용한 feature 기록입니다.")

class AffordanceToken(BaseToken):
    """Navigation affordance瑜?planner-facing token?쇰줈 ?쒗쁽?⑸땲??"""

    type: Literal["AffordanceToken"] = "AffordanceToken"
    entity_id: str = Field(description="Affordance媛 ?곌껐??object id ?먮뒗 region id?낅땲??")
    affordance: Literal[
        "passable",
        "blocking",
        "narrow_passage",
        "target_reachable",
        "inspect_required",
        "avoid_required",
    ] = Field(description="Navigation affordance type?낅땲?? manipulation affordance? MVP?먯꽌 ?쒖쇅?⑸땲??")
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "Phase 1 synthetic metadata 湲곕컲 affordance confidence?낅땲?? "
            "?ㅼ젣 robot action feasibility 寃利앷낵媛 ?꾨떃?덈떎."
        ),
    )
    preconditions: list[str] = Field(default_factory=list, description="?대떦 affordance媛 ?좏슚?섍린 ?꾪븳 理쒖냼 議곌굔?낅땲??")
    action_hint: str | None = Field(default=None, description="Planner媛 李멸퀬?????덈뒗 navigation action hint?낅땲??")
    navigation_margin: float | None = Field(default=None, description="path/gap/goal relation怨??곌껐??margin proxy?낅땲??")
    failure_risk: float | None = Field(default=None, ge=0, le=1, description="?ㅽ뙣 ?먮뒗 ?뚰뵾 ?꾪뿕 proxy?낅땲??")
    related_token_ids: list[str] = Field(default_factory=list, description="Affordance? ?곌껐??Risk/Relation/Uncertainty token id 紐⑸줉?낅땲??")
    evidence_token_ids: list[str] = Field(default_factory=list, description="Affordance? ?곌껐??EvidenceToken id 紐⑸줉?낅땲??")
    affordance_features: dict[str, Any] = Field(default_factory=dict, description="affordance rule 怨꾩궛???ъ슜??feature 湲곕줉?낅땲??")


class EvidenceToken(BaseToken):
    """Token, event, planner decision이 참조한 metadata 근거 pointer를 기록합니다."""

    type: Literal["EvidenceToken"] = "EvidenceToken"
    evidence_type: Literal[
        "metadata_object",
        "metadata_snapshot",
        "bbox_2d",
        "risk_feature",
        "uncertainty_feature",
        "event_diff",
        "planner_decision",
    ] = Field(description="근거가 가리키는 evidence 종류입니다.")
    source: str = Field(description="Evidence를 생성한 source입니다. MVP에서는 metadata simulator가 기본입니다.")
    pointer: str = Field(description="metadata snapshot, object, token, decision을 재확인하기 위한 pointer입니다.")
    entity_id: str | None = Field(default=None, description="Evidence와 연결된 entity id입니다.")
    related_token_ids: list[str] = Field(default_factory=list, description="이 evidence가 뒷받침하는 token id 목록입니다.")
    related_decision_ids: list[str] = Field(default_factory=list, description="이 evidence가 뒷받침하는 planner decision id 목록입니다.")
    bbox_2d: BBox2D | None = Field(default=None, description="metadata에 bbox-like 정보가 있을 때의 2D bbox pointer입니다.")
    metadata_path: str | None = Field(default=None, description="metadata 내부 경로 또는 object key path입니다.")
    snapshot_ref: str | None = Field(default=None, description="ObservationSnapshot 또는 metadata snapshot reference입니다.")
    frame_id: str | None = Field(default=None, description="향후 RGB/depth frame과 연결하기 위한 optional frame id입니다.")
    confidence_source: str | None = Field(default=None, description="confidence가 어떤 source에서 왔는지 나타냅니다.")
    evidence_features: dict[str, Any] = Field(
        default_factory=dict,
        description="risk, uncertainty, event diff, planner reason 등 evidence 재구성에 필요한 feature입니다.",
    )

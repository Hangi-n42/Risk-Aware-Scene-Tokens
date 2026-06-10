"""RAST MVP-0에서 사용하는 EntityToken과 RiskToken schema입니다."""

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

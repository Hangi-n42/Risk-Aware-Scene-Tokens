"""Simulator event를 공통 ObservationSnapshot으로 정규화하는 schema입니다."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from rast.schemas.common import RASTBaseModel, SCHEMA_VERSION, BBox2D, Vector3


class AgentState(RASTBaseModel):
    """Agent의 최소 pose 상태입니다."""

    position: Vector3 = Field(description="Agent의 simulator 좌표계 위치입니다.")
    rotation: Vector3 | None = Field(
        default=None,
        description="Agent 회전입니다. AI2-THOR yaw/pitch/roll 값을 담을 수 있습니다.",
    )
    horizon: float | None = Field(default=None, description="카메라 pitch 또는 horizon 값입니다.")


class ObjectMetadata(RASTBaseModel):
    """Phase 1 oracle metadata에서 추출한 객체 단위 snapshot입니다."""

    object_id: str = Field(description="Simulator가 제공하는 객체 식별자입니다.")
    category: str = Field(description="객체 category 또는 object type입니다.")
    position: Vector3 = Field(description="객체 중심 위치입니다.")
    distance_to_agent: float | None = Field(
        default=None,
        ge=0,
        description="Agent와 객체 사이 거리입니다. 없으면 후속 adapter/tokenizer가 계산할 수 있습니다.",
    )
    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description=(
            "Phase 1 oracle metadata 기본 confidence입니다. 실제 perception confidence가 아니며 "
            "Phase 2 perception-bound extractor에서 교체되어야 합니다."
        ),
    )
    visible: bool | None = Field(default=None, description="Simulator visibility flag입니다.")
    size: Vector3 | None = Field(default=None, description="객체 크기 또는 bounding box size입니다.")
    bbox_2d: BBox2D | None = Field(default=None, description="원본 이미지 영역 pointer입니다.")
    classification_confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Synthetic metadata의 classification confidence입니다. 실제 perception confidence가 아닙니다.",
    )
    classification_uncertainty: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Synthetic metadata의 classification uncertainty proxy입니다.",
    )
    position_variance: float = Field(default=0.0, ge=0, description="Synthetic metadata의 position variance proxy입니다.")
    occlusion_ratio: float = Field(default=0.0, ge=0, le=1, description="Synthetic partial occlusion ratio입니다.")
    sensor_agreement: float = Field(default=1.0, ge=0, le=1, description="Synthetic multi-sensor agreement proxy입니다.")
    possible_categories: list[str] = Field(default_factory=list, description="분류가 불확실할 때 가능한 category 후보입니다.")
    is_unknown: bool = Field(default=False, description="UnknownObject 계열 object인지 여부입니다.")
    raw: dict[str, Any] = Field(
        default_factory=dict,
        description="디버깅용 최소 원본 metadata 조각입니다. 대용량 raw dump 저장은 피합니다.",
    )


class ObservationSnapshot(RASTBaseModel):
    """Baseline과 RAST tokenization이 공유하는 information-bound snapshot입니다."""

    schema_version: str = Field(default=SCHEMA_VERSION, description="RAST schema version입니다.")
    scene_id: str = Field(description="Simulator scene 식별자입니다.")
    step: int = Field(ge=0, description="Episode 내 step index입니다.")
    agent_state: AgentState = Field(description="현재 agent 상태입니다.")
    objects: list[ObjectMetadata] = Field(default_factory=list, description="동일 source에서 온 객체 목록입니다.")
    episode_id: str | None = Field(default=None, description="Episode 식별자입니다.")
    timestamp: float | None = Field(default=None, description="Snapshot 생성 시각 또는 simulator timestamp입니다.")
    raw_observation_ref: str | None = Field(default=None, description="RGB/depth frame 등 raw observation pointer입니다.")
    metadata_snapshot_ref: str | None = Field(default=None, description="저장된 metadata snapshot pointer입니다.")
    source: str = Field(default="oracle_metadata", description="Snapshot 생성 source입니다.")

"""Flat Feature Table baseline representation을 생성합니다."""

from __future__ import annotations

from math import radians, sin, cos

from pydantic import Field

from rast.schemas.common import RASTBaseModel
from rast.schemas.observation import ObjectMetadata, ObservationSnapshot
from rast.tokenizer.entity_tokenizer import object_distance_to_agent
from rast.tokenizer.risk_tokenizer import distance_risk_score


class FlatFeatureRow(RASTBaseModel):
    """토큰 계약을 제거하고 object별 scalar feature만 담는 baseline row입니다."""

    object_id: str = Field(description="원본 object id입니다.")
    category: str = Field(description="객체 category입니다.")
    x: float = Field(description="객체 위치 x 좌표입니다.")
    y: float = Field(description="객체 위치 y 좌표입니다.")
    z: float = Field(description="객체 위치 z 좌표입니다.")
    visible: bool | None = Field(default=None, description="Observation visibility입니다.")
    distance_to_agent: float = Field(ge=0, description="Agent와 객체 사이 거리입니다.")
    distance_to_path_proxy: float = Field(ge=0, description="Agent forward ray 기준 lateral distance입니다.")
    object_size_proxy: float = Field(ge=0, description="객체 크기를 대표하는 scalar proxy입니다.")
    is_unknown: bool = Field(description="UnknownObject 계열 category 여부입니다.")
    risk_score_scalar: float = Field(ge=0, le=1, description="거리 기반 scalar risk score입니다.")
    within_risk_threshold: bool = Field(description="risk threshold 안에 들어오는지 여부입니다.")
    confidence: float = Field(ge=0, le=1, description="Phase 1 oracle metadata confidence입니다.")


def build_flat_feature_table(
    snapshot: ObservationSnapshot,
    *,
    risk_threshold: float,
    visible_only: bool = True,
) -> list[FlatFeatureRow]:
    """ObservationSnapshot과 같은 object source에서 flat scalar feature table을 생성합니다."""

    if risk_threshold <= 0:
        raise ValueError("risk_threshold는 0보다 커야 합니다.")

    return [
        _object_to_flat_row(obj, snapshot, risk_threshold=risk_threshold)
        for obj in snapshot.objects
        if not visible_only or obj.visible is not False
    ]


def _object_to_flat_row(
    obj: ObjectMetadata,
    snapshot: ObservationSnapshot,
    *,
    risk_threshold: float,
) -> FlatFeatureRow:
    distance = object_distance_to_agent(obj, snapshot.agent_state.position)
    return FlatFeatureRow(
        object_id=obj.object_id,
        category=obj.category,
        x=obj.position.x,
        y=obj.position.y,
        z=obj.position.z,
        visible=obj.visible,
        distance_to_agent=distance,
        distance_to_path_proxy=distance_to_path_proxy(obj, snapshot),
        object_size_proxy=object_size_proxy(obj),
        is_unknown=obj.category.lower().startswith("unknown"),
        risk_score_scalar=distance_risk_score(distance_to_agent=distance, threshold=risk_threshold),
        within_risk_threshold=distance <= risk_threshold,
        confidence=obj.confidence,
    )


def distance_to_path_proxy(obj: ObjectMetadata, snapshot: ObservationSnapshot) -> float:
    """현재 agent yaw를 기준으로 forward ray와 객체 사이의 2D lateral distance를 계산합니다."""

    agent_position = snapshot.agent_state.position
    yaw_degrees = 0.0
    if snapshot.agent_state.rotation is not None:
        yaw_degrees = snapshot.agent_state.rotation.y
    yaw = radians(yaw_degrees)
    forward_x = sin(yaw)
    forward_z = cos(yaw)
    dx = obj.position.x - agent_position.x
    dz = obj.position.z - agent_position.z
    return abs((dx * forward_z) - (dz * forward_x))


def object_size_proxy(obj: ObjectMetadata) -> float:
    """size metadata가 있으면 가장 큰 축 길이를 대표 크기로 사용합니다."""

    if obj.size is None:
        return 0.0
    return max(obj.size.x, obj.size.y, obj.size.z)

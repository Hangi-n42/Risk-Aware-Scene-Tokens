"""ObservationSnapshot에서 EntityToken을 생성합니다."""

from __future__ import annotations

from math import sqrt

from rast.schemas.common import Vector3
from rast.schemas.observation import ObjectMetadata, ObservationSnapshot
from rast.schemas.tokens import EntityToken


def build_entity_tokens(snapshot: ObservationSnapshot, *, visible_only: bool = True) -> list[EntityToken]:
    """Phase 1 oracle metadata 기반 EntityToken을 생성합니다.

    confidence 기본값 1.0은 simulator metadata를 신뢰하는 oracle 값이며,
    실제 perception model confidence가 아닙니다.
    """

    tokens: list[EntityToken] = []
    for index, obj in enumerate(_iter_objects(snapshot, visible_only=visible_only)):
        distance = object_distance_to_agent(obj, snapshot.agent_state.position)
        tokens.append(
            EntityToken(
                token_id=f"ent_{index:04d}",
                entity_id=obj.object_id,
                category=obj.category,
                position=obj.position,
                distance_to_agent=distance,
                confidence=obj.confidence,
                bbox_2d=obj.bbox_2d,
                size=obj.size,
                is_visible=obj.visible,
                source=snapshot.source,
                timestamp=snapshot.step,
            )
        )
    return tokens


def object_distance_to_agent(obj: ObjectMetadata, agent_position: Vector3) -> float:
    """객체 metadata에 거리가 없으면 agent 위치에서 유클리드 거리로 계산합니다."""

    if obj.distance_to_agent is not None:
        return obj.distance_to_agent
    return vector_distance(obj.position, agent_position)


def vector_distance(first: Vector3, second: Vector3) -> float:
    """두 3D 좌표 사이의 유클리드 거리입니다."""

    return sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2 + (first.z - second.z) ** 2)


def _iter_objects(snapshot: ObservationSnapshot, *, visible_only: bool) -> list[ObjectMetadata]:
    if not visible_only:
        return list(snapshot.objects)
    return [obj for obj in snapshot.objects if obj.visible is not False]

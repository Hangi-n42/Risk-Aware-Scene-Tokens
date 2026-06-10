"""Object List baseline representation을 생성합니다."""

from __future__ import annotations

from pydantic import Field

from rast.schemas.common import RASTBaseModel, Vector3
from rast.schemas.observation import ObjectMetadata, ObservationSnapshot
from rast.tokenizer.entity_tokenizer import object_distance_to_agent


class ObjectListItem(RASTBaseModel):
    """RiskToken contract 없이 object fact만 담는 baseline row입니다."""

    object_id: str = Field(description="원본 object id입니다.")
    category: str = Field(description="객체 category입니다.")
    position: Vector3 = Field(description="객체 위치입니다.")
    visible: bool | None = Field(default=None, description="Observation visibility입니다.")
    distance_to_agent: float = Field(ge=0, description="Agent와 객체 사이 거리입니다.")
    confidence: float = Field(description="Oracle metadata 기반 confidence입니다.")


def build_object_list(snapshot: ObservationSnapshot, *, visible_only: bool = True) -> list[ObjectListItem]:
    """RAST EntityToken과 같은 ObservationSnapshot object source에서 baseline을 생성합니다."""

    return [
        _object_to_item(obj, snapshot)
        for obj in snapshot.objects
        if not visible_only or obj.visible is not False
    ]


def _object_to_item(obj: ObjectMetadata, snapshot: ObservationSnapshot) -> ObjectListItem:
    return ObjectListItem(
        object_id=obj.object_id,
        category=obj.category,
        position=obj.position,
        visible=obj.visible,
        distance_to_agent=object_distance_to_agent(obj, snapshot.agent_state.position),
        confidence=obj.confidence,
    )

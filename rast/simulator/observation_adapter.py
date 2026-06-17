"""AI2-THOR metadata-like dict를 ObservationSnapshot으로 변환합니다.

Adapter는 Controller에 의존하지 않는 pure function입니다. Batch 2 fixture와
실제 AI2-THOR event.metadata가 가능한 한 같은 변환 경로를 사용하도록 둡니다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from rast.schemas.common import BBox2D, Vector3
from rast.schemas.observation import AgentState, ObjectMetadata, ObservationSnapshot


def event_to_observation_snapshot(
    event: Any,
    *,
    step: int | None = None,
    episode_id: str | None = None,
    raw_observation_ref: str | None = None,
    metadata_snapshot_ref: str | None = None,
    source: str = "oracle_metadata",
) -> ObservationSnapshot:
    """AI2-THOR event 또는 event-like 객체에서 metadata를 꺼내 snapshot으로 변환합니다."""

    if isinstance(event, Mapping) and "metadata" in event:
        metadata = event["metadata"]
    else:
        metadata = getattr(event, "metadata", event)
    return metadata_to_observation_snapshot(
        metadata,
        step=step,
        episode_id=episode_id,
        raw_observation_ref=raw_observation_ref,
        metadata_snapshot_ref=metadata_snapshot_ref,
        source=source,
    )


def metadata_to_observation_snapshot(
    metadata: Mapping[str, Any],
    *,
    step: int | None = None,
    episode_id: str | None = None,
    raw_observation_ref: str | None = None,
    metadata_snapshot_ref: str | None = None,
    source: str = "oracle_metadata",
) -> ObservationSnapshot:
    """AI2-THOR metadata-like dict를 공통 ObservationSnapshot으로 변환합니다."""

    if not isinstance(metadata, Mapping):
        raise ValueError("metadata는 mapping/dict 형태여야 합니다.")

    scene_id = _first_present(metadata, "sceneName", "scene_id", "sceneId", "scene")
    if not scene_id:
        raise ValueError("metadata에 scene id 필드(sceneName 또는 scene_id)가 없습니다.")

    agent_metadata = _require_mapping(metadata, "agent")
    agent_state = AgentState(
        position=_required_vector(agent_metadata, "position", context="agent.position"),
        rotation=_optional_vector(agent_metadata.get("rotation"), context="agent.rotation"),
        horizon=_first_present(agent_metadata, "cameraHorizon", "horizon"),
    )

    objects_metadata = metadata.get("objects")
    if not isinstance(objects_metadata, list):
        raise ValueError("metadata.objects는 list여야 합니다.")

    snapshot_step = step
    if snapshot_step is None:
        snapshot_step = int(_first_present(metadata, "step", "lastActionStep", default=0))

    objects: list[ObjectMetadata] = []
    for index, item in enumerate(objects_metadata):
        if not isinstance(item, Mapping):
            raise ValueError(f"objects[{index}]는 dict 형태여야 합니다.")
        objects.append(_object_metadata_from_ai2thor(item, index=index))

    return ObservationSnapshot(
        scene_id=str(scene_id),
        step=snapshot_step,
        episode_id=episode_id,
        agent_state=agent_state,
        objects=objects,
        raw_observation_ref=raw_observation_ref,
        metadata_snapshot_ref=metadata_snapshot_ref,
        source=source,
    )


def _object_metadata_from_ai2thor(item: Mapping[str, Any], *, index: int) -> ObjectMetadata:
    """AI2-THOR object metadata 한 개를 ObjectMetadata로 변환합니다."""

    object_id = _first_present(item, "objectId", "object_id", "id")
    if not object_id:
        raise ValueError(f"objects[{index}]에 object id(objectId)가 없습니다.")

    category = _first_present(item, "objectType", "category", "type", "name")
    if not category:
        raise ValueError(f"objects[{index}]에 category/objectType 필드가 없습니다.")

    position_source = item.get("position")
    if position_source is None:
        bbox = item.get("axisAlignedBoundingBox")
        if isinstance(bbox, Mapping):
            position_source = bbox.get("center")
    if position_source is None:
        raise ValueError(f"objects[{index}]에 position 필드가 없습니다.")

    bbox_2d = _optional_bbox2d(_first_present(item, "bbox2D", "bbox_2d", "bounds2D"))
    size = _optional_size(item)

    return ObjectMetadata(
        object_id=str(object_id),
        category=str(category),
        position=_vector_from_value(position_source, context=f"objects[{index}].position"),
        distance_to_agent=_optional_float(_first_present(item, "distance", "distance_to_agent")),
        confidence=float(_first_present(item, "confidence", "classificationConfidence", "classification_confidence", default=1.0)),
        visible=_optional_bool(item.get("visible")),
        size=size,
        bbox_2d=bbox_2d,
        classification_confidence=float(
            _first_present(item, "classification_confidence", "classificationConfidence", "confidence", default=1.0)
        ),
        classification_uncertainty=float(
            _first_present(item, "classification_uncertainty", "classificationUncertainty", default=0.0)
        ),
        position_variance=float(_first_present(item, "position_variance", "positionVariance", default=0.0)),
        occlusion_ratio=float(_first_present(item, "occlusion_ratio", "occlusionRatio", default=0.0)),
        sensor_agreement=float(_first_present(item, "sensor_agreement", "sensorAgreement", default=1.0)),
        possible_categories=list(_first_present(item, "possible_categories", "possibleCategories", default=[])),
        is_unknown=bool(
            _first_present(
                item,
                "is_unknown",
                "isUnknown",
                default=str(category).lower().startswith("unknown"),
            )
        ),
        raw=_minimal_raw(item),
    )


def _optional_size(item: Mapping[str, Any]) -> Vector3 | None:
    direct_size = item.get("size")
    if direct_size is not None:
        return _vector_from_value(direct_size, context="object.size")
    for box_key in ("axisAlignedBoundingBox", "objectOrientedBoundingBox"):
        box = item.get(box_key)
        if isinstance(box, Mapping) and box.get("size") is not None:
            return _vector_from_value(box["size"], context=f"{box_key}.size")
    return None


def _minimal_raw(item: Mapping[str, Any]) -> dict[str, Any]:
    """로그 비대화를 피하기 위해 adapter 검증에 유용한 최소 원본 필드만 보존합니다."""

    keys = (
        "objectId",
        "objectType",
        "visible",
        "distance",
        "classification_confidence",
        "classification_uncertainty",
        "position_variance",
        "occlusion_ratio",
        "sensor_agreement",
        "possible_categories",
        "is_unknown",
    )
    return {key: item[key] for key in keys if key in item}


def _require_mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"metadata.{key}는 dict 형태여야 합니다.")
    return value


def _first_present(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def _required_vector(mapping: Mapping[str, Any], key: str, *, context: str) -> Vector3:
    if key not in mapping:
        raise ValueError(f"{context} 필드가 없습니다.")
    return _vector_from_value(mapping[key], context=context)


def _optional_vector(value: Any, *, context: str) -> Vector3 | None:
    if value is None:
        return None
    return _vector_from_value(value, context=context)


def _vector_from_value(value: Any, *, context: str) -> Vector3:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context}는 x/y/z를 가진 dict여야 합니다.")
    missing = [axis for axis in ("x", "y", "z") if axis not in value]
    if missing:
        raise ValueError(f"{context}에 누락된 축이 있습니다: {', '.join(missing)}")
    return Vector3(x=float(value["x"]), y=float(value["y"]), z=float(value["z"]))


def _optional_bbox2d(value: Any) -> BBox2D | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        if {"x", "y", "width", "height"}.issubset(value):
            return BBox2D(
                x=float(value["x"]),
                y=float(value["y"]),
                width=float(value["width"]),
                height=float(value["height"]),
            )
        if {"x", "y", "w", "h"}.issubset(value):
            return BBox2D(x=float(value["x"]), y=float(value["y"]), width=float(value["w"]), height=float(value["h"]))
    if isinstance(value, list | tuple) and len(value) == 4:
        left, top, right, bottom = [float(number) for number in value]
        return BBox2D(x=left, y=top, width=max(0.0, right - left), height=max(0.0, bottom - top))
    return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)

"""TokenMemory 상태 간 semantic diff를 계산합니다."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Literal

from rast.schemas.common import Vector3
from rast.schemas.tokens import EntityToken, RiskToken


EventType = Literal["object_appeared", "object_disappeared", "object_moved", "risk_changed"]


@dataclass(frozen=True)
class EventCandidate:
    """EventToken으로 변환하기 전의 simulator 독립 event 후보입니다."""

    event_type: EventType
    entity_id: str
    previous_state: dict[str, Any]
    current_state: dict[str, Any]
    severity: str
    confidence: float = 1.0


def state_from_tokens(entities: list[EntityToken], risks: list[RiskToken]) -> dict[str, Any]:
    """EntityToken/RiskToken list를 diff 가능한 dict state로 변환합니다."""

    return {
        "objects": {entity.entity_id: _entity_state(entity) for entity in entities},
        "risks": {risk.entity_id: _risk_state(risk) for risk in risks},
    }


def diff_states(
    previous_state: dict[str, Any] | None,
    current_state: dict[str, Any],
    *,
    movement_threshold: float,
    risk_score_delta_threshold: float,
) -> list[EventCandidate]:
    """이전 state와 현재 state를 비교해 semantic event 후보를 반환합니다."""

    if movement_threshold < 0:
        raise ValueError("movement_threshold는 0 이상이어야 합니다.")
    if risk_score_delta_threshold < 0:
        raise ValueError("risk_score_delta_threshold는 0 이상이어야 합니다.")
    if previous_state is None:
        return []

    previous_objects = _objects(previous_state)
    current_objects = _objects(current_state)
    previous_risks = _risks(previous_state)
    current_risks = _risks(current_state)

    candidates: list[EventCandidate] = []
    candidates.extend(_diff_object_presence(previous_objects, current_objects))
    candidates.extend(_diff_object_motion(previous_objects, current_objects, movement_threshold=movement_threshold))
    candidates.extend(
        _diff_risk_state(
            previous_risks,
            current_risks,
            risk_score_delta_threshold=risk_score_delta_threshold,
        )
    )
    return candidates


def _diff_object_presence(
    previous_objects: dict[str, dict[str, Any]],
    current_objects: dict[str, dict[str, Any]],
) -> list[EventCandidate]:
    candidates: list[EventCandidate] = []
    for entity_id in sorted(current_objects.keys() - previous_objects.keys()):
        candidates.append(
            EventCandidate(
                event_type="object_appeared",
                entity_id=entity_id,
                previous_state={},
                current_state=current_objects[entity_id],
                severity="medium",
                confidence=float(current_objects[entity_id].get("confidence", 1.0)),
            )
        )
    for entity_id in sorted(previous_objects.keys() - current_objects.keys()):
        candidates.append(
            EventCandidate(
                event_type="object_disappeared",
                entity_id=entity_id,
                previous_state=previous_objects[entity_id],
                current_state={},
                severity="medium",
                confidence=float(previous_objects[entity_id].get("confidence", 1.0)),
            )
        )
    return candidates


def _diff_object_motion(
    previous_objects: dict[str, dict[str, Any]],
    current_objects: dict[str, dict[str, Any]],
    *,
    movement_threshold: float,
) -> list[EventCandidate]:
    candidates: list[EventCandidate] = []
    for entity_id in sorted(previous_objects.keys() & current_objects.keys()):
        previous_position = previous_objects[entity_id].get("position", {})
        current_position = current_objects[entity_id].get("position", {})
        move_distance = _position_distance(previous_position, current_position)
        if move_distance < movement_threshold:
            continue
        candidates.append(
            EventCandidate(
                event_type="object_moved",
                entity_id=entity_id,
                previous_state={**previous_objects[entity_id], "move_distance": move_distance},
                current_state={**current_objects[entity_id], "move_distance": move_distance},
                severity="low" if move_distance < movement_threshold * 2 else "medium",
                confidence=float(current_objects[entity_id].get("confidence", 1.0)),
            )
        )
    return candidates


def _diff_risk_state(
    previous_risks: dict[str, dict[str, Any]],
    current_risks: dict[str, dict[str, Any]],
    *,
    risk_score_delta_threshold: float,
) -> list[EventCandidate]:
    candidates: list[EventCandidate] = []
    for entity_id in sorted(current_risks.keys() - previous_risks.keys()):
        candidates.append(
            EventCandidate(
                event_type="risk_changed",
                entity_id=entity_id,
                previous_state={},
                current_state=current_risks[entity_id],
                severity=str(current_risks[entity_id].get("severity", "medium")),
                confidence=float(current_risks[entity_id].get("confidence", 1.0)),
            )
        )
    for entity_id in sorted(previous_risks.keys() - current_risks.keys()):
        candidates.append(
            EventCandidate(
                event_type="risk_changed",
                entity_id=entity_id,
                previous_state=previous_risks[entity_id],
                current_state={},
                severity="low",
                confidence=float(previous_risks[entity_id].get("confidence", 1.0)),
            )
        )
    for entity_id in sorted(previous_risks.keys() & current_risks.keys()):
        previous_score = float(previous_risks[entity_id].get("risk_score", 0.0) or 0.0)
        current_score = float(current_risks[entity_id].get("risk_score", 0.0) or 0.0)
        score_delta = abs(current_score - previous_score)
        if score_delta < risk_score_delta_threshold:
            continue
        current_severity = str(current_risks[entity_id].get("severity", "medium"))
        candidates.append(
            EventCandidate(
                event_type="risk_changed",
                entity_id=entity_id,
                previous_state={**previous_risks[entity_id], "risk_score_delta": score_delta},
                current_state={**current_risks[entity_id], "risk_score_delta": score_delta},
                severity=current_severity,
                confidence=float(current_risks[entity_id].get("confidence", 1.0)),
            )
        )
    return candidates


def _entity_state(entity: EntityToken) -> dict[str, Any]:
    return {
        "entity_id": entity.entity_id,
        "category": entity.category,
        "position": entity.position.to_dict(),
        "distance_to_agent": entity.distance_to_agent,
        "confidence": entity.confidence,
        "is_visible": entity.is_visible,
    }


def _risk_state(risk: RiskToken) -> dict[str, Any]:
    return {
        "entity_id": risk.entity_id,
        "risk_type": risk.risk_type,
        "severity": risk.severity,
        "risk_score": risk.risk_score,
        "confidence": risk.confidence,
        "affected_area": risk.affected_area,
    }


def _objects(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    objects = state.get("objects", {})
    return objects if isinstance(objects, dict) else {}


def _risks(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    risks = state.get("risks", {})
    return risks if isinstance(risks, dict) else {}


def _position_distance(previous_position: Any, current_position: Any) -> float:
    previous = _position_dict(previous_position)
    current = _position_dict(current_position)
    return sqrt(
        (previous["x"] - current["x"]) ** 2
        + (previous["y"] - current["y"]) ** 2
        + (previous["z"] - current["z"]) ** 2
    )


def _position_dict(value: Any) -> dict[str, float]:
    if isinstance(value, Vector3):
        return value.to_dict()
    if isinstance(value, dict):
        return {
            "x": float(value.get("x", 0.0)),
            "y": float(value.get("y", 0.0)),
            "z": float(value.get("z", 0.0)),
        }
    return {"x": 0.0, "y": 0.0, "z": 0.0}

"""TokenMemory 기반 incremental update 측정 helper입니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from rast.schemas.tokens import EntityToken, EventToken, RiskToken
from rast.token_memory.diff import diff_states


UpdateMode = Literal["full_recompute", "incremental"]
VALID_UPDATE_MODES: tuple[str, ...] = ("full_recompute", "incremental")


@dataclass(frozen=True)
class UpdateStats:
    """한 step에서 incremental update protocol에 기록할 최소 통계입니다."""

    update_mode: UpdateMode
    changed_object_ids: tuple[str, ...]
    changed_object_count: int
    affected_token_count: int


def compute_update_stats(
    *,
    previous_state: dict[str, Any] | None,
    current_state: dict[str, Any],
    entities: list[EntityToken],
    risks: list[RiskToken],
    events: list[EventToken],
    update_mode: UpdateMode,
    movement_threshold: float,
    risk_score_delta_threshold: float,
) -> UpdateStats:
    """full recompute와 incremental mode에서 공통으로 사용할 update 통계를 계산합니다."""

    if update_mode not in VALID_UPDATE_MODES:
        allowed = ", ".join(VALID_UPDATE_MODES)
        raise ValueError(f"지원하지 않는 update_mode입니다: {update_mode}. 허용값: {allowed}")

    changed_ids = changed_object_ids_from_states(
        previous_state,
        current_state,
        movement_threshold=movement_threshold,
        risk_score_delta_threshold=risk_score_delta_threshold,
    )
    if update_mode == "full_recompute":
        affected_token_count = len(entities) + len(risks) + len(events)
    else:
        affected_token_count = affected_token_count_for_changed_objects(
            changed_ids=changed_ids,
            entities=entities,
            risks=risks,
            events=events,
        )
    return UpdateStats(
        update_mode=update_mode,
        changed_object_ids=changed_ids,
        changed_object_count=len(changed_ids),
        affected_token_count=affected_token_count,
    )


def changed_object_ids_from_states(
    previous_state: dict[str, Any] | None,
    current_state: dict[str, Any],
    *,
    movement_threshold: float,
    risk_score_delta_threshold: float,
) -> tuple[str, ...]:
    """이전 state와 현재 state의 semantic diff에서 영향을 받은 object id를 추출합니다."""

    current_objects = _objects(current_state)
    if previous_state is None:
        return tuple(sorted(current_objects.keys()))

    candidates = diff_states(
        previous_state,
        current_state,
        movement_threshold=movement_threshold,
        risk_score_delta_threshold=risk_score_delta_threshold,
    )
    return tuple(sorted({candidate.entity_id for candidate in candidates}))


def affected_token_count_for_changed_objects(
    *,
    changed_ids: tuple[str, ...],
    entities: list[EntityToken],
    risks: list[RiskToken],
    events: list[EventToken],
) -> int:
    """changed object와 직접 연결된 Entity/Risk/Event token 수를 계산합니다."""

    changed = set(changed_ids)
    if not changed:
        return len(events)
    affected_entities = sum(1 for entity in entities if entity.entity_id in changed)
    affected_risks = sum(1 for risk in risks if risk.entity_id in changed)
    affected_events = sum(1 for event in events if event.entity_id in changed)
    return affected_entities + affected_risks + affected_events


def _objects(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    objects = state.get("objects", {})
    return objects if isinstance(objects, dict) else {}

"""Object List baseline의 최소 deterministic planner입니다."""

from __future__ import annotations

from dataclasses import dataclass

from rast.baselines.object_list import ObjectListItem
from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision


@dataclass(frozen=True)
class ObjectListPlannerConfig:
    """Object List baseline planner threshold를 주입하기 위한 설정입니다."""

    near_object_threshold: float


def plan_from_object_list(
    objects: list[ObjectListItem],
    *,
    config: ObjectListPlannerConfig,
) -> PlannerDecision:
    """RiskToken 없이 object distance만 보고 action과 선택 근거를 반환합니다."""

    if config.near_object_threshold <= 0:
        raise ValueError("near_object_threshold는 0보다 커야 합니다.")

    nearest = min(objects, key=lambda item: item.distance_to_agent, default=None)
    if nearest is not None and nearest.distance_to_agent <= config.near_object_threshold:
        return PlannerDecision(
            planner_name="object_list",
            action=Action.ROTATE_RIGHT,
            reason_code="near_object_distance",
            reason_text="Object is within near-object threshold.",
            trigger_object_ids=[nearest.object_id],
            trigger_token_ids=[],
            trigger_features={
                "distance_to_agent": nearest.distance_to_agent,
                "threshold": config.near_object_threshold,
                "category": nearest.category,
            },
            confidence=nearest.confidence,
        )

    return PlannerDecision(
        planner_name="object_list",
        action=Action.MOVE_AHEAD,
        reason_code="no_near_object_move_ahead",
        reason_text="No object is within near-object threshold.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={
            "nearest_distance_to_agent": nearest.distance_to_agent if nearest is not None else None,
            "threshold": config.near_object_threshold,
        },
        confidence=1.0,
    )

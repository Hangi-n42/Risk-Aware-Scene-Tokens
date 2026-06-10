"""MVP-0 공통 action contract입니다."""

from __future__ import annotations

from enum import Enum
from typing import Any


class Action(str, Enum):
    """AI2-THOR discrete action 이름과 맞출 수 있는 최소 action set입니다."""

    MOVE_AHEAD = "MoveAhead"
    ROTATE_LEFT = "RotateLeft"
    ROTATE_RIGHT = "RotateRight"
    STOP = "Stop"


ACTIONS: tuple[Action, ...] = (
    Action.MOVE_AHEAD,
    Action.ROTATE_LEFT,
    Action.ROTATE_RIGHT,
    Action.STOP,
)


def action_value(action_or_decision: Any) -> str:
    """Action 또는 PlannerDecision에서 simulator에 보낼 action 문자열을 꺼냅니다."""

    if isinstance(action_or_decision, Action):
        return action_or_decision.value
    action = getattr(action_or_decision, "action", None)
    if isinstance(action, Action):
        return action.value
    value = getattr(action_or_decision, "value", None)
    if isinstance(value, str):
        return value
    if isinstance(action_or_decision, str):
        return action_or_decision
    raise TypeError(f"Action으로 해석할 수 없는 값입니다: {type(action_or_decision)!r}")

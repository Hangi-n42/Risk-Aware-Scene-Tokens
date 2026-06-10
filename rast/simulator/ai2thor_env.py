"""AI2-THOR Controller를 선택적으로 사용하는 얇은 wrapper입니다.

이 파일만 AI2-THOR import를 소유합니다. 다른 RAST 모듈은 simulator가
설치되지 않은 환경에서도 import가 깨지지 않아야 합니다.
"""

from __future__ import annotations

from typing import Any

from rast.planner.actions import Action


class AI2THORNotAvailableError(RuntimeError):
    """AI2-THOR optional dependency가 없는 경우의 명확한 오류입니다."""


class AI2THOREnvironmentError(RuntimeError):
    """Controller 생성 또는 step 실행 중 렌더링/환경 문제가 난 경우의 오류입니다."""


ACTION_MAP: dict[Action, str] = {
    Action.MOVE_AHEAD: "MoveAhead",
    Action.ROTATE_LEFT: "RotateLeft",
    Action.ROTATE_RIGHT: "RotateRight",
    # AI2-THOR에는 일반적으로 Stop action이 없으므로 task 종료 의미의 Done으로 매핑합니다.
    Action.STOP: "Done",
}


def create_controller(*, scene: str = "FloorPlan1", cloud_rendering: bool = False, **controller_kwargs: Any) -> Any:
    """AI2-THOR Controller를 생성합니다.

    설치/렌더링 문제는 연구자가 바로 원인을 추적할 수 있도록 별도 메시지로 감쌉니다.
    """

    controller_cls = _load_controller_class()
    if cloud_rendering:
        controller_kwargs.setdefault("platform", _load_cloud_rendering())
    try:
        return controller_cls(scene=scene, **controller_kwargs)
    except Exception as exc:  # pragma: no cover - 실제 simulator 환경에서만 검증합니다.
        raise AI2THOREnvironmentError(
            "AI2-THOR Controller 생성에 실패했습니다. ai2thor 설치 여부, Unity 렌더링 환경, "
            f"headless/WSL2/GPU 설정, scene 이름을 확인하십시오. 원본 오류: {type(exc).__name__}: {exc}"
        ) from exc


def reset_scene(controller: Any, *, scene: str) -> Any:
    """지정한 scene으로 reset하고 AI2-THOR event를 반환합니다."""

    try:
        return controller.reset(scene=scene)
    except Exception as exc:  # pragma: no cover - 실제 simulator 환경에서만 검증합니다.
        raise AI2THOREnvironmentError(f"AI2-THOR scene reset에 실패했습니다: scene={scene}") from exc


def step_action(controller: Any, action: Action | str) -> Any:
    """공통 Action contract를 AI2-THOR action으로 변환해 한 step 실행합니다."""

    simulator_action = to_ai2thor_action(action)
    try:
        return controller.step(action=simulator_action)
    except Exception as exc:  # pragma: no cover - 실제 simulator 환경에서만 검증합니다.
        raise AI2THOREnvironmentError(f"AI2-THOR action 실행에 실패했습니다: action={simulator_action}") from exc


def to_ai2thor_action(action: Action | str) -> str:
    """RAST 공통 action을 AI2-THOR action 문자열로 변환합니다."""

    if isinstance(action, Action):
        return ACTION_MAP[action]
    if action == Action.STOP.value:
        return ACTION_MAP[Action.STOP]
    if action in {item.value for item in Action}:
        return action
    raise ValueError(f"지원하지 않는 RAST action입니다: {action}")


def _load_controller_class() -> Any:
    """AI2-THOR Controller를 lazy import합니다."""

    try:
        from ai2thor.controller import Controller  # type: ignore
    except ImportError as exc:  # pragma: no cover - 설치 여부에 따라 달라집니다.
        raise AI2THORNotAvailableError(
            "AI2-THOR가 설치되어 있지 않습니다. simulator smoke를 실행하려면 "
            "`python -m pip install -e .[sim]` 또는 공식 문서의 설치 절차를 확인하십시오."
        ) from exc
    return Controller


def _load_cloud_rendering() -> Any:
    """AI2-THOR CloudRendering platform을 lazy import합니다."""

    try:
        from ai2thor.platform import CloudRendering  # type: ignore
    except ImportError as exc:  # pragma: no cover - 설치 여부에 따라 달라집니다.
        raise AI2THORNotAvailableError(
            "AI2-THOR CloudRendering platform을 import할 수 없습니다. ai2thor 설치 상태와 버전을 확인하십시오."
        ) from exc
    return CloudRendering

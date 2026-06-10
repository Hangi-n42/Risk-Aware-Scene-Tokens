"""Windows native 환경에서 MVP-0 contract를 검증하기 위한 metadata-only simulator입니다.

3D rendering이나 physics를 구현하지 않습니다. 목적은 deterministic metadata를
`ObservationSnapshot`으로 변환한 뒤 기존 tokenizer/planner/logger 흐름을 유지하는 것입니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, radians, sin, sqrt
from typing import Any

from rast.planner.actions import Action
from rast.schemas.common import Vector3
from rast.schemas.observation import ObservationSnapshot
from rast.simulator.observation_adapter import metadata_to_observation_snapshot


@dataclass(frozen=True)
class SimObject:
    """metadata simulator가 노출하는 최소 object 정의입니다."""

    object_id: str
    object_type: str
    position: Vector3
    size: Vector3
    bbox_2d: dict[str, float] | None = None


@dataclass
class AgentPose:
    """Agent의 위치와 yaw 회전을 관리합니다."""

    position: Vector3
    yaw_degrees: float = 0.0
    horizon: float = 0.0


@dataclass(frozen=True)
class WindowsMetadataSimConfig:
    """threshold와 step 크기를 코드 본문 magic number로 고정하지 않기 위한 설정입니다."""

    scene_id: str = "WindowsRoom1"
    move_step: float = 0.25
    rotation_step_degrees: float = 90.0
    visible_distance: float = 5.0
    room_min_x: float = -3.0
    room_max_x: float = 3.0
    room_min_z: float = -3.0
    room_max_z: float = 3.0


@dataclass
class WindowsMetadataSim:
    """AI2-THOR 없이 metadata-like dict를 생성하는 deterministic simulator입니다."""

    config: WindowsMetadataSimConfig = field(default_factory=WindowsMetadataSimConfig)
    agent: AgentPose = field(
        default_factory=lambda: AgentPose(position=Vector3(x=0.0, y=0.0, z=0.0), yaw_degrees=0.0)
    )
    objects: list[SimObject] = field(default_factory=list)
    object_schedule: dict[int, list[SimObject]] = field(default_factory=dict)
    step_index: int = 0
    last_action: str | None = None
    _initial_agent: AgentPose = field(init=False, repr=False)
    _initial_objects: list[SimObject] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._initial_agent = _copy_agent(self.agent)
        if not self.objects:
            self.objects = default_objects()
        self._initial_objects = _copy_objects(self.objects)

    @classmethod
    def from_config_dict(cls, data: dict[str, Any]) -> "WindowsMetadataSim":
        """YAML 등에서 읽은 dict로 simulator를 구성합니다."""

        config = WindowsMetadataSimConfig(
            scene_id=str(data.get("scene_id", "WindowsRoom1")),
            move_step=float(data.get("move_step", 0.25)),
            rotation_step_degrees=float(data.get("rotation_step_degrees", 90.0)),
            visible_distance=float(data.get("visible_distance", 5.0)),
        )
        pose_data = data.get("initial_agent_pose", {})
        position_data = pose_data.get("position", {}) if isinstance(pose_data, dict) else {}
        agent = AgentPose(
            position=Vector3(
                x=float(position_data.get("x", 0.0)),
                y=float(position_data.get("y", 0.0)),
                z=float(position_data.get("z", 0.0)),
            ),
            yaw_degrees=float(pose_data.get("yaw_degrees", 0.0)) if isinstance(pose_data, dict) else 0.0,
            horizon=float(pose_data.get("horizon", 0.0)) if isinstance(pose_data, dict) else 0.0,
        )
        raw_objects = data.get("objects")
        objects = [_object_from_dict(item) for item in raw_objects] if isinstance(raw_objects, list) else default_objects()
        return cls(config=config, agent=agent, objects=objects)

    def reset(self) -> dict[str, Any]:
        """step을 0으로 되돌리고 현재 metadata를 반환합니다."""

        self.step_index = 0
        self.last_action = None
        self.agent = _copy_agent(self._initial_agent)
        self.objects = _copy_objects(self._initial_objects)
        return self.metadata()

    def step(self, action: Action | str) -> dict[str, Any]:
        """공통 action contract를 적용하고 다음 metadata를 반환합니다."""

        action_value = _normalize_action(action)
        self.last_action = action_value
        if action_value == Action.MOVE_AHEAD.value:
            self._move_ahead()
        elif action_value == Action.ROTATE_LEFT.value:
            self.agent.yaw_degrees = (self.agent.yaw_degrees - self.config.rotation_step_degrees) % 360.0
        elif action_value == Action.ROTATE_RIGHT.value:
            self.agent.yaw_degrees = (self.agent.yaw_degrees + self.config.rotation_step_degrees) % 360.0
        elif action_value == Action.STOP.value:
            pass
        else:
            raise ValueError(f"지원하지 않는 action입니다: {action_value}")
        self.step_index += 1
        self._apply_object_schedule()
        return self.metadata()

    def metadata(self) -> dict[str, Any]:
        """AI2-THOR event.metadata와 유사한 최소 dict를 반환합니다."""

        return {
            "sceneName": self.config.scene_id,
            "step": self.step_index,
            "lastAction": self.last_action,
            "agent": {
                "position": self.agent.position.to_dict(),
                "rotation": {"x": 0.0, "y": self.agent.yaw_degrees, "z": 0.0},
                "cameraHorizon": self.agent.horizon,
            },
            "objects": [self._object_metadata(obj) for obj in self.objects],
        }

    def snapshot(self, *, episode_id: str | None = None) -> ObservationSnapshot:
        """현재 metadata를 기존 adapter로 변환한 ObservationSnapshot입니다."""

        return metadata_to_observation_snapshot(
            self.metadata(),
            episode_id=episode_id,
            source="windows_metadata_sim",
        )

    def _move_ahead(self) -> None:
        yaw = radians(self.agent.yaw_degrees)
        next_x = self.agent.position.x + sin(yaw) * self.config.move_step
        next_z = self.agent.position.z + cos(yaw) * self.config.move_step
        self.agent.position = Vector3(
            x=_clamp(next_x, self.config.room_min_x, self.config.room_max_x),
            y=self.agent.position.y,
            z=_clamp(next_z, self.config.room_min_z, self.config.room_max_z),
        )

    def _object_metadata(self, obj: SimObject) -> dict[str, Any]:
        distance = vector_distance(self.agent.position, obj.position)
        return {
            "objectId": obj.object_id,
            "objectType": obj.object_type,
            "position": obj.position.to_dict(),
            "size": obj.size.to_dict(),
            "visible": distance <= self.config.visible_distance,
            "distance": distance,
            "bbox2D": obj.bbox_2d,
        }

    def _apply_object_schedule(self) -> None:
        """step index 기반 scripted object 변화를 metadata에만 반영합니다."""

        if self.step_index not in self.object_schedule:
            return
        self.objects = _copy_objects(self.object_schedule[self.step_index])


def default_objects() -> list[SimObject]:
    """MVP-0 검증용 기본 room object set입니다."""

    return [
        SimObject(
            object_id="Chair|windows|near|+00.00|+00.00|+00.80",
            object_type="Chair",
            position=Vector3(x=0.0, y=0.0, z=0.8),
            size=Vector3(x=0.6, y=0.9, z=0.6),
            bbox_2d={"x": 32.0, "y": 80.0, "width": 72.0, "height": 120.0},
        ),
        SimObject(
            object_id="Sofa|windows|far|+02.40|+00.00|+02.60",
            object_type="Sofa",
            position=Vector3(x=2.4, y=0.0, z=2.6),
            size=Vector3(x=1.8, y=0.8, z=0.9),
            bbox_2d={"x": 180.0, "y": 90.0, "width": 160.0, "height": 90.0},
        ),
        SimObject(
            object_id="Mug|windows|target|+01.20|+00.90|+01.30",
            object_type="Mug",
            position=Vector3(x=1.2, y=0.9, z=1.3),
            size=Vector3(x=0.12, y=0.12, z=0.12),
            bbox_2d={"x": 300.0, "y": 140.0, "width": 36.0, "height": 44.0},
        ),
        SimObject(
            object_id="UnknownObject|windows|+00.90|+00.00|-00.60",
            object_type="UnknownObject",
            position=Vector3(x=0.9, y=0.0, z=-0.6),
            size=Vector3(x=0.5, y=0.5, z=0.5),
            bbox_2d={"x": 110.0, "y": 110.0, "width": 64.0, "height": 72.0},
        ),
    ]


def vector_distance(first: Vector3, second: Vector3) -> float:
    """두 3D 좌표 사이의 Euclidean distance입니다."""

    return sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2 + (first.z - second.z) ** 2)


def _object_from_dict(data: dict[str, Any]) -> SimObject:
    return SimObject(
        object_id=str(data["object_id"]),
        object_type=str(data["object_type"]),
        position=_vector_from_config(data["position"]),
        size=_vector_from_config(data.get("size", {"x": 0.5, "y": 0.5, "z": 0.5})),
        bbox_2d=data.get("bbox_2d"),
    )


def _vector_from_config(data: dict[str, Any]) -> Vector3:
    return Vector3(x=float(data["x"]), y=float(data["y"]), z=float(data["z"]))


def _normalize_action(action: Action | str) -> str:
    if isinstance(action, Action):
        return action.value
    if action not in {item.value for item in Action}:
        raise ValueError(f"지원하지 않는 action입니다: {action}")
    return action


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


def _copy_agent(agent: AgentPose) -> AgentPose:
    return AgentPose(
        position=Vector3(x=agent.position.x, y=agent.position.y, z=agent.position.z),
        yaw_degrees=agent.yaw_degrees,
        horizon=agent.horizon,
    )


def _copy_object(obj: SimObject) -> SimObject:
    return SimObject(
        object_id=obj.object_id,
        object_type=obj.object_type,
        position=Vector3(x=obj.position.x, y=obj.position.y, z=obj.position.z),
        size=Vector3(x=obj.size.x, y=obj.size.y, z=obj.size.z),
        bbox_2d=dict(obj.bbox_2d) if obj.bbox_2d is not None else None,
    )


def _copy_objects(objects: list[SimObject]) -> list[SimObject]:
    return [_copy_object(item) for item in objects]

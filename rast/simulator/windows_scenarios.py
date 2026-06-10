"""WindowsMetadataSim controlled scenario suite입니다.

이 suite는 RAST가 더 좋다는 결론을 만들기 위한 것이 아니라, planner contract와
metric harness가 서로 다른 상황을 구분해 기록하는지 검증하기 위한 deterministic 입력입니다.
"""

from __future__ import annotations

from dataclasses import dataclass

from rast.schemas.common import Vector3
from rast.schemas.metrics import GoalSpec
from rast.simulator.windows_metadata_sim import AgentPose, SimObject, WindowsMetadataSim, WindowsMetadataSimConfig


@dataclass(frozen=True)
class WindowsScenarioSpec:
    """scenario별 simulator와 evaluation parameter 묶음입니다."""

    name: str
    description: str
    simulator: WindowsMetadataSim
    risk_threshold: float
    object_list_threshold: float
    collision_threshold: float
    near_miss_threshold: float
    max_steps: int
    apply_policy: str = "rast"
    goal: GoalSpec | None = None


def available_scenarios() -> tuple[str, ...]:
    """CLI와 테스트에서 사용할 수 있는 scenario 이름입니다."""

    return (
        "clear_path",
        "near_obstacle",
        "far_obstacle",
        "unknown_near_path",
        "target_reachable",
        "planner_disagreement",
        "object_appears",
        "object_disappears",
        "object_moves",
        "risk_increases",
    )


def build_windows_scenario(name: str) -> WindowsScenarioSpec:
    """scenario 이름으로 deterministic WindowsMetadataSim 입력을 생성합니다."""

    if name == "clear_path":
        return WindowsScenarioSpec(
            name=name,
            description="agent 전방 risk threshold 안에 object가 없는 diagnostic scenario입니다.",
            simulator=_sim(
                name,
                objects=[
                    _object("Sofa|clear|far", "Sofa", x=2.4, z=2.6),
                    _object("Mug|clear|side", "Mug", x=-2.0, y=0.9, z=2.5, size=0.12),
                ],
            ),
            risk_threshold=1.0,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=0.8,
            max_steps=10,
        )

    if name == "near_obstacle":
        return WindowsScenarioSpec(
            name=name,
            description="agent 근처 obstacle이 RiskToken과 회피 action을 유도하는 scenario입니다.",
            simulator=_sim(name, objects=[_object("Chair|near|front", "Chair", x=0.0, z=0.8)]),
            risk_threshold=1.5,
            object_list_threshold=1.5,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=10,
        )

    if name == "far_obstacle":
        return WindowsScenarioSpec(
            name=name,
            description="object가 있으나 risk threshold 밖에 있는 scenario입니다.",
            simulator=_sim(name, objects=[_object("Chair|far|front", "Chair", x=0.0, z=2.5)]),
            risk_threshold=1.0,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=0.8,
            max_steps=10,
        )

    if name == "unknown_near_path":
        return WindowsScenarioSpec(
            name=name,
            description="UnknownObject가 near path에 있어 RiskToken 생성을 확인하는 scenario입니다.",
            simulator=_sim(name, objects=[_object("UnknownObject|near_path", "UnknownObject", x=0.0, z=0.9)]),
            risk_threshold=1.5,
            object_list_threshold=1.5,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=10,
        )

    if name == "target_reachable":
        return WindowsScenarioSpec(
            name=name,
            description="goal position 도달 여부로 success를 계산하는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[
                    _object("Sofa|target_reachable|far", "Sofa", x=2.5, z=2.5),
                ],
            ),
            risk_threshold=0.4,
            object_list_threshold=0.4,
            collision_threshold=0.1,
            near_miss_threshold=0.4,
            max_steps=20,
            goal=GoalSpec(
                goal_type="reach_position",
                target_position=Vector3(x=0.0, y=0.0, z=1.0),
                success_distance=0.3,
            ),
        )

    if name == "planner_disagreement":
        return WindowsScenarioSpec(
            name=name,
            description="RAST risk threshold와 Object List threshold가 달라 planner action이 갈라지는 scenario입니다.",
            simulator=_sim(name, objects=[_object("UnknownObject|disagreement|front", "UnknownObject", x=0.0, z=1.2)]),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=10,
        )

    if name == "object_appears":
        far_sofa = _object("Sofa|object_appears|far", "Sofa", x=2.4, z=2.6)
        appearing_box = _object("Box|object_appears|front", "Box", x=0.0, z=1.2)
        return WindowsScenarioSpec(
            name=name,
            description="step 1부터 새 object가 metadata에 등장해 object_appeared EventToken을 검증하는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[far_sofa],
                object_schedule={
                    1: [far_sofa, appearing_box],
                    2: [far_sofa, appearing_box],
                    3: [far_sofa, appearing_box],
                    4: [far_sofa, appearing_box],
                },
            ),
            risk_threshold=1.5,
            object_list_threshold=1.5,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "object_disappears":
        far_sofa = _object("Sofa|object_disappears|far", "Sofa", x=2.4, z=2.6)
        disappearing_box = _object("Box|object_disappears|front", "Box", x=0.0, z=1.2)
        return WindowsScenarioSpec(
            name=name,
            description="step 0에는 object가 있고 step 1부터 사라져 object_disappeared EventToken을 검증하는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[far_sofa, disappearing_box],
                object_schedule={
                    1: [far_sofa],
                    2: [far_sofa],
                    3: [far_sofa],
                    4: [far_sofa],
                },
            ),
            risk_threshold=1.5,
            object_list_threshold=1.5,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "object_moves":
        base_sofa = _object("Sofa|object_moves|far", "Sofa", x=2.5, z=2.6)
        moving_box_0 = _object("Box|object_moves|front", "Box", x=0.8, z=2.0)
        moving_box_1 = _object("Box|object_moves|front", "Box", x=0.6, z=1.8)
        moving_box_2 = _object("Box|object_moves|front", "Box", x=0.4, z=1.6)
        moving_box_3 = _object("Box|object_moves|front", "Box", x=0.2, z=1.4)
        return WindowsScenarioSpec(
            name=name,
            description="동일 object id의 position이 step마다 변해 object_moved EventToken을 검증하는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[base_sofa, moving_box_0],
                object_schedule={
                    1: [base_sofa, moving_box_1],
                    2: [base_sofa, moving_box_2],
                    3: [base_sofa, moving_box_3],
                    4: [base_sofa, moving_box_3],
                },
            ),
            risk_threshold=0.8,
            object_list_threshold=0.8,
            collision_threshold=0.2,
            near_miss_threshold=0.9,
            max_steps=5,
        )

    if name == "risk_increases":
        far_sofa = _object("Sofa|risk_increases|far", "Sofa", x=2.4, z=2.6)
        moving_unknown_0 = _object("UnknownObject|risk_increases|front", "UnknownObject", x=0.0, z=2.1)
        moving_unknown_1 = _object("UnknownObject|risk_increases|front", "UnknownObject", x=0.0, z=1.2)
        return WindowsScenarioSpec(
            name=name,
            description="object가 risk threshold 안으로 들어와 risk_changed EventToken을 검증하는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[far_sofa, moving_unknown_0],
                object_schedule={
                    1: [far_sofa, moving_unknown_1],
                    2: [far_sofa, moving_unknown_1],
                    3: [far_sofa, moving_unknown_1],
                    4: [far_sofa, moving_unknown_1],
                },
            ),
            risk_threshold=1.5,
            object_list_threshold=1.5,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    allowed = ", ".join(available_scenarios())
    raise ValueError(f"지원하지 않는 WindowsMetadataSim scenario입니다: {name}. 허용값: {allowed}")


def _sim(
    name: str,
    *,
    objects: list[SimObject],
    object_schedule: dict[int, list[SimObject]] | None = None,
) -> WindowsMetadataSim:
    return WindowsMetadataSim(
        config=WindowsMetadataSimConfig(scene_id=f"WindowsRoom_{name}"),
        agent=AgentPose(position=Vector3(x=0.0, y=0.0, z=0.0), yaw_degrees=0.0),
        objects=objects,
        object_schedule=object_schedule or {},
    )


def _object(
    object_id: str,
    object_type: str,
    *,
    x: float,
    z: float,
    y: float = 0.0,
    size: float = 0.5,
) -> SimObject:
    return SimObject(
        object_id=object_id,
        object_type=object_type,
        position=Vector3(x=x, y=y, z=z),
        size=Vector3(x=size, y=size, z=size),
    )

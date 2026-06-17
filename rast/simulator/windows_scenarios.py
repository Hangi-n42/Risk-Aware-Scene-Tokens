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
    near_agent_relation_threshold: float | None = None
    near_path_relation_threshold: float | None = None
    blocking_relation_threshold: float | None = None

    @property
    def resolved_near_agent_relation_threshold(self) -> float:
        """scenario가 별도 값을 주지 않으면 기존 risk threshold를 relation 기본값으로 씁니다."""

        return self.near_agent_relation_threshold if self.near_agent_relation_threshold is not None else self.risk_threshold

    @property
    def resolved_near_path_relation_threshold(self) -> float:
        """전방 path proxy의 lateral threshold 기본값입니다."""

        return self.near_path_relation_threshold if self.near_path_relation_threshold is not None else 0.5

    @property
    def resolved_blocking_relation_threshold(self) -> float:
        """blocking_path relation의 distance threshold 기본값입니다."""

        return self.blocking_relation_threshold if self.blocking_relation_threshold is not None else self.risk_threshold


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
        "relation_near_but_low_risk",
        "blocking_relation_without_high_risk",
        "risk_without_graph_blocking",
        "event_changes_risk_but_graph_static",
        "unknown_uncertain_object",
        "partially_occluded_obstacle",
        "noisy_position_boundary",
        "low_sensor_agreement",
        "uncertainty_without_high_risk",
        "uncertainty_near_path",
        "narrow_passage",
        "passable_clear_gap",
        "inspect_required_uncertain_path",
        "avoid_required_blocking_path",
        "target_reachable_affordance",
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

    if name == "relation_near_but_low_risk":
        return WindowsScenarioSpec(
            name=name,
            description=(
                "object는 agent 근처 relation threshold 안에 있지만 risk threshold 밖에 있어 "
                "Scene Graph near_agent와 RAST no-risk decision 차이를 관찰하는 scenario입니다."
            ),
            simulator=_sim(
                name,
                objects=[
                    _object("Chair|relation_near_low_risk|side", "Chair", x=1.65, z=0.30),
                    _object("Mug|relation_near_low_risk|far", "Mug", x=-2.0, y=0.9, z=2.5, size=0.12),
                ],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
            near_agent_relation_threshold=2.0,
            near_path_relation_threshold=0.5,
            blocking_relation_threshold=1.5,
        )

    if name == "blocking_relation_without_high_risk":
        return WindowsScenarioSpec(
            name=name,
            description=(
                "blocking_path relation은 생성되지만 거리 기반 RiskToken severity는 high가 아닌 "
                "same-action-different-reason 관찰 scenario입니다."
            ),
            simulator=_sim(name, objects=[_object("Box|blocking_low_risk|front", "Box", x=0.0, z=1.4)]),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
            near_agent_relation_threshold=1.0,
            near_path_relation_threshold=0.5,
            blocking_relation_threshold=1.5,
        )

    if name == "risk_without_graph_blocking":
        return WindowsScenarioSpec(
            name=name,
            description=(
                "RiskToken은 생성되지만 relation threshold상 near_agent/blocking_path edge가 없어 "
                "RAST와 Scene Graph action 차이를 관찰하는 scenario입니다."
            ),
            simulator=_sim(
                name,
                objects=[_object("UnknownObject|risk_no_graph_blocking|offset", "UnknownObject", x=0.45, z=0.70)],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
            near_agent_relation_threshold=0.5,
            near_path_relation_threshold=0.35,
            blocking_relation_threshold=0.5,
        )

    if name == "event_changes_risk_but_graph_static":
        far_sofa = _object("Sofa|event_graph_static|far", "Sofa", x=2.4, z=2.6)
        moving_unknown_0 = _object("UnknownObject|event_graph_static|offset", "UnknownObject", x=0.45, z=2.0)
        moving_unknown_1 = _object("UnknownObject|event_graph_static|offset", "UnknownObject", x=0.45, z=1.0)
        return WindowsScenarioSpec(
            name=name,
            description=(
                "near_path relation 구조는 유지되지만 risk_changed EventToken이 발생해 "
                "Event-aware RAST와 Scene Graph decision basis 차이를 관찰하는 scenario입니다."
            ),
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
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
            near_agent_relation_threshold=0.5,
            near_path_relation_threshold=0.5,
            blocking_relation_threshold=0.5,
        )

    if name == "unknown_uncertain_object":
        return WindowsScenarioSpec(
            name=name,
            description="UnknownObject 계열 object가 높은 classification uncertainty를 갖는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[
                    _object(
                        "UnknownObject|uncertain|classification",
                        "UnknownObject",
                        x=0.9,
                        z=1.7,
                        classification_confidence=0.35,
                        classification_uncertainty=0.75,
                        possible_categories=["Bag", "Box", "UnknownObject"],
                        is_unknown=True,
                    )
                ],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "partially_occluded_obstacle":
        return WindowsScenarioSpec(
            name=name,
            description="path 근처 obstacle의 occlusion_ratio가 높아 partial_occlusion UncertaintyToken을 검증하는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[
                    _object(
                        "Chair|occluded|front",
                        "Chair",
                        x=0.2,
                        z=1.3,
                        occlusion_ratio=0.72,
                        possible_categories=["Chair", "Box"],
                    )
                ],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "noisy_position_boundary":
        return WindowsScenarioSpec(
            name=name,
            description="risk threshold 경계 근처 object의 position variance가 높은 scenario입니다.",
            simulator=_sim(
                name,
                objects=[
                    _object(
                        "Box|position_uncertain|boundary",
                        "Box",
                        x=0.05,
                        z=1.55,
                        position_variance=0.35,
                    )
                ],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "low_sensor_agreement":
        return WindowsScenarioSpec(
            name=name,
            description="sensor_agreement가 낮은 object를 통해 low_sensor_agreement UncertaintyToken을 검증하는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[
                    _object(
                        "Box|low_sensor_agreement|front",
                        "Box",
                        x=0.4,
                        z=1.4,
                        sensor_agreement=0.45,
                    )
                ],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "uncertainty_without_high_risk":
        return WindowsScenarioSpec(
            name=name,
            description=(
                "RiskToken은 없거나 high가 아니지만 path 근처 uncertainty가 높아 "
                "uncertainty-aware planner와 기본 RAST decision 차이를 관찰하는 scenario입니다."
            ),
            simulator=_sim(
                name,
                objects=[
                    _object(
                        "Box|uncertain_no_high_risk|front",
                        "Box",
                        x=0.0,
                        z=1.8,
                        classification_uncertainty=0.72,
                        position_variance=0.28,
                        possible_categories=["Box", "Bag"],
                    )
                ],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "uncertainty_near_path":
        return WindowsScenarioSpec(
            name=name,
            description="path 근처 높은 uncertainty object와 RiskToken이 함께 발생할 수 있는 scenario입니다.",
            simulator=_sim(
                name,
                objects=[
                    _object(
                        "UnknownObject|uncertain_near_path|front",
                        "UnknownObject",
                        x=0.05,
                        z=1.1,
                        classification_confidence=0.3,
                        classification_uncertainty=0.8,
                        occlusion_ratio=0.55,
                        sensor_agreement=0.5,
                        possible_categories=["UnknownObject", "Bag", "Box"],
                        is_unknown=True,
                    )
                ],
            ),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "narrow_passage":
        return WindowsScenarioSpec(
            name=name,
            description="agent forward path?? 좁은 passage margin??AffordanceToken?쇰줈 湲곕줉?섎뒗 scenario?낅땲??",
            simulator=_sim(
                name,
                objects=[
                    _object("Chair|narrow_passage|left", "Chair", x=-0.42, z=1.0),
                    _object("Chair|narrow_passage|right", "Chair", x=0.42, z=1.0),
                    _object("Sofa|narrow_passage|far", "Sofa", x=2.4, z=2.6),
                ],
            ),
            risk_threshold=0.6,
            object_list_threshold=0.8,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
            near_agent_relation_threshold=0.6,
            near_path_relation_threshold=0.5,
            blocking_relation_threshold=0.6,
        )

    if name == "passable_clear_gap":
        return WindowsScenarioSpec(
            name=name,
            description="side obstacle 사이에 충분한 gap이 있어 passable affordance를 검증하는 scenario?낅땲??",
            simulator=_sim(
                name,
                objects=[
                    _object("Chair|passable_gap|left", "Chair", x=-0.85, z=1.1),
                    _object("Chair|passable_gap|right", "Chair", x=0.85, z=1.1),
                    _object("Mug|passable_gap|far", "Mug", x=2.0, y=0.9, z=2.2, size=0.12),
                ],
            ),
            risk_threshold=0.6,
            object_list_threshold=0.8,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
            near_agent_relation_threshold=0.6,
            near_path_relation_threshold=0.5,
            blocking_relation_threshold=0.6,
        )

    if name == "inspect_required_uncertain_path":
        return WindowsScenarioSpec(
            name=name,
            description="path 근처 high uncertainty object로 inspect_required affordance를 검증하는 scenario?낅땲??",
            simulator=_sim(
                name,
                objects=[
                    _object(
                        "Box|inspect_required|uncertain_path",
                        "Box",
                        x=0.15,
                        z=1.4,
                        classification_uncertainty=0.76,
                        occlusion_ratio=0.62,
                        possible_categories=["Box", "Bag"],
                    )
                ],
            ),
            risk_threshold=1.0,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
        )

    if name == "avoid_required_blocking_path":
        return WindowsScenarioSpec(
            name=name,
            description="blocking_path object가 avoid_required/blocking affordance로 표현되는 scenario?낅땲??",
            simulator=_sim(name, objects=[_object("Box|avoid_required|front", "Box", x=0.0, z=0.9)]),
            risk_threshold=1.5,
            object_list_threshold=1.0,
            collision_threshold=0.2,
            near_miss_threshold=1.0,
            max_steps=5,
            near_agent_relation_threshold=1.0,
            near_path_relation_threshold=0.5,
            blocking_relation_threshold=1.5,
        )

    if name == "target_reachable_affordance":
        return WindowsScenarioSpec(
            name=name,
            description="goal이 agent forward path에 있어 target_reachable affordance를 검증하는 scenario?낅땲??",
            simulator=_sim(
                name,
                objects=[_object("Sofa|target_reachable_affordance|far", "Sofa", x=2.5, z=2.5)],
            ),
            risk_threshold=0.4,
            object_list_threshold=0.4,
            collision_threshold=0.1,
            near_miss_threshold=0.4,
            max_steps=10,
            goal=GoalSpec(
                goal_type="reach_position",
                target_position=Vector3(x=0.0, y=0.0, z=1.0),
                success_distance=0.3,
            ),
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
    classification_confidence: float = 1.0,
    classification_uncertainty: float = 0.0,
    position_variance: float = 0.0,
    occlusion_ratio: float = 0.0,
    sensor_agreement: float = 1.0,
    possible_categories: list[str] | None = None,
    is_unknown: bool | None = None,
) -> SimObject:
    return SimObject(
        object_id=object_id,
        object_type=object_type,
        position=Vector3(x=x, y=y, z=z),
        size=Vector3(x=size, y=size, z=size),
        classification_confidence=classification_confidence,
        classification_uncertainty=classification_uncertainty,
        position_variance=position_variance,
        occlusion_ratio=occlusion_ratio,
        sensor_agreement=sensor_agreement,
        possible_categories=possible_categories or [],
        is_unknown=is_unknown,
    )

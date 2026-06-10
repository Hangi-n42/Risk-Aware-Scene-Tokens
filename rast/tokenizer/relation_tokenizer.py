"""ObservationSnapshot에서 navigation RelationToken을 생성합니다."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin, sqrt

from rast.schemas.common import Vector3
from rast.schemas.metrics import GoalSpec
from rast.schemas.observation import ObservationSnapshot
from rast.schemas.tokens import EntityToken, RelationToken


AGENT_NODE_ID = "agent"
DEFAULT_PATH_SEGMENT_ID = "agent_forward_path_proxy"


@dataclass(frozen=True)
class RelationTokenizerConfig:
    """RelationToken 생성 threshold를 외부 config에서 주입하기 위한 설정입니다."""

    near_agent_threshold: float = 1.0
    near_path_lateral_threshold: float = 0.5
    blocking_path_lateral_threshold: float = 0.35
    blocking_path_distance_threshold: float = 1.5
    path_lookahead: float = 2.0
    target_reachable_distance: float = 1.5
    path_segment_id: str = DEFAULT_PATH_SEGMENT_ID


@dataclass(frozen=True)
class PathProxyFeatures:
    """Agent yaw 기준 전방 path proxy에 대한 object 위치 feature입니다."""

    projection: float
    lateral_distance: float
    distance_to_agent: float
    is_ahead: bool
    within_lookahead: bool


def build_relation_tokens(
    snapshot: ObservationSnapshot,
    entities: list[EntityToken],
    *,
    config: RelationTokenizerConfig | None = None,
    goal: GoalSpec | None = None,
) -> list[RelationToken]:
    """EntityToken과 goal spec에서 navigation RelationToken을 생성합니다.

    이 함수는 simulator controller에 의존하지 않는 pure function입니다. Relation은 현재 MVP에서
    simple geometry rule 기반이며 learned relation extraction 결과가 아닙니다.
    """

    relation_config = config or RelationTokenizerConfig()
    _validate_config(relation_config)

    tokens: list[RelationToken] = []
    for entity in entities:
        features = path_proxy_features(
            agent_position=snapshot.agent_state.position,
            agent_yaw_degrees=_agent_yaw_degrees(snapshot),
            object_position=entity.position,
            distance_to_agent=entity.distance_to_agent,
            lookahead=relation_config.path_lookahead,
        )
        if entity.distance_to_agent <= relation_config.near_agent_threshold:
            tokens.append(
                _relation_token(
                    index=len(tokens),
                    relation="near_agent",
                    object_id=entity.entity_id,
                    confidence=entity.confidence,
                    timestamp=snapshot.step,
                    threshold=relation_config.near_agent_threshold,
                    observed_value=entity.distance_to_agent,
                    features=features,
                    category=entity.category,
                    path_segment_id=None,
                )
            )
        if _is_near_path(features, relation_config):
            tokens.append(
                _relation_token(
                    index=len(tokens),
                    relation="near_path",
                    object_id=entity.entity_id,
                    confidence=entity.confidence,
                    timestamp=snapshot.step,
                    threshold=relation_config.near_path_lateral_threshold,
                    observed_value=features.lateral_distance,
                    features=features,
                    category=entity.category,
                    path_segment_id=relation_config.path_segment_id,
                )
            )
        if _is_blocking_path(features, relation_config):
            tokens.append(
                _relation_token(
                    index=len(tokens),
                    relation="blocking_path",
                    object_id=entity.entity_id,
                    confidence=entity.confidence,
                    timestamp=snapshot.step,
                    threshold=relation_config.blocking_path_lateral_threshold,
                    observed_value=features.lateral_distance,
                    features=features,
                    category=entity.category,
                    path_segment_id=relation_config.path_segment_id,
                )
            )

    goal_token = _target_reachable_token(snapshot, goal=goal, config=relation_config, token_index=len(tokens))
    if goal_token is not None:
        tokens.append(goal_token)
    return tokens


def path_proxy_features(
    *,
    agent_position: Vector3,
    agent_yaw_degrees: float,
    object_position: Vector3,
    distance_to_agent: float | None = None,
    lookahead: float,
) -> PathProxyFeatures:
    """Agent 전방 ray 기준 projection/lateral distance를 계산합니다."""

    yaw = radians(agent_yaw_degrees)
    forward_x = sin(yaw)
    forward_z = cos(yaw)
    dx = object_position.x - agent_position.x
    dz = object_position.z - agent_position.z
    projection = (dx * forward_x) + (dz * forward_z)
    lateral_distance = abs((dx * forward_z) - (dz * forward_x))
    distance = distance_to_agent if distance_to_agent is not None else _vector_distance(agent_position, object_position)
    return PathProxyFeatures(
        projection=projection,
        lateral_distance=lateral_distance,
        distance_to_agent=distance,
        is_ahead=projection >= 0,
        within_lookahead=0 <= projection <= lookahead,
    )


def _target_reachable_token(
    snapshot: ObservationSnapshot,
    *,
    goal: GoalSpec | None,
    config: RelationTokenizerConfig,
    token_index: int,
) -> RelationToken | None:
    if goal is None:
        return None
    target_position = _goal_target_position(snapshot, goal)
    if target_position is None:
        return None
    features = path_proxy_features(
        agent_position=snapshot.agent_state.position,
        agent_yaw_degrees=_agent_yaw_degrees(snapshot),
        object_position=target_position,
        lookahead=config.path_lookahead,
    )
    if not features.is_ahead or features.lateral_distance > config.near_path_lateral_threshold:
        return None
    if features.distance_to_agent > config.target_reachable_distance:
        return None
    return _relation_token(
        index=token_index,
        relation="target_reachable",
        object_id=_goal_object_id(goal),
        confidence=1.0,
        timestamp=snapshot.step,
        threshold=config.target_reachable_distance,
        observed_value=features.distance_to_agent,
        features=features,
        category="goal",
        path_segment_id=config.path_segment_id,
    )


def _relation_token(
    *,
    index: int,
    relation: str,
    object_id: str,
    confidence: float,
    timestamp: int,
    threshold: float,
    observed_value: float,
    features: PathProxyFeatures,
    category: str,
    path_segment_id: str | None,
) -> RelationToken:
    return RelationToken(
        token_id=f"rel_{index:04d}",
        subject_id=AGENT_NODE_ID,
        relation=relation,  # type: ignore[arg-type]
        object_id=object_id,
        confidence=confidence,
        timestamp=timestamp,
        distance_margin=threshold - observed_value,
        path_segment_id=path_segment_id,
        relation_features={
            "category": category,
            "projection": features.projection,
            "lateral_distance": features.lateral_distance,
            "distance_to_agent": features.distance_to_agent,
            "is_ahead": features.is_ahead,
            "within_lookahead": features.within_lookahead,
            "threshold": threshold,
        },
    )


def _is_near_path(features: PathProxyFeatures, config: RelationTokenizerConfig) -> bool:
    return (
        features.is_ahead
        and features.within_lookahead
        and features.lateral_distance <= config.near_path_lateral_threshold
    )


def _is_blocking_path(features: PathProxyFeatures, config: RelationTokenizerConfig) -> bool:
    return (
        _is_near_path(features, config)
        and features.lateral_distance <= config.blocking_path_lateral_threshold
        and features.distance_to_agent <= config.blocking_path_distance_threshold
    )


def _goal_target_position(snapshot: ObservationSnapshot, goal: GoalSpec) -> Vector3 | None:
    if goal.goal_type == "reach_position":
        return goal.target_position
    for item in snapshot.objects:
        if goal.target_object_id is not None and item.object_id == goal.target_object_id:
            return item.position
        if goal.target_category is not None and item.category == goal.target_category:
            return item.position
    return None


def _goal_object_id(goal: GoalSpec) -> str:
    if goal.target_object_id:
        return goal.target_object_id
    if goal.target_category:
        return f"goal_category:{goal.target_category}"
    return "goal:reach_position"


def _agent_yaw_degrees(snapshot: ObservationSnapshot) -> float:
    if snapshot.agent_state.rotation is None:
        return 0.0
    return snapshot.agent_state.rotation.y


def _vector_distance(first: Vector3, second: Vector3) -> float:
    return sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2 + (first.z - second.z) ** 2)


def _validate_config(config: RelationTokenizerConfig) -> None:
    if config.near_agent_threshold <= 0:
        raise ValueError("near_agent_threshold는 0보다 커야 합니다.")
    if config.near_path_lateral_threshold < 0:
        raise ValueError("near_path_lateral_threshold는 0 이상이어야 합니다.")
    if config.blocking_path_lateral_threshold < 0:
        raise ValueError("blocking_path_lateral_threshold는 0 이상이어야 합니다.")
    if config.blocking_path_distance_threshold <= 0:
        raise ValueError("blocking_path_distance_threshold는 0보다 커야 합니다.")
    if config.path_lookahead <= 0:
        raise ValueError("path_lookahead는 0보다 커야 합니다.")
    if config.target_reachable_distance <= 0:
        raise ValueError("target_reachable_distance는 0보다 커야 합니다.")

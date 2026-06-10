"""일반 Scene Graph baseline representation을 생성합니다."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rast.schemas.metrics import GoalSpec
from rast.schemas.observation import ObservationSnapshot
from rast.schemas.tokens import RelationToken


AGENT_NODE_ID = "agent"
GOAL_NODE_ID = "goal"


@dataclass(frozen=True)
class SceneGraphNode:
    """Scene Graph baseline의 node입니다."""

    node_id: str
    node_type: str
    category: str
    features: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SceneGraphEdge:
    """Scene Graph baseline의 relation edge입니다."""

    subject_id: str
    relation: str
    object_id: str
    confidence: float
    features: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SceneGraph:
    """MVP용 simplified scene graph입니다."""

    nodes: list[SceneGraphNode]
    edges: list[SceneGraphEdge]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def edges_by_relation(self, relation: str) -> list[SceneGraphEdge]:
        return [edge for edge in self.edges if edge.relation == relation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.__dict__ for node in self.nodes],
            "edges": [edge.__dict__ for edge in self.edges],
            "node_count": self.node_count,
            "edge_count": self.edge_count,
        }


def build_scene_graph(
    snapshot: ObservationSnapshot,
    relation_tokens: list[RelationToken],
    *,
    goal: GoalSpec | None = None,
    visible_only: bool = True,
) -> SceneGraph:
    """ObservationSnapshot과 relation source에서 simplified Scene Graph baseline을 생성합니다."""

    nodes = [
        SceneGraphNode(
            node_id=AGENT_NODE_ID,
            node_type="agent",
            category="agent",
            features={
                "x": snapshot.agent_state.position.x,
                "y": snapshot.agent_state.position.y,
                "z": snapshot.agent_state.position.z,
            },
        )
    ]
    for obj in snapshot.objects:
        if visible_only and obj.visible is False:
            continue
        nodes.append(
            SceneGraphNode(
                node_id=obj.object_id,
                node_type="object",
                category=obj.category,
                features={
                    "x": obj.position.x,
                    "y": obj.position.y,
                    "z": obj.position.z,
                    "visible": obj.visible,
                    "distance_to_agent": obj.distance_to_agent,
                    "confidence": obj.confidence,
                },
            )
        )
    if goal is not None:
        nodes.append(
            SceneGraphNode(
                node_id=GOAL_NODE_ID,
                node_type="goal",
                category=goal.target_category or goal.goal_type,
                features={
                    "goal_type": goal.goal_type,
                    "target_object_id": goal.target_object_id,
                    "success_distance": goal.success_distance,
                },
            )
        )

    node_ids = {node.node_id for node in nodes}
    edges: list[SceneGraphEdge] = []
    for token in relation_tokens:
        # RAST-only risk contract field는 사용하지 않고 relation edge 정보만 보존합니다.
        object_id = GOAL_NODE_ID if token.relation == "target_reachable" and token.object_id.startswith("goal:") else token.object_id
        if object_id not in node_ids and token.relation != "target_reachable":
            continue
        edges.append(
            SceneGraphEdge(
                subject_id=token.subject_id,
                relation=token.relation,
                object_id=object_id,
                confidence=token.confidence,
                features={
                    "distance_margin": token.distance_margin,
                    "path_segment_id": token.path_segment_id,
                    **token.relation_features,
                },
            )
        )

    return SceneGraph(nodes=nodes, edges=edges)

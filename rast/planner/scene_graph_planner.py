"""Scene Graph baseline을 사용하는 deterministic planner입니다."""

from __future__ import annotations

from rast.baselines.scene_graph import SceneGraph, SceneGraphEdge
from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision


def plan_from_scene_graph(graph: SceneGraph) -> PlannerDecision:
    """Scene Graph edge structure만 사용해 action과 decision trace를 반환합니다."""

    blocking_edge = _first_edge(graph, "blocking_path")
    if blocking_edge is not None:
        return _decision_from_edge(
            edge=blocking_edge,
            action=Action.ROTATE_RIGHT,
            reason_code="graph_blocking_path",
            reason_text="Scene graph contains a blocking_path edge.",
        )

    near_edge = _first_edge(graph, "near_agent")
    if near_edge is not None:
        return _decision_from_edge(
            edge=near_edge,
            action=Action.ROTATE_RIGHT,
            reason_code="graph_near_object",
            reason_text="Scene graph contains a near_agent edge.",
        )

    target_edge = _first_edge(graph, "target_reachable")
    if target_edge is not None:
        return _decision_from_edge(
            edge=target_edge,
            action=Action.MOVE_AHEAD,
            reason_code="graph_target_reachable",
            reason_text="Scene graph contains a reachable target relation without blocking edges.",
        )

    return PlannerDecision(
        planner_name="scene_graph",
        action=Action.MOVE_AHEAD,
        reason_code="graph_no_blocking_move_ahead",
        reason_text="Scene graph has no blocking or near-agent relation.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
        },
        confidence=1.0,
    )


def _first_edge(graph: SceneGraph, relation: str) -> SceneGraphEdge | None:
    edges = graph.edges_by_relation(relation)
    return edges[0] if edges else None


def _decision_from_edge(
    *,
    edge: SceneGraphEdge,
    action: Action,
    reason_code: str,
    reason_text: str,
) -> PlannerDecision:
    return PlannerDecision(
        planner_name="scene_graph",
        action=action,
        reason_code=reason_code,
        reason_text=reason_text,
        trigger_object_ids=[edge.object_id],
        trigger_token_ids=[],
        trigger_features={
            "relation": edge.relation,
            "confidence": edge.confidence,
            **edge.features,
        },
        confidence=edge.confidence,
    )

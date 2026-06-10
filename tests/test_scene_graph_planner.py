from rast.baselines.scene_graph import build_scene_graph
from rast.planner.actions import Action
from rast.planner.scene_graph_planner import plan_from_scene_graph
from rast.schemas.decision import PlannerDecision
from rast.simulator.windows_scenarios import build_windows_scenario
from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.relation_tokenizer import RelationTokenizerConfig, build_relation_tokens


def _graph_for_scenario(name: str):
    scenario = build_windows_scenario(name)
    snapshot = scenario.simulator.snapshot(episode_id="scene_graph_planner_test")
    entities = build_entity_tokens(snapshot)
    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(
            near_agent_threshold=scenario.risk_threshold,
            blocking_path_distance_threshold=scenario.risk_threshold,
        ),
        goal=scenario.goal,
    )
    return build_scene_graph(snapshot, relations, goal=scenario.goal)


def test_scene_graph_planner_returns_decision_for_blocking_edge() -> None:
    graph = _graph_for_scenario("near_obstacle")

    decision = plan_from_scene_graph(graph)

    assert isinstance(decision, PlannerDecision)
    assert decision.action in {Action.ROTATE_RIGHT, Action.STOP}
    assert decision.reason_code == "graph_blocking_path"
    assert decision.trigger_object_ids


def test_scene_graph_planner_moves_ahead_without_blocking_relation() -> None:
    graph = _graph_for_scenario("clear_path")

    decision = plan_from_scene_graph(graph)

    assert decision.action == Action.MOVE_AHEAD
    assert decision.reason_code in {"graph_no_blocking_move_ahead", "graph_target_reachable"}

from rast.baselines.scene_graph import build_scene_graph
from rast.simulator.windows_scenarios import build_windows_scenario
from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.relation_tokenizer import RelationTokenizerConfig, build_relation_tokens


def test_scene_graph_uses_same_visible_object_source_as_snapshot() -> None:
    scenario = build_windows_scenario("near_obstacle")
    snapshot = scenario.simulator.snapshot(episode_id="scene_graph_test")
    entities = build_entity_tokens(snapshot)
    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(near_agent_threshold=scenario.risk_threshold),
    )

    graph = build_scene_graph(snapshot, relations)
    visible_objects = [item for item in snapshot.objects if item.visible is not False]

    assert graph.node_count == len(visible_objects) + 1
    assert {node.node_id for node in graph.nodes}.issuperset({item.object_id for item in visible_objects})


def test_scene_graph_edges_follow_relation_tokens() -> None:
    scenario = build_windows_scenario("near_obstacle")
    snapshot = scenario.simulator.snapshot(episode_id="scene_graph_test")
    entities = build_entity_tokens(snapshot)
    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(
            near_agent_threshold=scenario.risk_threshold,
            blocking_path_distance_threshold=scenario.risk_threshold,
        ),
    )

    graph = build_scene_graph(snapshot, relations)

    assert graph.edge_count == len(relations)
    assert any(edge.relation == "blocking_path" for edge in graph.edges)
    assert all("recommended_policy" not in edge.features for edge in graph.edges)

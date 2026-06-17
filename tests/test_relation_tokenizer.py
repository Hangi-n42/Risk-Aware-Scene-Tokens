from rast.schemas.metrics import GoalSpec
from rast.simulator.windows_scenarios import build_windows_scenario
from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.relation_tokenizer import RelationTokenizerConfig, build_relation_tokens


def test_near_object_creates_near_agent_relation() -> None:
    scenario = build_windows_scenario("near_obstacle")
    snapshot = scenario.simulator.snapshot(episode_id="relation_test")
    entities = build_entity_tokens(snapshot)

    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(near_agent_threshold=scenario.risk_threshold),
    )

    assert any(token.relation == "near_agent" for token in relations)


def test_blocking_path_scenario_creates_blocking_path_relation() -> None:
    scenario = build_windows_scenario("near_obstacle")
    snapshot = scenario.simulator.snapshot(episode_id="relation_test")
    entities = build_entity_tokens(snapshot)

    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(
            near_agent_threshold=scenario.risk_threshold,
            blocking_path_distance_threshold=scenario.risk_threshold,
        ),
    )

    assert any(token.relation == "blocking_path" for token in relations)


def test_clear_path_has_no_blocking_relation() -> None:
    scenario = build_windows_scenario("clear_path")
    snapshot = scenario.simulator.snapshot(episode_id="relation_test")
    entities = build_entity_tokens(snapshot)

    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(near_agent_threshold=scenario.risk_threshold),
    )

    assert not any(token.relation == "blocking_path" for token in relations)


def test_target_reachable_relation_uses_goal_spec() -> None:
    scenario = build_windows_scenario("target_reachable")
    assert isinstance(scenario.goal, GoalSpec)
    snapshot = scenario.simulator.snapshot(episode_id="relation_test")
    entities = build_entity_tokens(snapshot)

    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(target_reachable_distance=1.5),
        goal=scenario.goal,
    )

    assert any(token.relation == "target_reachable" for token in relations)


def test_relation_threshold_can_be_larger_than_risk_threshold() -> None:
    scenario = build_windows_scenario("relation_near_but_low_risk")
    snapshot = scenario.simulator.snapshot(episode_id="relation_threshold_split_test")
    entities = build_entity_tokens(snapshot)

    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(
            near_agent_threshold=scenario.resolved_near_agent_relation_threshold,
            near_path_lateral_threshold=scenario.resolved_near_path_relation_threshold,
            blocking_path_distance_threshold=scenario.resolved_blocking_relation_threshold,
        ),
    )

    assert any(token.relation == "near_agent" for token in relations)


def test_risk_scenario_can_avoid_blocking_path_relation() -> None:
    scenario = build_windows_scenario("risk_without_graph_blocking")
    snapshot = scenario.simulator.snapshot(episode_id="relation_threshold_split_test")
    entities = build_entity_tokens(snapshot)

    relations = build_relation_tokens(
        snapshot,
        entities,
        config=RelationTokenizerConfig(
            near_agent_threshold=scenario.resolved_near_agent_relation_threshold,
            near_path_lateral_threshold=scenario.resolved_near_path_relation_threshold,
            blocking_path_distance_threshold=scenario.resolved_blocking_relation_threshold,
        ),
    )

    assert not any(token.relation == "blocking_path" for token in relations)

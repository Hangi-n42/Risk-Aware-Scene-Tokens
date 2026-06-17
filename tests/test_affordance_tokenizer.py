from rast.simulator.windows_scenarios import build_windows_scenario
from rast.tokenizer.affordance_tokenizer import AffordanceTokenizerConfig
from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.relation_tokenizer import RelationTokenizerConfig
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig
from rast.tokenizer.uncertainty_tokenizer import UncertaintyTokenizerConfig


def affordances_for_scenario(name: str) -> set[str]:
    scenario = build_windows_scenario(name)
    snapshot = scenario.simulator.snapshot(episode_id=f"test_{name}")
    result = tokenize_snapshot(
        snapshot,
        risk_config=RiskTokenizerConfig(near_agent_threshold=scenario.risk_threshold),
        relation_config=RelationTokenizerConfig(
            near_agent_threshold=scenario.resolved_near_agent_relation_threshold,
            near_path_lateral_threshold=scenario.resolved_near_path_relation_threshold,
            blocking_path_distance_threshold=scenario.resolved_blocking_relation_threshold,
            target_reachable_distance=max(scenario.risk_threshold, scenario.near_miss_threshold, 1.5),
        ),
        uncertainty_config=UncertaintyTokenizerConfig(
            risk_threshold=scenario.risk_threshold,
            path_lateral_threshold=scenario.resolved_near_path_relation_threshold,
        ),
        affordance_config=AffordanceTokenizerConfig(
            path_lateral_threshold=scenario.resolved_near_path_relation_threshold,
            collision_clearance=scenario.collision_threshold,
        ),
        goal=scenario.goal,
        enable_relations=True,
        enable_uncertainty=True,
        enable_affordances=True,
    )
    return {token.affordance for token in result.affordances}


def test_passable_clear_gap_generates_passable_affordance() -> None:
    assert "passable" in affordances_for_scenario("passable_clear_gap")


def test_narrow_passage_generates_narrow_affordance() -> None:
    assert "narrow_passage" in affordances_for_scenario("narrow_passage")


def test_uncertain_path_generates_inspect_required_affordance() -> None:
    assert "inspect_required" in affordances_for_scenario("inspect_required_uncertain_path")


def test_blocking_path_generates_avoid_or_blocking_affordance() -> None:
    affordances = affordances_for_scenario("avoid_required_blocking_path")

    assert {"avoid_required", "blocking"} & affordances


def test_target_reachable_generates_target_affordance() -> None:
    assert "target_reachable" in affordances_for_scenario("target_reachable_affordance")

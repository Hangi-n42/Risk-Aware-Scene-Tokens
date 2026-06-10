from rast.baselines.object_list import build_object_list
from rast.planner.actions import ACTIONS, Action
from rast.planner.object_list_planner import ObjectListPlannerConfig, plan_from_object_list
from rast.planner.token_planner import plan_from_tokens
from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig, build_risk_tokens

from tests.test_entity_tokenizer import load_sample_snapshot


def test_token_planner_avoids_move_ahead_when_high_risk_exists() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)
    risks = build_risk_tokens(entities, config=RiskTokenizerConfig(near_agent_threshold=1.6))

    decision = plan_from_tokens(entities, risks)

    assert decision.action in ACTIONS
    assert decision.action != Action.MOVE_AHEAD
    assert decision.reason_code == "high_risk_token"
    assert decision.trigger_token_ids


def test_token_planner_moves_ahead_without_risk() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)

    decision = plan_from_tokens(entities, [])

    assert decision.action == Action.MOVE_AHEAD
    assert decision.reason_code == "no_risk_move_ahead"


def test_object_list_planner_uses_same_action_set_as_token_planner() -> None:
    snapshot = load_sample_snapshot()
    object_list = build_object_list(snapshot)

    decision = plan_from_object_list(
        object_list,
        config=ObjectListPlannerConfig(near_object_threshold=1.6),
    )

    assert decision.action in ACTIONS
    assert isinstance(decision.action, Action)
    assert decision.action != Action.MOVE_AHEAD
    assert decision.reason_code == "near_object_distance"
    assert decision.trigger_object_ids

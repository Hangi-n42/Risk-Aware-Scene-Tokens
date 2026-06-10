from rast.baselines.flat_feature_table import build_flat_feature_table
from rast.baselines.object_list import build_object_list
from rast.planner.actions import Action
from rast.planner.flat_feature_planner import plan_from_flat_features
from rast.planner.object_list_planner import ObjectListPlannerConfig, plan_from_object_list
from rast.planner.token_planner import plan_from_tokens
from rast.schemas.decision import PlannerDecision
from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig, build_risk_tokens

from tests.test_entity_tokenizer import load_sample_snapshot


def test_planner_decision_exposes_action_value_for_compatibility() -> None:
    decision = PlannerDecision(
        planner_name="rast",
        action=Action.MOVE_AHEAD,
        reason_code="no_risk_move_ahead",
        reason_text="No RiskToken is present.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={},
        confidence=1.0,
    )

    assert decision.value == "MoveAhead"
    assert decision.to_dict()["action"] == "MoveAhead"


def test_rast_decision_records_risk_token_trigger() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)
    risks = build_risk_tokens(entities, config=RiskTokenizerConfig(near_agent_threshold=1.6))

    decision = plan_from_tokens(entities, risks)

    assert decision.action != Action.MOVE_AHEAD
    assert decision.reason_code == "high_risk_token"
    assert decision.trigger_token_ids
    assert decision.trigger_object_ids
    assert "risk_score" in decision.trigger_features


def test_object_list_decision_records_near_object_trigger() -> None:
    snapshot = load_sample_snapshot()
    object_list = build_object_list(snapshot)

    decision = plan_from_object_list(
        object_list,
        config=ObjectListPlannerConfig(near_object_threshold=1.6),
    )

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code == "near_object_distance"
    assert decision.trigger_object_ids
    assert "distance_to_agent" in decision.trigger_features


def test_flat_feature_decision_records_scalar_trigger_features() -> None:
    snapshot = load_sample_snapshot()
    rows = build_flat_feature_table(snapshot, risk_threshold=1.6)

    decision = plan_from_flat_features(rows)

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code in {"within_risk_threshold", "high_risk_score_scalar"}
    assert decision.trigger_object_ids
    assert "risk_score_scalar" in decision.trigger_features
    assert "within_risk_threshold" in decision.trigger_features


def test_no_risk_decision_moves_ahead_with_no_risk_reason() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)

    decision = plan_from_tokens(entities, [])

    assert decision.action == Action.MOVE_AHEAD
    assert decision.reason_code == "no_risk_move_ahead"
    assert decision.trigger_token_ids == []

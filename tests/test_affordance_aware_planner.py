from rast.planner.actions import Action
from rast.planner.affordance_aware_token_planner import plan_from_affordance_aware_tokens
from rast.schemas.tokens import AffordanceToken


def affordance(affordance_type: str, *, token_id: str | None = None) -> AffordanceToken:
    return AffordanceToken(
        token_id=token_id or f"aff_{affordance_type}",
        entity_id=f"entity_{affordance_type}",
        affordance=affordance_type,  # type: ignore[arg-type]
        confidence=1.0,
        timestamp=1,
        action_hint="test_hint",
        affordance_features={"source": "unit_test"},
    )


def test_affordance_aware_planner_moves_ahead_on_passable() -> None:
    decision = plan_from_affordance_aware_tokens([], [], [], [affordance("passable")])

    assert decision.action == Action.MOVE_AHEAD
    assert decision.reason_code == "affordance_passable_move_ahead"
    assert decision.trigger_token_ids == ["aff_passable"]


def test_affordance_aware_planner_rotates_on_narrow_passage() -> None:
    decision = plan_from_affordance_aware_tokens([], [], [], [affordance("narrow_passage")])

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code == "affordance_narrow_passage_slow_or_rotate"


def test_affordance_aware_planner_stops_on_inspect_required() -> None:
    decision = plan_from_affordance_aware_tokens([], [], [], [affordance("inspect_required")])

    assert decision.action == Action.STOP
    assert decision.reason_code == "affordance_inspect_required"


def test_affordance_aware_planner_rotates_on_avoid_required() -> None:
    decision = plan_from_affordance_aware_tokens([], [], [], [affordance("avoid_required")])

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code == "affordance_avoid_required"


def test_affordance_aware_planner_moves_ahead_on_target_reachable() -> None:
    decision = plan_from_affordance_aware_tokens([], [], [], [affordance("target_reachable")])

    assert decision.action == Action.MOVE_AHEAD
    assert decision.reason_code == "affordance_target_reachable"

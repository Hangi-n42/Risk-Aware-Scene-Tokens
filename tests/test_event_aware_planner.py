from rast.planner.actions import Action
from rast.planner.event_aware_token_planner import plan_from_event_aware_tokens
from rast.planner.token_planner import plan_from_tokens
from rast.schemas.common import Vector3
from rast.schemas.tokens import EntityToken, EventToken, RiskToken


def entity(entity_id: str = "Box|event|front", *, distance: float = 0.8) -> EntityToken:
    return EntityToken(
        token_id=f"ent_{entity_id}",
        entity_id=entity_id,
        category="Box",
        position=Vector3(x=0.0, y=0.0, z=distance),
        distance_to_agent=distance,
        timestamp=1,
    )


def risk(entity_id: str = "Box|event|front", *, severity: str = "medium") -> RiskToken:
    return RiskToken(
        token_id=f"risk_{entity_id}",
        risk_type="near_agent_obstacle",
        severity=severity,
        entity_id=entity_id,
        affected_area={"agent_radius": 1.5, "entity_distance_to_agent": 0.8},
        risk_score=0.5,
        risk_features={"distance_to_agent": 0.8, "near_agent_threshold": 1.5},
        timestamp=1,
    )


def event(event_type: str, entity_id: str = "Box|event|front") -> EventToken:
    return EventToken(
        token_id=f"evt_{event_type}",
        event_type=event_type,  # type: ignore[arg-type]
        entity_id=entity_id,
        previous_state={"risk_score": 0.0} if event_type != "object_appeared" else {},
        current_state={"risk_score": 0.5} if event_type != "object_disappeared" else {},
        severity="medium",
        timestamp=1,
    )


def test_event_aware_planner_uses_object_appeared_risk_reason() -> None:
    current_entity = entity()
    current_risk = risk()
    decision = plan_from_event_aware_tokens(
        [current_entity],
        [current_risk],
        [event("object_appeared")],
    )

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code == "event_object_appeared_near_path"
    assert decision.trigger_token_ids == ["evt_object_appeared", "risk_Box|event|front"]
    assert decision.trigger_features["event_types"] == ["object_appeared"]


def test_event_aware_planner_falls_back_like_existing_rast_without_events() -> None:
    current_entity = entity()
    current_risk = risk(severity="high")

    event_aware_decision = plan_from_event_aware_tokens([current_entity], [current_risk], [])
    rast_decision = plan_from_tokens([current_entity], [current_risk])

    assert event_aware_decision.action == rast_decision.action
    assert event_aware_decision.reason_code == "fallback_risk_token_present"


def test_event_aware_planner_can_move_ahead_after_disappeared_clear_path() -> None:
    decision = plan_from_event_aware_tokens(
        [entity("Sofa|far", distance=2.5)],
        [],
        [event("object_disappeared")],
    )

    assert decision.action == Action.MOVE_AHEAD
    assert decision.reason_code == "event_object_disappeared_clear_path"
    assert decision.trigger_features["event_types"] == ["object_disappeared"]


def test_logging_only_variant_matches_existing_rast_action() -> None:
    current_entity = entity()
    current_risk = risk(severity="medium")

    event_aware_decision = plan_from_event_aware_tokens(
        [current_entity],
        [current_risk],
        [event("risk_changed")],
        policy_variant="logging_only",
    )
    rast_decision = plan_from_tokens([current_entity], [current_risk])

    assert event_aware_decision.action == rast_decision.action
    assert event_aware_decision.trigger_features["event_policy_variant"] == "logging_only"
    assert "risk_changed" in event_aware_decision.trigger_features["disabled_event_rules"]


def test_no_risk_changed_variant_does_not_react_to_risk_changed_event() -> None:
    current_entity = entity()
    current_risk = risk(severity="medium")

    full_decision = plan_from_event_aware_tokens(
        [current_entity],
        [current_risk],
        [event("risk_changed")],
        policy_variant="full",
    )
    ablated_decision = plan_from_event_aware_tokens(
        [current_entity],
        [current_risk],
        [event("risk_changed")],
        policy_variant="no_risk_changed",
    )

    assert full_decision.action == Action.STOP
    assert full_decision.reason_code == "event_risk_increased"
    assert ablated_decision.action == Action.ROTATE_RIGHT
    assert ablated_decision.reason_code == "fallback_risk_token_present"
    assert ablated_decision.trigger_features["event_policy_variant"] == "no_risk_changed"
    assert ablated_decision.trigger_features["disabled_event_rules"] == ["risk_changed"]

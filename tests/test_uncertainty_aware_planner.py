from rast.planner.actions import Action
from rast.planner.uncertainty_aware_token_planner import plan_from_uncertainty_aware_tokens
from rast.schemas.common import Vector3
from rast.schemas.tokens import EntityToken, RiskToken, UncertaintyToken


def entity(entity_id: str = "Box|uncertain|front", *, distance: float = 1.8) -> EntityToken:
    return EntityToken(
        token_id=f"ent_{entity_id}",
        entity_id=entity_id,
        category="Box",
        position=Vector3(x=0.0, y=0.0, z=distance),
        distance_to_agent=distance,
        timestamp=1,
    )


def risk(entity_id: str = "Box|uncertain|front", *, severity: str = "medium") -> RiskToken:
    return RiskToken(
        token_id=f"risk_{entity_id}",
        risk_type="near_agent_obstacle",
        severity=severity,
        entity_id=entity_id,
        affected_area={"agent_radius": 1.5},
        risk_score=0.5,
        risk_features={"distance_to_agent": 0.8, "near_agent_threshold": 1.5},
        timestamp=1,
    )


def uncertainty(
    uncertainty_type: str = "classification_uncertainty",
    *,
    entity_id: str = "Box|uncertain|front",
    level: str = "high",
    near_path: bool = True,
) -> UncertaintyToken:
    return UncertaintyToken(
        token_id=f"unc_{uncertainty_type}",
        uncertainty_type=uncertainty_type,  # type: ignore[arg-type]
        entity_id=entity_id,
        level=level,  # type: ignore[arg-type]
        recommended_action="inspect_before_passing",
        uncertainty_features={
            "near_path": near_path,
            "distance_to_path_proxy": 0.1 if near_path else 1.2,
            "near_risk_boundary": uncertainty_type == "position_uncertainty",
        },
        timestamp=1,
    )


def test_uncertainty_aware_planner_reacts_to_high_uncertainty_near_path() -> None:
    current_entity = entity()
    decision = plan_from_uncertainty_aware_tokens(
        [current_entity],
        [],
        [uncertainty()],
    )

    assert decision.action != Action.MOVE_AHEAD
    assert decision.reason_code == "high_uncertainty_near_path"
    assert decision.trigger_token_ids == ["unc_classification_uncertainty"]


def test_unknown_object_uncertainty_has_specific_reason_code() -> None:
    decision = plan_from_uncertainty_aware_tokens(
        [entity("UnknownObject|uncertain")],
        [],
        [uncertainty("unknown_object", entity_id="UnknownObject|uncertain")],
    )

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code == "unknown_object_uncertainty"


def test_uncertainty_unrelated_to_path_falls_back_to_rast_like_policy() -> None:
    current_entity = entity()
    current_risk = risk(severity="medium")
    decision = plan_from_uncertainty_aware_tokens(
        [current_entity],
        [current_risk],
        [uncertainty(near_path=False)],
    )

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code == "fallback_risk_token_present"


def test_position_uncertainty_boundary_can_trigger_conservative_action() -> None:
    decision = plan_from_uncertainty_aware_tokens(
        [entity()],
        [],
        [uncertainty("position_uncertainty", level="medium")],
    )

    assert decision.action == Action.ROTATE_RIGHT
    assert decision.reason_code == "position_uncertainty_boundary"

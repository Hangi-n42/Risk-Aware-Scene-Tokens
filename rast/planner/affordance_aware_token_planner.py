"""AffordanceToken??decision reason??諛섏쁺?섎뒗 ?ㅽ뿕??RAST planner?낅땲??"""

from __future__ import annotations

from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision
from rast.schemas.tokens import AffordanceToken, EntityToken, EventToken, RelationToken, RiskToken, UncertaintyToken


AFFORDANCE_BASED_REASON_CODES: set[str] = {
    "affordance_passable_move_ahead",
    "affordance_narrow_passage_slow_or_rotate",
    "affordance_inspect_required",
    "affordance_avoid_required",
    "affordance_target_reachable",
}


def plan_from_affordance_aware_tokens(
    entities: list[EntityToken],
    risks: list[RiskToken],
    relations: list[RelationToken],
    affordances: list[AffordanceToken],
    events: list[EventToken] | None = None,
    uncertainties: list[UncertaintyToken] | None = None,
) -> PlannerDecision:
    """Navigation AffordanceToken???뚯떆?곸쑝濡??ъ슜??PlannerDecision??諛섑솚?⑸땲??"""

    del entities, relations, events, uncertainties
    avoid = _first_affordance(affordances, {"avoid_required", "blocking"})
    if avoid is not None:
        return _affordance_decision(
            token=avoid,
            action=Action.ROTATE_RIGHT,
            reason_code="affordance_avoid_required",
            reason_text="An affordance indicates that the path should be avoided or treated as blocking.",
        )

    inspect = _first_affordance(affordances, {"inspect_required"})
    if inspect is not None:
        return _affordance_decision(
            token=inspect,
            action=Action.STOP,
            reason_code="affordance_inspect_required",
            reason_text="An affordance indicates that the path should be inspected before passing.",
        )

    narrow = _first_affordance(affordances, {"narrow_passage"})
    if narrow is not None:
        return _affordance_decision(
            token=narrow,
            action=Action.ROTATE_RIGHT,
            reason_code="affordance_narrow_passage_slow_or_rotate",
            reason_text="A narrow passage affordance requires a conservative navigation action.",
        )

    target = _first_affordance(affordances, {"target_reachable"})
    if target is not None:
        return _affordance_decision(
            token=target,
            action=Action.MOVE_AHEAD,
            reason_code="affordance_target_reachable",
            reason_text="A target_reachable affordance indicates that moving ahead can progress toward the goal.",
        )

    passable = _first_affordance(affordances, {"passable"})
    if passable is not None:
        return _affordance_decision(
            token=passable,
            action=Action.MOVE_AHEAD,
            reason_code="affordance_passable_move_ahead",
            reason_text="A passable affordance indicates that the forward path can be used.",
        )

    return _fallback_decision(risks)


def _first_affordance(affordances: list[AffordanceToken], allowed: set[str]) -> AffordanceToken | None:
    return next((token for token in affordances if token.affordance in allowed), None)


def _affordance_decision(
    *,
    token: AffordanceToken,
    action: Action,
    reason_code: str,
    reason_text: str,
) -> PlannerDecision:
    return PlannerDecision(
        planner_name="affordance_aware_rast",
        action=action,
        reason_code=reason_code,
        reason_text=reason_text,
        trigger_object_ids=[token.entity_id],
        trigger_token_ids=[token.token_id],
        trigger_features={
            "affordance": token.affordance,
            "action_hint": token.action_hint,
            "navigation_margin": token.navigation_margin,
            "failure_risk": token.failure_risk,
            **token.affordance_features,
        },
        confidence=token.confidence,
        evidence_token_ids=token.evidence_token_ids,
    )


def _fallback_decision(risks: list[RiskToken]) -> PlannerDecision:
    high_risk = next((risk for risk in risks if risk.severity == "high"), None)
    if high_risk is not None:
        return _risk_fallback_decision(
            risk=high_risk,
            action=Action.STOP,
            reason_text="No affordance-specific rule fired, but a high RiskToken is present.",
        )
    if risks:
        return _risk_fallback_decision(
            risk=risks[0],
            action=Action.ROTATE_RIGHT,
            reason_text="No affordance-specific rule fired, but a RiskToken is present.",
        )
    return PlannerDecision(
        planner_name="affordance_aware_rast",
        action=Action.MOVE_AHEAD,
        reason_code="fallback_no_risk_move_ahead",
        reason_text="No AffordanceToken or RiskToken requires avoidance.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={"risk_token_count": 0, "affordance_triggered": False},
        confidence=1.0,
    )


def _risk_fallback_decision(*, risk: RiskToken, action: Action, reason_text: str) -> PlannerDecision:
    return PlannerDecision(
        planner_name="affordance_aware_rast",
        action=action,
        reason_code="fallback_risk_token_present",
        reason_text=reason_text,
        trigger_object_ids=[risk.entity_id],
        trigger_token_ids=[risk.token_id],
        trigger_features={
            "risk_type": risk.risk_type,
            "severity": risk.severity,
            "risk_score": risk.risk_score,
            "affordance_triggered": False,
            **risk.risk_features,
        },
        confidence=risk.confidence,
    )

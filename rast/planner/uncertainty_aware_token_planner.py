"""UncertaintyToken을 decision reason에 반영하는 실험용 RAST planner입니다."""

from __future__ import annotations

from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision
from rast.schemas.tokens import EntityToken, EventToken, RiskToken, UncertaintyToken


UNCERTAINTY_BASED_REASON_CODES: set[str] = {
    "high_uncertainty_near_path",
    "unknown_object_uncertainty",
    "partial_occlusion_uncertainty",
    "position_uncertainty_boundary",
    "low_sensor_agreement",
}


def plan_from_uncertainty_aware_tokens(
    entities: list[EntityToken],
    risks: list[RiskToken],
    uncertainties: list[UncertaintyToken],
    events: list[EventToken] | None = None,
) -> PlannerDecision:
    """RiskToken과 UncertaintyToken을 함께 보고 rule-based PlannerDecision을 반환합니다.

    EventToken은 현재 policy에 직접 사용하지 않으며, signature만 향후 비교 확장을 위해 열어 둡니다.
    """

    del entities, events
    near_path_uncertainties = [token for token in uncertainties if _is_near_path(token)]

    unknown_near_path = next((token for token in near_path_uncertainties if token.uncertainty_type == "unknown_object"), None)
    if unknown_near_path is not None:
        return _uncertainty_decision(
            token=unknown_near_path,
            action=Action.ROTATE_RIGHT,
            reason_code="unknown_object_uncertainty",
            reason_text="An unknown object uncertainty is near the path proxy.",
        )

    occlusion_near_path = next(
        (token for token in near_path_uncertainties if token.uncertainty_type == "partial_occlusion"),
        None,
    )
    if occlusion_near_path is not None:
        return _uncertainty_decision(
            token=occlusion_near_path,
            action=Action.ROTATE_RIGHT,
            reason_code="partial_occlusion_uncertainty",
            reason_text="A partially occluded object is near the path proxy.",
        )

    position_boundary = next(
        (
            token
            for token in uncertainties
            if token.uncertainty_type == "position_uncertainty"
            and bool(token.uncertainty_features.get("near_risk_boundary"))
        ),
        None,
    )
    if position_boundary is not None:
        return _uncertainty_decision(
            token=position_boundary,
            action=Action.ROTATE_RIGHT,
            reason_code="position_uncertainty_boundary",
            reason_text="Position uncertainty is close to the configured risk boundary.",
        )

    low_agreement_near_path = next(
        (token for token in near_path_uncertainties if token.uncertainty_type == "low_sensor_agreement"),
        None,
    )
    if low_agreement_near_path is not None:
        return _uncertainty_decision(
            token=low_agreement_near_path,
            action=Action.ROTATE_RIGHT,
            reason_code="low_sensor_agreement",
            reason_text="Low synthetic sensor agreement is near the path proxy.",
        )

    high_near_path = next((token for token in near_path_uncertainties if token.level == "high"), None)
    if high_near_path is not None:
        return _uncertainty_decision(
            token=high_near_path,
            action=Action.STOP,
            reason_code="high_uncertainty_near_path",
            reason_text="A high-level UncertaintyToken is near the path proxy.",
        )

    return _fallback_decision(risks)


def _uncertainty_decision(
    *,
    token: UncertaintyToken,
    action: Action,
    reason_code: str,
    reason_text: str,
) -> PlannerDecision:
    return PlannerDecision(
        planner_name="uncertainty_aware_rast",
        action=action,
        reason_code=reason_code,
        reason_text=reason_text,
        trigger_object_ids=[token.entity_id],
        trigger_token_ids=[token.token_id],
        trigger_features={
            "uncertainty_type": token.uncertainty_type,
            "level": token.level,
            "recommended_action": token.recommended_action,
            "variance": token.variance,
            "sensor_agreement": token.sensor_agreement,
            **token.uncertainty_features,
        },
        confidence=token.confidence,
    )


def _fallback_decision(risks: list[RiskToken]) -> PlannerDecision:
    high_risk = next((risk for risk in risks if risk.severity == "high"), None)
    if high_risk is not None:
        return _risk_fallback_decision(
            risk=high_risk,
            action=Action.STOP,
            reason_text="No uncertainty-specific rule fired, but a high RiskToken is present.",
        )
    if risks:
        return _risk_fallback_decision(
            risk=risks[0],
            action=Action.ROTATE_RIGHT,
            reason_text="No uncertainty-specific rule fired, but a RiskToken is present.",
        )
    return PlannerDecision(
        planner_name="uncertainty_aware_rast",
        action=Action.MOVE_AHEAD,
        reason_code="fallback_no_risk_move_ahead",
        reason_text="No UncertaintyToken or RiskToken requires avoidance.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={"risk_token_count": 0, "uncertainty_triggered": False},
        confidence=1.0,
    )


def _risk_fallback_decision(*, risk: RiskToken, action: Action, reason_text: str) -> PlannerDecision:
    return PlannerDecision(
        planner_name="uncertainty_aware_rast",
        action=action,
        reason_code="fallback_risk_token_present",
        reason_text=reason_text,
        trigger_object_ids=[risk.entity_id],
        trigger_token_ids=[risk.token_id],
        trigger_features={
            "risk_type": risk.risk_type,
            "severity": risk.severity,
            "risk_score": risk.risk_score,
            "uncertainty_triggered": False,
            **risk.risk_features,
        },
        confidence=risk.confidence,
    )


def _is_near_path(token: UncertaintyToken) -> bool:
    return bool(token.uncertainty_features.get("near_path"))

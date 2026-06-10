"""EntityToken/RiskToken 기반 최소 deterministic planner입니다."""

from __future__ import annotations

from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision
from rast.schemas.tokens import EntityToken, RiskToken


def plan_from_tokens(
    entities: list[EntityToken],
    risks: list[RiskToken],
) -> PlannerDecision:
    """RiskToken contract를 사용해 action과 구조화된 선택 근거를 반환합니다."""

    del entities  # MVP-0 policy는 EntityToken 자체보다 RiskToken contract를 우선 사용합니다.
    high_risk = next((risk for risk in risks if risk.severity == "high"), None)
    if high_risk is not None:
        return _decision_from_risk(
            action=Action.STOP,
            reason_code="high_risk_token",
            reason_text="High severity RiskToken is present.",
            risk=high_risk,
        )
    if risks:
        return _decision_from_risk(
            action=Action.ROTATE_RIGHT,
            reason_code="risk_token_present",
            reason_text="RiskToken is present, so planner chooses a conservative turn.",
            risk=risks[0],
        )
    return PlannerDecision(
        planner_name="rast",
        action=Action.MOVE_AHEAD,
        reason_code="no_risk_move_ahead",
        reason_text="No RiskToken is present.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={"risk_token_count": 0},
        confidence=1.0,
    )


def _decision_from_risk(
    *,
    action: Action,
    reason_code: str,
    reason_text: str,
    risk: RiskToken,
) -> PlannerDecision:
    """RiskToken 하나를 action trigger로 기록하는 RAST planner decision을 만듭니다."""

    return PlannerDecision(
        planner_name="rast",
        action=action,
        reason_code=reason_code,
        reason_text=reason_text,
        trigger_object_ids=[risk.entity_id],
        trigger_token_ids=[risk.token_id],
        trigger_features={
            "risk_type": risk.risk_type,
            "severity": risk.severity,
            "risk_score": risk.risk_score,
            **risk.risk_features,
        },
        confidence=risk.confidence,
    )

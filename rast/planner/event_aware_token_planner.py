"""EventToken을 decision reason에 반영하는 실험용 RAST planner입니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision
from rast.schemas.tokens import EntityToken, EventToken, RiskToken


EventPolicyVariant = Literal[
    "full",
    "logging_only",
    "no_risk_changed",
    "no_object_appeared",
    "no_object_moved",
    "no_object_disappeared",
]

VALID_EVENT_POLICY_VARIANTS: tuple[EventPolicyVariant, ...] = (
    "full",
    "logging_only",
    "no_risk_changed",
    "no_object_appeared",
    "no_object_moved",
    "no_object_disappeared",
)

EVENT_BASED_REASON_CODES: set[str] = {
    "event_object_appeared_near_path",
    "event_risk_increased",
    "event_object_moved",
    "event_object_disappeared_clear_path",
}

EVENT_RULE_BY_VARIANT: dict[str, str] = {
    "no_risk_changed": "risk_changed",
    "no_object_appeared": "object_appeared",
    "no_object_moved": "object_moved",
    "no_object_disappeared": "object_disappeared",
}


@dataclass(frozen=True)
class EventAwarePlannerConfig:
    """Event-aware planner ablation 설정입니다."""

    policy_variant: EventPolicyVariant = "full"

    @property
    def disabled_event_rules(self) -> list[str]:
        if self.policy_variant == "logging_only":
            return ["object_appeared", "risk_changed", "object_moved", "object_disappeared"]
        disabled = EVENT_RULE_BY_VARIANT.get(self.policy_variant)
        return [disabled] if disabled is not None else []


def plan_from_event_aware_tokens(
    entities: list[EntityToken],
    risks: list[RiskToken],
    events: list[EventToken],
    *,
    config: EventAwarePlannerConfig | None = None,
    policy_variant: EventPolicyVariant | None = None,
) -> PlannerDecision:
    """Entity/Risk/EventToken을 보고 rule-based PlannerDecision을 반환합니다."""

    planner_config = _resolve_config(config=config, policy_variant=policy_variant)
    del entities  # MVP-0 정책은 EntityToken 자체보다 Risk/EventToken contract를 우선 사용합니다.
    risk_by_entity = {risk.entity_id: risk for risk in risks}

    if planner_config.policy_variant == "logging_only":
        return _with_variant_features(_fallback_decision(risks), planner_config)

    if _rule_enabled("object_appeared", planner_config):
        appeared_decision = _first_object_appeared_near_path(events, risk_by_entity, planner_config)
        if appeared_decision is not None:
            return appeared_decision

    if _rule_enabled("risk_changed", planner_config):
        risk_changed_decision = _first_risk_increase(events, risk_by_entity, planner_config)
        if risk_changed_decision is not None:
            return risk_changed_decision

    if _rule_enabled("object_moved", planner_config):
        moved_decision = _first_moved_object_risk(events, risk_by_entity, planner_config)
        if moved_decision is not None:
            return moved_decision

    if _rule_enabled("object_disappeared", planner_config):
        disappeared_decision = _first_disappeared_clear_path(events, risks, planner_config)
        if disappeared_decision is not None:
            return disappeared_decision

    return _with_variant_features(_fallback_decision(risks), planner_config)


def _first_object_appeared_near_path(
    events: list[EventToken],
    risk_by_entity: dict[str, RiskToken],
    config: EventAwarePlannerConfig,
) -> PlannerDecision | None:
    for event in events:
        if event.event_type != "object_appeared":
            continue
        risk = risk_by_entity.get(event.entity_id)
        if risk is None:
            continue
        return _event_risk_decision(
            event=event,
            risk=risk,
            action=Action.ROTATE_RIGHT,
            reason_code="event_object_appeared_near_path",
            reason_text="A newly appeared object is linked to a current RiskToken.",
            config=config,
        )
    return None


def _first_risk_increase(
    events: list[EventToken],
    risk_by_entity: dict[str, RiskToken],
    config: EventAwarePlannerConfig,
) -> PlannerDecision | None:
    for event in events:
        if event.event_type != "risk_changed":
            continue
        risk = risk_by_entity.get(event.entity_id)
        if risk is None or not _risk_increased(event):
            continue
        action = Action.STOP if risk.severity in {"medium", "high"} else Action.ROTATE_RIGHT
        return _event_risk_decision(
            event=event,
            risk=risk,
            action=action,
            reason_code="event_risk_increased",
            reason_text="A semantic risk change indicates increased risk near the agent.",
            config=config,
        )
    return None


def _first_moved_object_risk(
    events: list[EventToken],
    risk_by_entity: dict[str, RiskToken],
    config: EventAwarePlannerConfig,
) -> PlannerDecision | None:
    for event in events:
        if event.event_type != "object_moved":
            continue
        risk = risk_by_entity.get(event.entity_id)
        if risk is None:
            continue
        return _event_risk_decision(
            event=event,
            risk=risk,
            action=Action.ROTATE_RIGHT,
            reason_code="event_object_moved",
            reason_text="A moved object is currently linked to a RiskToken.",
            config=config,
        )
    return None


def _first_disappeared_clear_path(
    events: list[EventToken],
    risks: list[RiskToken],
    config: EventAwarePlannerConfig,
) -> PlannerDecision | None:
    if risks:
        return None
    for event in events:
        if event.event_type != "object_disappeared":
            continue
        return PlannerDecision(
            planner_name="event_aware_rast",
            action=Action.MOVE_AHEAD,
            reason_code="event_object_disappeared_clear_path",
            reason_text="An object disappeared and no RiskToken remains.",
            trigger_object_ids=[event.entity_id],
            trigger_token_ids=[event.token_id],
            trigger_features={
                "event_types": [event.event_type],
                "event_token_ids": [event.token_id],
                "risk_token_count": 0,
                **_variant_features(config),
            },
            confidence=event.confidence,
        )
    return None


def _fallback_decision(risks: list[RiskToken]) -> PlannerDecision:
    high_risk = next((risk for risk in risks if risk.severity == "high"), None)
    if high_risk is not None:
        return _risk_fallback_decision(
            risk=high_risk,
            action=Action.STOP,
            reason_text="No event-specific rule fired, but a high RiskToken is present.",
        )
    if risks:
        return _risk_fallback_decision(
            risk=risks[0],
            action=Action.ROTATE_RIGHT,
            reason_text="No event-specific rule fired, but a RiskToken is present.",
        )
    return PlannerDecision(
        planner_name="event_aware_rast",
        action=Action.MOVE_AHEAD,
        reason_code="fallback_no_risk_move_ahead",
        reason_text="No EventToken rule or RiskToken requires avoidance.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={"risk_token_count": 0, "event_triggered": False},
        confidence=1.0,
    )


def _risk_fallback_decision(*, risk: RiskToken, action: Action, reason_text: str) -> PlannerDecision:
    return PlannerDecision(
        planner_name="event_aware_rast",
        action=action,
        reason_code="fallback_risk_token_present",
        reason_text=reason_text,
        trigger_object_ids=[risk.entity_id],
        trigger_token_ids=[risk.token_id],
        trigger_features={
            "risk_type": risk.risk_type,
            "severity": risk.severity,
            "risk_score": risk.risk_score,
            "event_triggered": False,
            **risk.risk_features,
        },
        confidence=risk.confidence,
    )


def _event_risk_decision(
    *,
    event: EventToken,
    risk: RiskToken,
    action: Action,
    reason_code: str,
    reason_text: str,
    config: EventAwarePlannerConfig,
) -> PlannerDecision:
    return PlannerDecision(
        planner_name="event_aware_rast",
        action=action,
        reason_code=reason_code,
        reason_text=reason_text,
        trigger_object_ids=[event.entity_id],
        trigger_token_ids=[event.token_id, risk.token_id],
        trigger_features={
            "event_types": [event.event_type],
            "event_token_ids": [event.token_id],
            "risk_token_ids": [risk.token_id],
            "risk_type": risk.risk_type,
            "severity": risk.severity,
            "risk_score": risk.risk_score,
            "previous_state": event.previous_state,
            "current_state": event.current_state,
            **_variant_features(config),
            **risk.risk_features,
        },
        confidence=min(event.confidence, risk.confidence),
    )


def _resolve_config(
    *,
    config: EventAwarePlannerConfig | None,
    policy_variant: EventPolicyVariant | None,
) -> EventAwarePlannerConfig:
    if config is not None and policy_variant is not None and config.policy_variant != policy_variant:
        raise ValueError("config.policy_variant와 policy_variant 인자를 동시에 다르게 지정할 수 없습니다.")
    resolved = config or EventAwarePlannerConfig(policy_variant=policy_variant or "full")
    if resolved.policy_variant not in VALID_EVENT_POLICY_VARIANTS:
        allowed = ", ".join(VALID_EVENT_POLICY_VARIANTS)
        raise ValueError(f"지원하지 않는 event policy variant입니다: {resolved.policy_variant}. 허용값: {allowed}")
    return resolved


def _rule_enabled(event_type: str, config: EventAwarePlannerConfig) -> bool:
    return event_type not in config.disabled_event_rules


def _variant_features(config: EventAwarePlannerConfig) -> dict[str, object]:
    return {
        "event_policy_variant": config.policy_variant,
        "disabled_event_rules": list(config.disabled_event_rules),
    }


def _with_variant_features(decision: PlannerDecision, config: EventAwarePlannerConfig) -> PlannerDecision:
    features = {**decision.trigger_features, **_variant_features(config)}
    return PlannerDecision(
        planner_name=decision.planner_name,
        action=decision.action,
        reason_code=decision.reason_code,
        reason_text=decision.reason_text,
        trigger_object_ids=decision.trigger_object_ids,
        trigger_token_ids=decision.trigger_token_ids,
        trigger_features=features,
        confidence=decision.confidence,
    )


def _risk_increased(event: EventToken) -> bool:
    previous_score = _state_score(event.previous_state)
    current_score = _state_score(event.current_state)
    if event.current_state and not event.previous_state:
        return True
    return current_score >= previous_score


def _state_score(state: dict[str, object]) -> float:
    raw_value = state.get("risk_score", 0.0)
    if raw_value is None:
        return 0.0
    return float(raw_value)

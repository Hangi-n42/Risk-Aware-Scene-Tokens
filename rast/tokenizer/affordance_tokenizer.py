"""ObservationSnapshot?먯꽌 navigation AffordanceToken???앹꽦?⑸땲??"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin

from rast.schemas.observation import ObservationSnapshot
from rast.schemas.tokens import AffordanceToken, EntityToken, EvidenceToken, RelationToken, RiskToken, UncertaintyToken
from rast.tokenizer.relation_tokenizer import DEFAULT_PATH_SEGMENT_ID, path_proxy_features


REGION_PATH_ID = "region:agent_forward_path_proxy"


@dataclass(frozen=True)
class AffordanceTokenizerConfig:
    """Navigation affordance rule threshold瑜??몃? config?먯꽌 二쇱엯?섍린 ?꾪븳 ?ㅼ젙?낅땲??"""

    path_lateral_threshold: float = 0.5
    path_lookahead: float = 2.0
    narrow_passage_width_threshold: float = 1.0
    passable_gap_width_threshold: float = 1.2
    collision_clearance: float = 0.2
    high_failure_risk_threshold: float = 0.67
    path_segment_id: str = DEFAULT_PATH_SEGMENT_ID


def build_affordance_tokens(
    snapshot: ObservationSnapshot,
    entities: list[EntityToken],
    risks: list[RiskToken],
    relations: list[RelationToken],
    uncertainties: list[UncertaintyToken],
    evidence_tokens: list[EvidenceToken] | None = None,
    *,
    config: AffordanceTokenizerConfig | None = None,
) -> list[AffordanceToken]:
    """Navigation-only AffordanceToken???앹꽦?섎뒗 pure function?낅땲??"""

    affordance_config = config or AffordanceTokenizerConfig()
    _validate_config(affordance_config)
    evidence_by_token = _evidence_ids_by_related_token(evidence_tokens or [])
    tokens: list[AffordanceToken] = []

    blocking_relations = [relation for relation in relations if relation.relation == "blocking_path"]
    for relation in blocking_relations:
        tokens.append(
            _token(
                index=len(tokens),
                entity_id=relation.object_id,
                affordance="blocking",
                timestamp=snapshot.step,
                confidence=relation.confidence,
                related_token_ids=[relation.token_id],
                evidence_by_token=evidence_by_token,
                action_hint="avoid_or_rotate",
                navigation_margin=relation.distance_margin,
                failure_risk=0.8,
                features={"source": "blocking_path_relation", **relation.relation_features},
            )
        )

    for risk in risks:
        if risk.severity != "high":
            continue
        tokens.append(
            _token(
                index=len(tokens),
                entity_id=risk.entity_id,
                affordance="avoid_required",
                timestamp=snapshot.step,
                confidence=risk.confidence,
                related_token_ids=[risk.token_id],
                evidence_by_token=evidence_by_token,
                action_hint="rotate_or_stop",
                failure_risk=risk.risk_score,
                features={"source": "high_risk_token", "risk_type": risk.risk_type, "severity": risk.severity, **risk.risk_features},
            )
        )

    for uncertainty in uncertainties:
        if uncertainty.level != "high" or not _uncertainty_near_path(uncertainty):
            continue
        tokens.append(
            _token(
                index=len(tokens),
                entity_id=uncertainty.entity_id,
                affordance="inspect_required",
                timestamp=snapshot.step,
                confidence=uncertainty.confidence,
                related_token_ids=[uncertainty.token_id],
                evidence_by_token=evidence_by_token,
                action_hint="inspect_before_passing",
                failure_risk=None,
                features={
                    "source": "high_uncertainty_near_path",
                    "uncertainty_type": uncertainty.uncertainty_type,
                    "level": uncertainty.level,
                    **uncertainty.uncertainty_features,
                },
            )
        )

    for relation in relations:
        if relation.relation != "target_reachable":
            continue
        tokens.append(
            _token(
                index=len(tokens),
                entity_id=relation.object_id,
                affordance="target_reachable",
                timestamp=snapshot.step,
                confidence=relation.confidence,
                related_token_ids=[relation.token_id],
                evidence_by_token=evidence_by_token,
                action_hint="move_ahead_to_goal",
                navigation_margin=relation.distance_margin,
                failure_risk=0.0,
                features={"source": "target_reachable_relation", **relation.relation_features},
            )
        )

    passage = _passage_features(snapshot, entities, affordance_config)
    has_blocking_or_avoid = any(token.affordance in {"blocking", "avoid_required"} for token in tokens)
    if not has_blocking_or_avoid and passage["gap_width"] is not None:
        gap_width = float(passage["gap_width"])
        if affordance_config.collision_clearance * 2 < gap_width <= affordance_config.narrow_passage_width_threshold:
            tokens.append(
                _token(
                    index=len(tokens),
                    entity_id=REGION_PATH_ID,
                    affordance="narrow_passage",
                    timestamp=snapshot.step,
                    confidence=1.0,
                    related_token_ids=[],
                    evidence_by_token=evidence_by_token,
                    action_hint="move_ahead_with_caution",
                    navigation_margin=gap_width,
                    failure_risk=0.4,
                    features={**passage, "source": "gap_width_rule"},
                )
            )
        elif gap_width >= affordance_config.passable_gap_width_threshold:
            tokens.append(
                _token(
                    index=len(tokens),
                    entity_id=REGION_PATH_ID,
                    affordance="passable",
                    timestamp=snapshot.step,
                    confidence=1.0,
                    related_token_ids=[],
                    evidence_by_token=evidence_by_token,
                    action_hint="move_ahead",
                    navigation_margin=gap_width,
                    failure_risk=0.0,
                    features={**passage, "source": "gap_width_rule"},
                )
            )
    elif not has_blocking_or_avoid and not _has_inspect_required(tokens) and _path_is_clear(snapshot, entities, affordance_config):
        tokens.append(
            _token(
                index=len(tokens),
                entity_id=REGION_PATH_ID,
                affordance="passable",
                timestamp=snapshot.step,
                confidence=1.0,
                related_token_ids=[],
                evidence_by_token=evidence_by_token,
                action_hint="move_ahead",
                navigation_margin=affordance_config.path_lateral_threshold,
                failure_risk=0.0,
                features={"source": "clear_path_rule", "path_segment_id": affordance_config.path_segment_id},
            )
        )

    return tokens


def _token(
    *,
    index: int,
    entity_id: str,
    affordance: str,
    timestamp: int,
    confidence: float,
    related_token_ids: list[str],
    evidence_by_token: dict[str, list[str]],
    action_hint: str,
    navigation_margin: float | None = None,
    failure_risk: float | None = None,
    features: dict[str, object] | None = None,
) -> AffordanceToken:
    evidence_ids = [evidence_id for token_id in related_token_ids for evidence_id in evidence_by_token.get(token_id, [])]
    return AffordanceToken(
        token_id=f"aff_{index:04d}",
        entity_id=entity_id,
        affordance=affordance,  # type: ignore[arg-type]
        confidence=confidence,
        timestamp=timestamp,
        preconditions=["navigation_affordance_only"],
        action_hint=action_hint,
        navigation_margin=navigation_margin,
        failure_risk=failure_risk,
        related_token_ids=related_token_ids,
        evidence_token_ids=evidence_ids,
        affordance_features=features or {},
    )


def _passage_features(
    snapshot: ObservationSnapshot,
    entities: list[EntityToken],
    config: AffordanceTokenizerConfig,
) -> dict[str, object]:
    signed_laterals: list[float] = []
    for entity in entities:
        features = path_proxy_features(
            agent_position=snapshot.agent_state.position,
            agent_yaw_degrees=_agent_yaw_degrees(snapshot),
            object_position=entity.position,
            distance_to_agent=entity.distance_to_agent,
            lookahead=config.path_lookahead,
        )
        if not features.is_ahead or not features.within_lookahead:
            continue
        signed_lateral = _signed_lateral(
            snapshot=snapshot,
            object_position=entity.position,
        )
        if abs(signed_lateral) <= max(config.passable_gap_width_threshold, config.narrow_passage_width_threshold):
            signed_laterals.append(signed_lateral)

    left = [value for value in signed_laterals if value < 0]
    right = [value for value in signed_laterals if value > 0]
    if not left or not right:
        return {
            "gap_width": None,
            "left_boundary": min(left) if left else None,
            "right_boundary": max(right) if right else None,
            "path_segment_id": config.path_segment_id,
        }
    left_boundary = max(left)
    right_boundary = min(right)
    return {
        "gap_width": right_boundary - left_boundary,
        "left_boundary": left_boundary,
        "right_boundary": right_boundary,
        "path_segment_id": config.path_segment_id,
    }


def _path_is_clear(
    snapshot: ObservationSnapshot,
    entities: list[EntityToken],
    config: AffordanceTokenizerConfig,
) -> bool:
    for entity in entities:
        features = path_proxy_features(
            agent_position=snapshot.agent_state.position,
            agent_yaw_degrees=_agent_yaw_degrees(snapshot),
            object_position=entity.position,
            distance_to_agent=entity.distance_to_agent,
            lookahead=config.path_lookahead,
        )
        if features.is_ahead and features.within_lookahead and features.lateral_distance <= config.path_lateral_threshold:
            return False
    return True


def _signed_lateral(*, snapshot: ObservationSnapshot, object_position) -> float:
    yaw = radians(_agent_yaw_degrees(snapshot))
    dx = object_position.x - snapshot.agent_state.position.x
    dz = object_position.z - snapshot.agent_state.position.z
    return (dx * cos(yaw)) - (dz * sin(yaw))


def _agent_yaw_degrees(snapshot: ObservationSnapshot) -> float:
    if snapshot.agent_state.rotation is None:
        return 0.0
    return snapshot.agent_state.rotation.y


def _uncertainty_near_path(token: UncertaintyToken) -> bool:
    return bool(token.uncertainty_features.get("near_path"))


def _has_inspect_required(tokens: list[AffordanceToken]) -> bool:
    return any(token.affordance == "inspect_required" for token in tokens)


def _evidence_ids_by_related_token(evidence_tokens: list[EvidenceToken]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for evidence in evidence_tokens:
        for token_id in evidence.related_token_ids:
            mapping.setdefault(token_id, []).append(evidence.token_id)
    return mapping


def _validate_config(config: AffordanceTokenizerConfig) -> None:
    if config.path_lateral_threshold < 0:
        raise ValueError("path_lateral_threshold??0 ?댁긽?댁뼱???⑸땲??")
    if config.path_lookahead <= 0:
        raise ValueError("path_lookahead??0蹂대떎 而ㅼ빞 ?⑸땲??")
    if config.narrow_passage_width_threshold <= config.collision_clearance * 2:
        raise ValueError("narrow_passage_width_threshold??collision clearance蹂대떎 而ㅼ빞 ?⑸땲??")
    if config.passable_gap_width_threshold <= 0:
        raise ValueError("passable_gap_width_threshold??0蹂대떎 而ㅼ빞 ?⑸땲??")

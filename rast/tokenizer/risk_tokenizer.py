"""EntityToken에서 MVP-0 near-agent RiskToken을 생성합니다."""

from __future__ import annotations

from dataclasses import dataclass

from rast.schemas.tokens import EntityToken, RiskToken


@dataclass(frozen=True)
class RiskTokenizerConfig:
    """Risk threshold를 코드 본문에 고정하지 않기 위한 설정 객체입니다."""

    near_agent_threshold: float
    high_severity_score: float = 0.67
    medium_severity_score: float = 0.34
    risk_type: str = "near_agent_obstacle"


def build_risk_tokens(
    entities: list[EntityToken],
    *,
    config: RiskTokenizerConfig,
) -> list[RiskToken]:
    """가까운 entity에 대해서만 near-agent RiskToken을 생성합니다."""

    if config.near_agent_threshold <= 0:
        raise ValueError("near_agent_threshold는 0보다 커야 합니다.")

    risks: list[RiskToken] = []
    for index, entity in enumerate(entities):
        if entity.distance_to_agent > config.near_agent_threshold:
            continue

        risk_score = distance_risk_score(
            distance_to_agent=entity.distance_to_agent,
            threshold=config.near_agent_threshold,
        )
        risks.append(
            RiskToken(
                token_id=f"risk_{index:04d}",
                risk_type=config.risk_type,
                severity=severity_from_score(risk_score, config=config),
                entity_id=entity.entity_id,
                affected_area={
                    "agent_radius": config.near_agent_threshold,
                    "entity_distance_to_agent": entity.distance_to_agent,
                },
                confidence=entity.confidence,
                risk_score=risk_score,
                recommended_policy="stop_or_turn",
                risk_features={
                    "distance_to_agent": entity.distance_to_agent,
                    "near_agent_threshold": config.near_agent_threshold,
                },
                timestamp=entity.timestamp,
            )
        )
    return risks


def distance_risk_score(*, distance_to_agent: float, threshold: float) -> float:
    """거리 기반 risk score입니다. 가까울수록 1.0에 가까워집니다."""

    if threshold <= 0:
        raise ValueError("threshold는 0보다 커야 합니다.")
    raw_score = 1.0 - (distance_to_agent / threshold)
    return min(1.0, max(0.0, raw_score))


def severity_from_score(score: float, *, config: RiskTokenizerConfig) -> str:
    """Risk score를 low/medium/high severity로 변환합니다."""

    if score >= config.high_severity_score:
        return "high"
    if score >= config.medium_severity_score:
        return "medium"
    return "low"

"""Synthetic metadata uncertainty를 UncertaintyToken으로 변환합니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rast.baselines.flat_feature_table import distance_to_path_proxy
from rast.schemas.observation import ObjectMetadata, ObservationSnapshot
from rast.schemas.tokens import UncertaintyToken
from rast.tokenizer.entity_tokenizer import object_distance_to_agent


@dataclass(frozen=True)
class UncertaintyTokenizerConfig:
    """UncertaintyToken 생성 threshold를 runner/config에서 주입하기 위한 설정입니다."""

    classification_uncertainty_threshold: float = 0.5
    position_variance_threshold: float = 0.2
    occlusion_ratio_threshold: float = 0.5
    sensor_agreement_threshold: float = 0.6
    path_lateral_threshold: float = 0.5
    risk_threshold: float = 1.5
    risk_boundary_margin: float = 0.25


def build_uncertainty_tokens(
    snapshot: ObservationSnapshot,
    *,
    config: UncertaintyTokenizerConfig,
    visible_only: bool = True,
) -> list[UncertaintyToken]:
    """ObservationSnapshot의 synthetic uncertainty metadata에서 UncertaintyToken을 생성합니다.

    이 tokenizer는 실제 perception uncertainty calibration이 아니라 WindowsMetadataSim의
    deterministic metadata field를 사용하는 Phase 1 oracle/synthetic 경로입니다.
    """

    _validate_config(config)
    tokens: list[UncertaintyToken] = []
    for obj in snapshot.objects:
        if visible_only and obj.visible is False:
            continue
        tokens.extend(_tokens_for_object(obj, snapshot, config=config, start_index=len(tokens)))
    return tokens


def _tokens_for_object(
    obj: ObjectMetadata,
    snapshot: ObservationSnapshot,
    *,
    config: UncertaintyTokenizerConfig,
    start_index: int,
) -> list[UncertaintyToken]:
    tokens: list[UncertaintyToken] = []
    base_features = _base_features(obj, snapshot, config=config)
    if obj.is_unknown or obj.category.lower().startswith("unknown"):
        tokens.append(
            _make_token(
                obj,
                snapshot,
                index=start_index + len(tokens),
                uncertainty_type="unknown_object",
                level="high",
                recommended_action="treat_as_risk" if base_features["near_path"] else "inspect_before_passing",
                features=base_features,
            )
        )
    if obj.classification_uncertainty >= config.classification_uncertainty_threshold:
        tokens.append(
            _make_token(
                obj,
                snapshot,
                index=start_index + len(tokens),
                uncertainty_type="classification_uncertainty",
                level=_level_from_high_value(obj.classification_uncertainty, high=0.7, medium=config.classification_uncertainty_threshold),
                recommended_action="inspect_before_passing",
                features=base_features | {"classification_uncertainty": obj.classification_uncertainty},
            )
        )
    if obj.position_variance >= config.position_variance_threshold:
        boundary_margin = abs(base_features["distance_to_agent"] - config.risk_threshold)
        tokens.append(
            _make_token(
                obj,
                snapshot,
                index=start_index + len(tokens),
                uncertainty_type="position_uncertainty",
                level=_level_from_high_value(obj.position_variance, high=0.35, medium=config.position_variance_threshold),
                recommended_action="replan_around" if boundary_margin <= config.risk_boundary_margin else "slow_down",
                variance=obj.position_variance,
                features=base_features
                | {
                    "position_variance": obj.position_variance,
                    "risk_boundary_margin": boundary_margin,
                    "near_risk_boundary": boundary_margin <= config.risk_boundary_margin,
                },
            )
        )
    if obj.occlusion_ratio >= config.occlusion_ratio_threshold:
        tokens.append(
            _make_token(
                obj,
                snapshot,
                index=start_index + len(tokens),
                uncertainty_type="partial_occlusion",
                level=_level_from_high_value(obj.occlusion_ratio, high=0.7, medium=config.occlusion_ratio_threshold),
                recommended_action="inspect_before_passing" if base_features["near_path"] else "slow_down",
                features=base_features | {"occlusion_ratio": obj.occlusion_ratio},
            )
        )
    if obj.sensor_agreement <= config.sensor_agreement_threshold:
        tokens.append(
            _make_token(
                obj,
                snapshot,
                index=start_index + len(tokens),
                uncertainty_type="low_sensor_agreement",
                level=_level_from_low_value(obj.sensor_agreement, high=0.4, medium=config.sensor_agreement_threshold),
                recommended_action="inspect_before_passing" if base_features["near_path"] else "slow_down",
                sensor_agreement=obj.sensor_agreement,
                features=base_features | {"sensor_agreement": obj.sensor_agreement},
            )
        )
    return tokens


def _make_token(
    obj: ObjectMetadata,
    snapshot: ObservationSnapshot,
    *,
    index: int,
    uncertainty_type: Literal[
        "classification_uncertainty",
        "position_uncertainty",
        "partial_occlusion",
        "low_sensor_agreement",
        "unknown_object",
    ],
    level: Literal["low", "medium", "high"],
    recommended_action: Literal["proceed", "slow_down", "inspect_before_passing", "replan_around", "treat_as_risk"],
    features: dict[str, object],
    variance: float | None = None,
    sensor_agreement: float | None = None,
) -> UncertaintyToken:
    return UncertaintyToken(
        token_id=f"unc_{index:04d}",
        uncertainty_type=uncertainty_type,
        entity_id=obj.object_id,
        level=level,
        confidence=obj.classification_confidence,
        variance=variance,
        possible_categories=list(obj.possible_categories),
        recommended_action=recommended_action,
        sensor_agreement=sensor_agreement,
        uncertainty_features=features,
        timestamp=snapshot.step,
    )


def _base_features(
    obj: ObjectMetadata,
    snapshot: ObservationSnapshot,
    *,
    config: UncertaintyTokenizerConfig,
) -> dict[str, object]:
    distance = object_distance_to_agent(obj, snapshot.agent_state.position)
    path_distance = distance_to_path_proxy(obj, snapshot)
    return {
        "category": obj.category,
        "distance_to_agent": distance,
        "distance_to_path_proxy": path_distance,
        "path_lateral_threshold": config.path_lateral_threshold,
        "risk_threshold": config.risk_threshold,
        "near_path": path_distance <= config.path_lateral_threshold,
        "within_risk_threshold": distance <= config.risk_threshold,
        "classification_confidence": obj.classification_confidence,
    }


def _level_from_high_value(value: float, *, high: float, medium: float) -> Literal["low", "medium", "high"]:
    if value >= high:
        return "high"
    if value >= medium:
        return "medium"
    return "low"


def _level_from_low_value(value: float, *, high: float, medium: float) -> Literal["low", "medium", "high"]:
    if value <= high:
        return "high"
    if value <= medium:
        return "medium"
    return "low"


def _validate_config(config: UncertaintyTokenizerConfig) -> None:
    if not 0 <= config.classification_uncertainty_threshold <= 1:
        raise ValueError("classification_uncertainty_threshold는 0과 1 사이여야 합니다.")
    if config.position_variance_threshold < 0:
        raise ValueError("position_variance_threshold는 0 이상이어야 합니다.")
    if not 0 <= config.occlusion_ratio_threshold <= 1:
        raise ValueError("occlusion_ratio_threshold는 0과 1 사이여야 합니다.")
    if not 0 <= config.sensor_agreement_threshold <= 1:
        raise ValueError("sensor_agreement_threshold는 0과 1 사이여야 합니다.")
    if config.path_lateral_threshold < 0:
        raise ValueError("path_lateral_threshold는 0 이상이어야 합니다.")
    if config.risk_threshold <= 0:
        raise ValueError("risk_threshold는 0보다 커야 합니다.")
    if config.risk_boundary_margin < 0:
        raise ValueError("risk_boundary_margin은 0 이상이어야 합니다.")

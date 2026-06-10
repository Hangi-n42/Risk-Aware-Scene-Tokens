"""Flat Feature Table baseline의 deterministic planner입니다."""

from __future__ import annotations

from dataclasses import dataclass

from rast.baselines.flat_feature_table import FlatFeatureRow
from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision


@dataclass(frozen=True)
class FlatFeaturePlannerConfig:
    """Flat Feature planner가 scalar risk를 해석할 때 쓰는 설정입니다."""

    risk_score_threshold: float = 0.34
    use_within_risk_threshold: bool = True


def plan_from_flat_features(
    rows: list[FlatFeatureRow],
    *,
    config: FlatFeaturePlannerConfig | None = None,
) -> PlannerDecision:
    """토큰 contract 없이 scalar feature만 보고 action과 선택 근거를 반환합니다."""

    planner_config = config or FlatFeaturePlannerConfig()
    if planner_config.risk_score_threshold < 0 or planner_config.risk_score_threshold > 1:
        raise ValueError("risk_score_threshold는 0 이상 1 이하이어야 합니다.")

    for row in rows:
        if planner_config.use_within_risk_threshold and row.within_risk_threshold:
            return _decision_from_row(
                row=row,
                action=Action.ROTATE_RIGHT,
                reason_code="within_risk_threshold",
                reason_text="Flat feature row is within risk threshold.",
                config=planner_config,
            )
        if row.risk_score_scalar >= planner_config.risk_score_threshold:
            return _decision_from_row(
                row=row,
                action=Action.ROTATE_RIGHT,
                reason_code="high_risk_score_scalar",
                reason_text="Flat feature risk score scalar exceeds threshold.",
                config=planner_config,
            )

    return PlannerDecision(
        planner_name="flat_feature",
        action=Action.MOVE_AHEAD,
        reason_code="no_risk_scalar_move_ahead",
        reason_text="No flat feature row crosses the scalar risk rule.",
        trigger_object_ids=[],
        trigger_token_ids=[],
        trigger_features={
            "row_count": len(rows),
            "risk_score_threshold": planner_config.risk_score_threshold,
            "use_within_risk_threshold": planner_config.use_within_risk_threshold,
        },
        confidence=1.0,
    )


def _decision_from_row(
    *,
    row: FlatFeatureRow,
    action: Action,
    reason_code: str,
    reason_text: str,
    config: FlatFeaturePlannerConfig,
) -> PlannerDecision:
    """Flat Feature row 하나를 action trigger로 기록합니다."""

    return PlannerDecision(
        planner_name="flat_feature",
        action=action,
        reason_code=reason_code,
        reason_text=reason_text,
        trigger_object_ids=[row.object_id],
        trigger_token_ids=[],
        trigger_features={
            "risk_score_scalar": row.risk_score_scalar,
            "within_risk_threshold": row.within_risk_threshold,
            "distance_to_agent": row.distance_to_agent,
            "distance_to_path_proxy": row.distance_to_path_proxy,
            "risk_score_threshold": config.risk_score_threshold,
        },
        confidence=row.confidence,
    )

"""Baseline information-bound audit helper입니다."""

from __future__ import annotations

from pydantic import Field

from rast.schemas.common import RASTBaseModel


class BaselineAudit(RASTBaseModel):
    """Baseline이 접근 가능한 field와 금지 field를 기록합니다."""

    baseline_type: str = Field(description="Baseline 이름입니다.")
    accessible_fields: list[str] = Field(description="Baseline이 사용할 수 있는 field입니다.")
    forbidden_fields: list[str] = Field(description="Baseline이 보면 안 되는 RAST-only field입니다.")
    input_unit_count: int | None = Field(default=None, ge=0, description="해당 baseline 입력 단위 수입니다.")


def object_list_audit(*, input_unit_count: int | None = None) -> BaselineAudit:
    """Object List baseline의 accessible/forbidden contract입니다."""

    return BaselineAudit(
        baseline_type="object_list",
        accessible_fields=[
            "object_id",
            "category",
            "position",
            "visible",
            "distance_to_agent",
            "confidence",
        ],
        forbidden_fields=[
            "risk_score",
            "recommended_policy",
            "risk_type",
            "severity",
            "token_type",
        ],
        input_unit_count=input_unit_count,
    )


def flat_feature_table_audit(*, input_unit_count: int | None = None) -> BaselineAudit:
    """Flat Feature Table baseline의 accessible/forbidden contract입니다."""

    return BaselineAudit(
        baseline_type="flat_feature_table",
        accessible_fields=[
            "object_id",
            "category",
            "x",
            "y",
            "z",
            "visible",
            "distance_to_agent",
            "distance_to_path_proxy",
            "object_size_proxy",
            "is_unknown",
            "risk_score_scalar",
            "within_risk_threshold",
            "confidence",
        ],
        forbidden_fields=[
            "token_type",
            "risk_type",
            "severity",
            "recommended_policy",
            "evidence_pointer",
            "event_type",
        ],
        input_unit_count=input_unit_count,
    )


def rast_audit(*, input_unit_count: int | None = None) -> BaselineAudit:
    """RAST token contract가 접근하는 field 목록을 기록합니다."""

    return BaselineAudit(
        baseline_type="rast",
        accessible_fields=[
            "token_type",
            "entity_id",
            "category",
            "position",
            "distance_to_agent",
            "confidence",
            "risk_type",
            "severity",
            "risk_score",
            "recommended_policy",
        ],
        forbidden_fields=[],
        input_unit_count=input_unit_count,
    )


def audit_for_baseline(baseline_type: str, *, input_unit_count: int | None = None) -> BaselineAudit:
    """baseline 이름으로 audit contract를 조회합니다."""

    if baseline_type == "object_list":
        return object_list_audit(input_unit_count=input_unit_count)
    if baseline_type == "flat_feature_table":
        return flat_feature_table_audit(input_unit_count=input_unit_count)
    if baseline_type == "rast":
        return rast_audit(input_unit_count=input_unit_count)
    raise ValueError(f"지원하지 않는 baseline_type입니다: {baseline_type}")

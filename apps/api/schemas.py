"""FastAPI 요청/응답에 사용하는 얇은 API schema입니다."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SUPPORTED_POLICIES = (
    "object_list",
    "flat_feature",
    "scene_graph",
    "rast",
    "event_aware_rast",
    "uncertainty_aware_rast",
    "affordance_aware_rast",
)

SUPPORTED_UPDATE_MODES = ("full_recompute", "incremental")

PolicyName = Literal[
    "object_list",
    "flat_feature",
    "scene_graph",
    "rast",
    "event_aware_rast",
    "uncertainty_aware_rast",
    "affordance_aware_rast",
]
UpdateMode = Literal["full_recompute", "incremental"]


class RunScenarioRequest(BaseModel):
    """WindowsMetadataSim scenario를 API에서 짧게 실행하기 위한 요청입니다."""

    scenario: str = Field(default="clear_path", description="실행할 WindowsMetadataSim scenario 이름입니다.")
    apply_policy: PolicyName = Field(default="rast", description="simulator에 적용할 planner policy입니다.")
    max_steps: int = Field(default=5, ge=1, le=50, description="API demo에서 실행할 최대 step 수입니다.")
    update_mode: UpdateMode = Field(default="full_recompute", description="token update mode입니다.")

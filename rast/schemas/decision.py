"""Planner action 선택 근거를 기록하는 decision schema입니다."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from rast.planner.actions import Action
from rast.schemas.common import RASTBaseModel


class PlannerDecision(RASTBaseModel):
    """각 planner가 선택한 action과 그 근거를 함께 담는 구조화된 결정 기록입니다."""

    planner_name: str = Field(description="decision을 생성한 planner 이름입니다.")
    action: Action = Field(description="planner가 선택한 공통 action입니다.")
    reason_code: str = Field(description="action 선택 사유를 기계적으로 집계하기 위한 코드입니다.")
    reason_text: str = Field(description="사람이 읽을 수 있는 짧은 action 선택 설명입니다.")
    trigger_object_ids: list[str] = Field(default_factory=list, description="action을 유발한 object id 목록입니다.")
    trigger_token_ids: list[str] = Field(default_factory=list, description="action을 유발한 token id 목록입니다.")
    trigger_features: dict[str, Any] = Field(default_factory=dict, description="action 선택에 사용된 주요 feature 값입니다.")
    confidence: float = Field(default=1.0, ge=0, le=1, description="rule-based decision confidence입니다.")

    @property
    def value(self) -> str:
        """기존 Action 반환 경로와의 호환을 위해 action.value를 노출합니다."""

        return self.action.value

    def __str__(self) -> str:
        return self.value

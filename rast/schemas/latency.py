"""RAST latency accounting schema입니다."""

from __future__ import annotations

from pydantic import Field

from rast.schemas.common import RASTBaseModel


class LatencyRecord(RASTBaseModel):
    """PRD의 end-to-end latency breakdown을 보존합니다."""

    observation: float = Field(ge=0, description="Observation 수집 또는 snapshot 생성 시간(ms)입니다.")
    perception: float = Field(
        ge=0,
        description="Perception adapter 시간(ms)입니다. Phase 1에서는 실제 perception latency로 해석하지 않습니다.",
    )
    token_generation: float = Field(ge=0, description="Token generation 시간(ms)입니다.")
    planning: float = Field(ge=0, description="Planner action 결정 시간(ms)입니다.")
    action: float = Field(ge=0, description="Action 생성 또는 전송 시간(ms)입니다.")
    total: float = Field(ge=0, description="전체 decision loop latency(ms)입니다.")

    @classmethod
    def from_stages(
        cls,
        *,
        observation: float = 0.0,
        perception: float = 0.0,
        token_generation: float = 0.0,
        planning: float = 0.0,
        action: float = 0.0,
    ) -> "LatencyRecord":
        """Stage 값의 합으로 total을 계산합니다."""

        total = observation + perception + token_generation + planning + action
        return cls(
            observation=observation,
            perception=perception,
            token_generation=token_generation,
            planning=planning,
            action=action,
            total=total,
        )

    def stage_sum(self) -> float:
        """total을 제외한 stage 합계를 반환합니다."""

        return self.observation + self.perception + self.token_generation + self.planning + self.action

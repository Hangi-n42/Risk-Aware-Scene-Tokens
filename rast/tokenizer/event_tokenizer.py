"""TokenMemory diff 결과를 EventToken으로 변환합니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rast.schemas.tokens import EventToken
from rast.token_memory.diff import diff_states


@dataclass(frozen=True)
class EventTokenizerConfig:
    """Event 감지 threshold를 runner/config에서 주입할 수 있게 분리한 설정입니다."""

    movement_threshold: float = 0.1
    risk_score_delta_threshold: float = 0.1


def build_event_tokens(
    previous_state: dict[str, Any] | None,
    current_state: dict[str, Any],
    *,
    config: EventTokenizerConfig | None = None,
    timestamp: int | float | None = None,
) -> list[EventToken]:
    """previous/current state diff를 EventToken list로 변환합니다."""

    resolved_config = config or EventTokenizerConfig()
    candidates = diff_states(
        previous_state,
        current_state,
        movement_threshold=resolved_config.movement_threshold,
        risk_score_delta_threshold=resolved_config.risk_score_delta_threshold,
    )
    return [
        EventToken(
            token_id=f"evt_{index:04d}",
            event_type=candidate.event_type,
            entity_id=candidate.entity_id,
            previous_state=candidate.previous_state,
            current_state=candidate.current_state,
            severity=candidate.severity,
            confidence=candidate.confidence,
            timestamp=timestamp,
        )
        for index, candidate in enumerate(candidates)
    ]

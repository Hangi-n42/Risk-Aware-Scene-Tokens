"""이전 step의 token 상태를 보관하는 최소 Token Memory입니다."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class TokenMemory:
    """EventToken 생성을 위해 직전 step 상태만 보관합니다.

    MVP-0에서는 full recomputation 최적화를 구현하지 않고, semantic event logging에 필요한
    previous/current state 비교 계약만 제공합니다.
    """

    def __init__(self) -> None:
        self._previous_state: dict[str, Any] | None = None
        self.current_step: int = 0

    def reset(self) -> None:
        """저장된 이전 상태와 step counter를 초기화합니다."""

        self._previous_state = None
        self.current_step = 0

    def get_previous_state(self) -> dict[str, Any] | None:
        """직전 step 상태의 복사본을 반환합니다."""

        if self._previous_state is None:
            return None
        return deepcopy(self._previous_state)

    def update(self, current_state: dict[str, Any]) -> None:
        """현재 step 상태를 다음 step의 previous state로 저장합니다."""

        self._previous_state = deepcopy(current_state)
        self.current_step += 1

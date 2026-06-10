"""Simulator 없이 사용할 수 있는 latency timing utility입니다."""

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

from rast.schemas.latency import LatencyRecord


LATENCY_STAGES = ("observation", "perception", "token_generation", "planning", "action")
MIN_BENEFIT_DENOMINATOR_MS = 1e-9


def incremental_update_benefit(*, full_recompute_latency_ms: float, incremental_update_latency_ms: float) -> float:
    """full recompute 대비 incremental update latency benefit을 안전하게 계산합니다."""

    if full_recompute_latency_ms <= MIN_BENEFIT_DENOMINATOR_MS:
        return 0.0
    return 1.0 - (incremental_update_latency_ms / full_recompute_latency_ms)


class LatencyTimer:
    """`time.perf_counter()` 기반 stage timer입니다."""

    def __init__(self) -> None:
        self._elapsed_ms: dict[str, float] = {}

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        """지정한 stage의 elapsed time을 ms 단위로 기록합니다."""

        self._validate_stage(name)
        start = perf_counter()
        try:
            yield
        finally:
            self._elapsed_ms[name] = (perf_counter() - start) * 1000.0

    def record_stage(self, name: str, elapsed_ms: float) -> None:
        """테스트와 외부 측정값 주입을 위해 stage 시간을 직접 기록합니다."""

        self._validate_stage(name)
        if elapsed_ms < 0:
            raise ValueError("latency는 음수가 될 수 없습니다.")
        self._elapsed_ms[name] = elapsed_ms

    def to_record(self) -> LatencyRecord:
        """누락된 stage는 0ms로 채워 LatencyRecord를 생성합니다."""

        values = {stage: self._elapsed_ms.get(stage, 0.0) for stage in LATENCY_STAGES}
        return LatencyRecord.from_stages(**values)

    def to_dict(self) -> dict[str, float]:
        """LatencyRecord와 같은 key 구조의 dict를 반환합니다."""

        return self.to_record().to_dict()

    @staticmethod
    def _validate_stage(name: str) -> None:
        if name not in LATENCY_STAGES:
            allowed = ", ".join(LATENCY_STAGES)
            raise ValueError(f"지원하지 않는 latency stage입니다: {name}. 허용값: {allowed}")

import pytest

from rast.evaluation.latency import LatencyTimer
from rast.schemas.latency import LatencyRecord


def test_latency_record_computes_total_from_stages() -> None:
    record = LatencyRecord.from_stages(
        observation=1.0,
        perception=2.0,
        token_generation=3.0,
        planning=4.0,
        action=5.0,
    )

    assert record.total == 15.0
    assert record.stage_sum() == 15.0


def test_latency_timer_records_direct_stage_values() -> None:
    timer = LatencyTimer()
    timer.record_stage("observation", 1.0)
    timer.record_stage("perception", 2.0)
    timer.record_stage("token_generation", 3.0)
    timer.record_stage("planning", 4.0)
    timer.record_stage("action", 5.0)

    record = timer.to_record()

    assert record.total == 15.0
    assert record.token_generation == 3.0


def test_latency_timer_context_manager_records_stage() -> None:
    timer = LatencyTimer()

    with timer.stage("planning"):
        pass

    record = timer.to_record()

    assert record.planning >= 0.0
    assert record.total >= record.planning


def test_latency_timer_rejects_unknown_stage() -> None:
    timer = LatencyTimer()

    with pytest.raises(ValueError):
        timer.record_stage("unknown", 1.0)

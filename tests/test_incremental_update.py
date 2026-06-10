from rast.evaluation.latency import incremental_update_benefit
from rast.token_memory.incremental_update import changed_object_ids_from_states


def test_changed_object_ids_detects_disappeared_object() -> None:
    previous = {
        "objects": {
            "Box|1": {"position": {"x": 0.0, "y": 0.0, "z": 1.0}},
            "Sofa|1": {"position": {"x": 2.0, "y": 0.0, "z": 2.0}},
        },
        "risks": {},
    }
    current = {
        "objects": {
            "Sofa|1": {"position": {"x": 2.0, "y": 0.0, "z": 2.0}},
        },
        "risks": {},
    }

    changed = changed_object_ids_from_states(
        previous,
        current,
        movement_threshold=0.1,
        risk_score_delta_threshold=0.1,
    )

    assert changed == ("Box|1",)


def test_incremental_update_benefit_handles_zero_full_latency() -> None:
    benefit = incremental_update_benefit(full_recompute_latency_ms=0.0, incremental_update_latency_ms=0.1)

    assert benefit == 0.0


def test_incremental_update_benefit_can_be_negative_when_incremental_is_slower() -> None:
    benefit = incremental_update_benefit(full_recompute_latency_ms=1.0, incremental_update_latency_ms=2.0)

    assert benefit == -1.0

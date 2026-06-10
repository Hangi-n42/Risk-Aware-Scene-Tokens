from rast.planner.actions import Action
from rast.simulator.windows_scenarios import build_windows_scenario
from rast.token_memory.memory import TokenMemory
from rast.tokenizer.event_tokenizer import EventTokenizerConfig, build_event_tokens
from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig


def test_object_appeared_event_is_created() -> None:
    previous = {"objects": {}, "risks": {}}
    current = {"objects": {"Box|1": {"position": {"x": 0.0, "y": 0.0, "z": 1.0}}}, "risks": {}}

    events = build_event_tokens(previous, current, config=EventTokenizerConfig(), timestamp=1)

    assert [event.event_type for event in events] == ["object_appeared"]
    assert events[0].entity_id == "Box|1"


def test_object_disappeared_event_is_created() -> None:
    previous = {"objects": {"Box|1": {"position": {"x": 0.0, "y": 0.0, "z": 1.0}}}, "risks": {}}
    current = {"objects": {}, "risks": {}}

    events = build_event_tokens(previous, current, config=EventTokenizerConfig(), timestamp=1)

    assert [event.event_type for event in events] == ["object_disappeared"]


def test_object_moved_event_uses_position_threshold() -> None:
    previous = {"objects": {"Box|1": {"position": {"x": 0.0, "y": 0.0, "z": 1.0}}}, "risks": {}}
    current = {"objects": {"Box|1": {"position": {"x": 0.0, "y": 0.0, "z": 1.3}}}, "risks": {}}

    events = build_event_tokens(
        previous,
        current,
        config=EventTokenizerConfig(movement_threshold=0.2),
        timestamp=1,
    )

    assert [event.event_type for event in events] == ["object_moved"]


def test_risk_changed_event_is_created_from_presence_change() -> None:
    previous = {"objects": {"Box|1": {}}, "risks": {}}
    current = {
        "objects": {"Box|1": {}},
        "risks": {"Box|1": {"risk_score": 0.7, "severity": "high", "confidence": 1.0}},
    }

    events = build_event_tokens(previous, current, config=EventTokenizerConfig(), timestamp=1)

    assert [event.event_type for event in events] == ["risk_changed"]
    assert events[0].severity == "high"


def test_windows_object_appears_scenario_generates_event_token() -> None:
    event_types = event_types_after_one_step("object_appears")

    assert "object_appeared" in event_types


def test_windows_object_moves_scenario_generates_event_token() -> None:
    event_types = event_types_after_one_step("object_moves")

    assert "object_moved" in event_types


def test_windows_risk_increases_scenario_generates_event_token() -> None:
    event_types = event_types_after_one_step("risk_increases")

    assert "risk_changed" in event_types


def test_windows_object_disappears_scenario_generates_event_token() -> None:
    event_types = event_types_after_one_step("object_disappears")

    assert "object_disappeared" in event_types


def event_types_after_one_step(scenario_name: str) -> list[str]:
    scenario = build_windows_scenario(scenario_name)
    memory = TokenMemory()
    risk_config = RiskTokenizerConfig(near_agent_threshold=scenario.risk_threshold)

    snapshot_0 = scenario.simulator.snapshot(episode_id="event_scenario_test")
    first = tokenize_snapshot(
        snapshot_0,
        risk_config=risk_config,
        token_memory=memory,
        enable_events=True,
    )
    scenario.simulator.step(Action.STOP)
    snapshot_1 = scenario.simulator.snapshot(episode_id="event_scenario_test")
    second = tokenize_snapshot(
        snapshot_1,
        risk_config=risk_config,
        token_memory=memory,
        enable_events=True,
    )

    assert first.events == []
    return [event.event_type for event in second.events]

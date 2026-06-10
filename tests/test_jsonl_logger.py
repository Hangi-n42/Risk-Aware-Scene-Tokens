from rast.evaluation.jsonl_logger import JSONLLogger
from rast.evaluation.records import StepLogRecord
from rast.schemas.latency import LatencyRecord
from rast.schemas.tokens import EntityToken
from rast.schemas.common import Vector3


def test_jsonl_logger_appends_step_log_record(tmp_path) -> None:
    logger = JSONLLogger(tmp_path / "run.jsonl")
    latency = LatencyRecord.from_stages(
        observation=1.0,
        perception=0.0,
        token_generation=2.0,
        planning=3.0,
        action=4.0,
    )
    token = EntityToken(
        token_id="ent_1",
        entity_id="Chair|1",
        category="chair",
        position=Vector3(x=1.0, y=0.0, z=2.0),
        distance_to_agent=2.2,
    )
    record = StepLogRecord.from_parts(
        run_id="run_001",
        episode_id="episode_001",
        scene_id="FloorPlan1",
        step=1,
        baseline_type="rast",
        latency=latency,
        selected_action="MoveAhead",
        tokens=[token],
    )

    logger.append(record)
    rows = logger.read_all()

    assert len(rows) == 1
    assert rows[0]["run_id"] == "run_001"
    assert rows[0]["episode_id"] == "episode_001"
    assert rows[0]["scene_id"] == "FloorPlan1"
    assert rows[0]["step"] == 1
    assert rows[0]["baseline_type"] == "rast"
    assert rows[0]["selected_action"] == "MoveAhead"
    assert rows[0]["latency"]["total"] == 10.0
    assert rows[0]["tokens"][0]["type"] == "EntityToken"

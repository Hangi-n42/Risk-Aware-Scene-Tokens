from rast.token_memory.memory import TokenMemory


def test_token_memory_stores_previous_state_copy() -> None:
    memory = TokenMemory()
    state = {"objects": {"obj_1": {"position": {"x": 0.0, "y": 0.0, "z": 1.0}}}, "risks": {}}

    memory.update(state)
    state["objects"]["obj_1"]["position"]["z"] = 99.0

    previous = memory.get_previous_state()

    assert previous is not None
    assert previous["objects"]["obj_1"]["position"]["z"] == 1.0
    assert memory.current_step == 1


def test_token_memory_reset_clears_state() -> None:
    memory = TokenMemory()
    memory.update({"objects": {"obj_1": {}}, "risks": {}})

    memory.reset()

    assert memory.get_previous_state() is None
    assert memory.current_step == 0

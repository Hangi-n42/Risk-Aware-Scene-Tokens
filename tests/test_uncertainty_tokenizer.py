from rast.simulator.windows_scenarios import build_windows_scenario
from rast.tokenizer.uncertainty_tokenizer import UncertaintyTokenizerConfig, build_uncertainty_tokens


def token_types_for_scenario(name: str) -> set[str]:
    scenario = build_windows_scenario(name)
    snapshot = scenario.simulator.snapshot(episode_id=f"test_{name}")
    tokens = build_uncertainty_tokens(
        snapshot,
        config=UncertaintyTokenizerConfig(risk_threshold=scenario.risk_threshold),
    )
    return {token.uncertainty_type for token in tokens}


def test_unknown_object_generates_unknown_uncertainty() -> None:
    token_types = token_types_for_scenario("unknown_uncertain_object")

    assert "unknown_object" in token_types
    assert "classification_uncertainty" in token_types


def test_occlusion_ratio_generates_partial_occlusion() -> None:
    token_types = token_types_for_scenario("partially_occluded_obstacle")

    assert "partial_occlusion" in token_types


def test_position_variance_generates_position_uncertainty() -> None:
    token_types = token_types_for_scenario("noisy_position_boundary")

    assert "position_uncertainty" in token_types


def test_low_sensor_agreement_generates_uncertainty_token() -> None:
    token_types = token_types_for_scenario("low_sensor_agreement")

    assert "low_sensor_agreement" in token_types


def test_uncertainty_without_high_risk_has_uncertainty_token() -> None:
    scenario = build_windows_scenario("uncertainty_without_high_risk")
    snapshot = scenario.simulator.snapshot(episode_id="uncertainty_without_high_risk_test")
    tokens = build_uncertainty_tokens(
        snapshot,
        config=UncertaintyTokenizerConfig(risk_threshold=scenario.risk_threshold),
    )

    assert tokens
    assert any(token.level == "high" for token in tokens)

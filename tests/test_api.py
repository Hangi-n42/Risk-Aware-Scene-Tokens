"""FastAPI 제출용 demo surface의 최소 동작 테스트입니다."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "rast-api", "version": "1.0.0"}


def test_scenarios_returns_non_empty_list() -> None:
    response = client.get("/api/scenarios")

    assert response.status_code == 200
    assert response.json()["scenarios"]


def test_policies_include_rast() -> None:
    response = client.get("/api/policies")

    assert response.status_code == 200
    assert "rast" in response.json()["policies"]


def test_run_scenario_returns_summary() -> None:
    response = client.post(
        "/api/run-scenario",
        json={
            "scenario": "clear_path",
            "apply_policy": "rast",
            "max_steps": 3,
            "update_mode": "full_recompute",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["scenario"] == "clear_path"
    assert payload["apply_policy"] == "rast"
    assert payload["selected_action"]
    assert payload["planner_decision_summary"]["reason_code"]
    assert set(payload["token_counts"]) >= {
        "entity",
        "risk",
        "relation",
        "event",
        "uncertainty",
        "evidence",
        "affordance",
    }
    assert payload["replay_trace_preview"]


def test_metrics_returns_plain_text() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "total_api_requests" in response.text
    assert "scenario_runs_total" in response.text


def test_root_ui_returns_html() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "<html" in response.text
    assert "RAST MVP-0 Demo" in response.text

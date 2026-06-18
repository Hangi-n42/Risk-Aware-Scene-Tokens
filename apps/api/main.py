"""RAST MVP-0 제출용 FastAPI demo app입니다."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

from apps.api.schemas import RunScenarioRequest
from apps.api.service import latest_report_summaries, list_policies, list_scenarios, run_scenario_summary


APP_VERSION = "1.0.0"
STATIC_DIR = Path(__file__).resolve().parent / "static"
STARTED_AT = perf_counter()
TOTAL_API_REQUESTS = 0
SCENARIO_RUNS_TOTAL = 0
LAST_RUN_LATENCY_MS = 0.0

app = FastAPI(
    title="RAST MVP-0 API",
    version=APP_VERSION,
    description="WindowsMetadataSim metadata-only RAST MVP-0 demo API입니다.",
)


@app.middleware("http")
async def count_api_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
    """간단한 plain-text metrics를 위해 request count를 기록합니다."""

    global TOTAL_API_REQUESTS
    TOTAL_API_REQUESTS += 1
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
def root_ui() -> str:
    """plain HTML demo UI를 반환합니다."""

    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rast-api", "version": APP_VERSION}


@app.get("/api/scenarios")
def scenarios() -> dict[str, list[str]]:
    return {"scenarios": list_scenarios()}


@app.get("/api/policies")
def policies() -> dict[str, list[str]]:
    return {"policies": list_policies()}


@app.post("/api/run-scenario")
def run_scenario(request: RunScenarioRequest) -> dict[str, object]:
    """WindowsMetadataSim scenario를 실행하고 RAST 요약 결과를 반환합니다."""

    global SCENARIO_RUNS_TOTAL, LAST_RUN_LATENCY_MS
    start = perf_counter()
    try:
        result = run_scenario_summary(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    LAST_RUN_LATENCY_MS = (perf_counter() - start) * 1000.0
    SCENARIO_RUNS_TOTAL += 1
    return result


@app.get("/api/reports/latest")
def reports_latest() -> dict[str, object]:
    return {"reports": latest_report_summaries()}


@app.get("/metrics")
def metrics() -> Response:
    uptime = perf_counter() - STARTED_AT
    body = "\n".join(
        [
            "# TYPE total_api_requests counter",
            f"total_api_requests {TOTAL_API_REQUESTS}",
            "# TYPE scenario_runs_total counter",
            f"scenario_runs_total {SCENARIO_RUNS_TOTAL}",
            "# TYPE last_run_latency_ms gauge",
            f"last_run_latency_ms {LAST_RUN_LATENCY_MS:.6f}",
            "# TYPE app_uptime_seconds gauge",
            f"app_uptime_seconds {uptime:.6f}",
            "",
        ]
    )
    return Response(content=body, media_type="text/plain; version=0.0.4")

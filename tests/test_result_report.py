import csv
from pathlib import Path

from rast.evaluation.report import generate_result_report, write_result_report


def write_fake_aggregate_results(path: Path) -> None:
    fieldnames = [
        "suite_run_id",
        "scenario",
        "seed",
        "apply_policy",
        "risk_threshold",
        "near_miss_threshold",
        "collision_threshold",
        "success",
        "goal_reached",
        "completed_steps",
        "collision_count",
        "near_miss_count",
        "baseline_disagreement_count",
        "rast_vs_object_list_disagreement_count",
        "rast_vs_flat_feature_disagreement_count",
        "object_list_vs_flat_feature_disagreement_count",
        "token_count_avg",
        "object_count_avg",
        "flat_feature_row_count_avg",
        "latency_avg_ms",
        "latency_p50_ms",
        "latency_p95_ms",
        "token_generation_latency_avg_ms",
        "planning_latency_avg_ms",
        "total_latency_avg_ms",
        "status",
    ]
    rows = [
        {
            "suite_run_id": "suite_test",
            "scenario": "clear_path",
            "seed": "0",
            "apply_policy": "rast",
            "risk_threshold": "1.5",
            "near_miss_threshold": "1.0",
            "collision_threshold": "0.2",
            "success": "True",
            "goal_reached": "False",
            "completed_steps": "10",
            "collision_count": "0",
            "near_miss_count": "0",
            "baseline_disagreement_count": "0",
            "rast_vs_object_list_disagreement_count": "0",
            "rast_vs_flat_feature_disagreement_count": "0",
            "object_list_vs_flat_feature_disagreement_count": "0",
            "token_count_avg": "2.0",
            "object_count_avg": "2.0",
            "flat_feature_row_count_avg": "2.0",
            "latency_avg_ms": "0.2",
            "latency_p50_ms": "0.2",
            "latency_p95_ms": "0.3",
            "token_generation_latency_avg_ms": "0.05",
            "planning_latency_avg_ms": "0.04",
            "total_latency_avg_ms": "0.2",
            "status": "success",
        },
        {
            "suite_run_id": "suite_test",
            "scenario": "planner_disagreement",
            "seed": "0",
            "apply_policy": "object_list",
            "risk_threshold": "1.5",
            "near_miss_threshold": "1.0",
            "collision_threshold": "0.2",
            "success": "True",
            "goal_reached": "False",
            "completed_steps": "10",
            "collision_count": "0",
            "near_miss_count": "3",
            "baseline_disagreement_count": "7",
            "rast_vs_object_list_disagreement_count": "7",
            "rast_vs_flat_feature_disagreement_count": "0",
            "object_list_vs_flat_feature_disagreement_count": "7",
            "token_count_avg": "2.0",
            "object_count_avg": "1.0",
            "flat_feature_row_count_avg": "1.0",
            "latency_avg_ms": "0.25",
            "latency_p50_ms": "0.24",
            "latency_p95_ms": "0.4",
            "token_generation_latency_avg_ms": "0.06",
            "planning_latency_avg_ms": "0.05",
            "total_latency_avg_ms": "0.25",
            "status": "success",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_generate_result_report_markdown_contains_required_sections_and_limits(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    write_fake_aggregate_results(results_path)

    markdown = generate_result_report(results_path=results_path)

    assert "WindowsMetadataSim" in markdown
    assert "deterministic metadata simulator" in markdown
    assert "does not support real-world performance claims" in markdown
    assert "## Baselines" in markdown
    assert "## EventToken Summary" in markdown
    assert "## Incremental Update Summary" in markdown
    assert "## Decision Trace Summary" in markdown
    assert "EventToken does not affect planner action" in markdown
    assert "incremental update optimization is experimental" in markdown
    assert "rule-based planner explanations" in markdown
    assert "## Limitations" in markdown


def test_write_result_report_creates_output_file(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results.csv"
    output_path = tmp_path / "docs" / "result_report.md"
    write_fake_aggregate_results(results_path)

    write_result_report(results_path=results_path, output_path=output_path)

    assert output_path.exists()
    assert "RAST MVP-0 Result Report" in output_path.read_text(encoding="utf-8")


def test_generate_result_report_summarizes_event_fields(tmp_path: Path) -> None:
    results_path = tmp_path / "aggregate_results_with_events.csv"
    fieldnames = [
        "suite_run_id",
        "scenario",
        "seed",
        "apply_policy",
        "risk_threshold",
        "near_miss_threshold",
        "collision_threshold",
        "success",
        "goal_reached",
        "completed_steps",
        "collision_count",
        "near_miss_count",
        "baseline_disagreement_count",
        "rast_vs_object_list_disagreement_count",
        "rast_vs_flat_feature_disagreement_count",
        "object_list_vs_flat_feature_disagreement_count",
        "token_count_avg",
        "object_count_avg",
        "flat_feature_row_count_avg",
        "event_token_count_total",
        "event_token_count_avg",
        "event_type_counts",
        "update_mode",
        "changed_object_count_avg",
        "affected_token_count_avg",
        "full_recompute_latency_avg_ms",
        "incremental_update_latency_avg_ms",
        "incremental_update_benefit_avg",
        "rast_reason_code_counts",
        "object_list_reason_code_counts",
        "flat_feature_reason_code_counts",
        "rast_trigger_token_count_total",
        "decision_trace_coverage",
        "latency_avg_ms",
        "latency_p50_ms",
        "latency_p95_ms",
        "token_generation_latency_avg_ms",
        "planning_latency_avg_ms",
        "total_latency_avg_ms",
        "status",
    ]
    rows = [
        {
            "suite_run_id": "suite_test",
            "scenario": "object_appears",
            "seed": "0",
            "apply_policy": "rast",
            "risk_threshold": "1.5",
            "near_miss_threshold": "1.0",
            "collision_threshold": "0.2",
            "success": "True",
            "goal_reached": "False",
            "completed_steps": "5",
            "collision_count": "0",
            "near_miss_count": "1",
            "baseline_disagreement_count": "0",
            "rast_vs_object_list_disagreement_count": "0",
            "rast_vs_flat_feature_disagreement_count": "0",
            "object_list_vs_flat_feature_disagreement_count": "0",
            "token_count_avg": "3.0",
            "object_count_avg": "2.0",
            "flat_feature_row_count_avg": "2.0",
            "event_token_count_total": "2",
            "event_token_count_avg": "0.4",
            "event_type_counts": '{"object_appeared": 1, "risk_changed": 1}',
            "update_mode": "incremental",
            "changed_object_count_avg": "1.0",
            "affected_token_count_avg": "2.0",
            "full_recompute_latency_avg_ms": "0.2",
            "incremental_update_latency_avg_ms": "0.1",
            "incremental_update_benefit_avg": "0.5",
            "rast_reason_code_counts": '{"high_risk_token": 1, "no_risk_move_ahead": 4}',
            "object_list_reason_code_counts": '{"near_object_distance": 1, "no_near_object_move_ahead": 4}',
            "flat_feature_reason_code_counts": '{"within_risk_threshold": 1, "no_risk_scalar_move_ahead": 4}',
            "rast_trigger_token_count_total": "1",
            "decision_trace_coverage": "1.0",
            "latency_avg_ms": "0.3",
            "latency_p50_ms": "0.3",
            "latency_p95_ms": "0.4",
            "token_generation_latency_avg_ms": "0.08",
            "planning_latency_avg_ms": "0.05",
            "total_latency_avg_ms": "0.3",
            "status": "success",
        }
    ]
    with results_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    markdown = generate_result_report(results_path=results_path)

    assert "## EventToken Summary" in markdown
    assert "EventToken included in this report: yes" in markdown
    assert "semantic event" in markdown
    assert "object_appeared" in markdown
    assert "risk_changed" in markdown
    assert "does not affect planner action" in markdown
    assert "## Incremental Update Summary" in markdown
    assert "incremental update optimization is experimental" in markdown
    assert "incremental" in markdown
    assert "## Decision Trace Summary" in markdown
    assert "high_risk_token" in markdown
    assert "decision_trace_coverage" in markdown
    assert "does not affect planner action" in markdown

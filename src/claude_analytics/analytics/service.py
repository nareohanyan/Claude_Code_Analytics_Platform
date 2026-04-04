from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import text

from claude_analytics.analytics.schemas import (
    AdoptionBreakdown,
    ErrorSummary,
    ModelSummary,
    OverviewKPIs,
    PeakUsageHour,
    SessionHighlight,
    ToolSummary,
    UsageTrendPoint,
)
from claude_analytics.db.session import create_session_factory


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


class AnalyticsService:
    """Reusable analytics queries over the normalized PostgreSQL schema."""

    def __init__(self, database_url: str) -> None:
        self._session_factory = create_session_factory(database_url)

    def get_overview_kpis(self) -> OverviewKPIs:
        query = text(
            """
            WITH api_errors AS (
                SELECT COUNT(*)::int AS total_api_errors
                FROM events
                WHERE event_name = 'api_error'
            ),
            api_requests AS (
                SELECT COUNT(*)::int AS total_api_requests
                FROM events
                WHERE event_name = 'api_request'
            )
            SELECT
                (SELECT COUNT(*)::int FROM employees) AS total_employees,
                (SELECT COUNT(DISTINCT user_email)::int FROM sessions) AS active_users,
                (SELECT COUNT(*)::int FROM sessions) AS total_sessions,
                (SELECT COUNT(*)::int FROM events) AS total_events,
                (SELECT COALESCE(ROUND(SUM(cost_usd)::numeric, 2), 0) FROM events WHERE event_name = 'api_request') AS total_cost_usd,
                (SELECT COALESCE(SUM(input_tokens), 0)::bigint FROM events WHERE event_name = 'api_request') AS total_input_tokens,
                (SELECT COALESCE(SUM(output_tokens), 0)::bigint FROM events WHERE event_name = 'api_request') AS total_output_tokens,
                api_errors.total_api_errors,
                COALESCE(ROUND((api_errors.total_api_errors::numeric / NULLIF(api_requests.total_api_requests, 0)) * 100, 2), 0) AS api_error_rate_pct
            FROM api_errors, api_requests
            """
        )
        with self._session_factory() as session:
            row = session.execute(query).mappings().one()
        return OverviewKPIs(
            total_employees=row["total_employees"],
            active_users=row["active_users"],
            total_sessions=row["total_sessions"],
            total_events=row["total_events"],
            total_cost_usd=_to_float(row["total_cost_usd"]),
            total_input_tokens=row["total_input_tokens"],
            total_output_tokens=row["total_output_tokens"],
            total_api_errors=row["total_api_errors"],
            api_error_rate_pct=_to_float(row["api_error_rate_pct"]),
        )

    def get_adoption_by_dimension(self, dimension: str) -> list[AdoptionBreakdown]:
        allowed_dimensions = {
            "practice": "employee_practice",
            "level": "employee_level",
            "location": "employee_location",
            "terminal": "terminal_type",
            "os": "os_type",
        }
        if dimension not in allowed_dimensions:
            valid = ", ".join(sorted(allowed_dimensions))
            raise ValueError(f"Unsupported dimension '{dimension}'. Expected one of: {valid}")

        column_name = allowed_dimensions[dimension]
        query = text(
            f"""
            SELECT
                COALESCE({column_name}, 'Unknown') AS dimension,
                COUNT(DISTINCT user_email)::int AS active_users,
                COUNT(DISTINCT session_id)::int AS total_sessions,
                COUNT(*)::int AS total_events,
                COALESCE(ROUND(SUM(cost_usd)::numeric, 2), 0) AS total_cost_usd
            FROM event_facts
            GROUP BY 1
            ORDER BY total_cost_usd DESC, total_events DESC
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query).mappings().all()
        return [
            AdoptionBreakdown(
                dimension=row["dimension"],
                active_users=row["active_users"],
                total_sessions=row["total_sessions"],
                total_events=row["total_events"],
                total_cost_usd=_to_float(row["total_cost_usd"]),
            )
            for row in rows
        ]

    def get_daily_usage_trend(self) -> list[UsageTrendPoint]:
        query = text(
            """
            SELECT
                event_date::text AS event_date,
                COUNT(DISTINCT user_email)::int AS active_users,
                COUNT(DISTINCT session_id)::int AS total_sessions,
                COUNT(*)::int AS total_events,
                COALESCE(ROUND(SUM(cost_usd)::numeric, 2), 0) AS total_cost_usd,
                COALESCE(SUM(input_tokens), 0)::bigint AS total_input_tokens,
                COALESCE(SUM(output_tokens), 0)::bigint AS total_output_tokens
            FROM events
            GROUP BY event_date
            ORDER BY event_date
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query).mappings().all()
        return [
            UsageTrendPoint(
                event_date=row["event_date"],
                active_users=row["active_users"],
                total_sessions=row["total_sessions"],
                total_events=row["total_events"],
                total_cost_usd=_to_float(row["total_cost_usd"]),
                total_input_tokens=row["total_input_tokens"],
                total_output_tokens=row["total_output_tokens"],
            )
            for row in rows
        ]

    def get_model_summary(self) -> list[ModelSummary]:
        query = text(
            """
            SELECT
                model,
                COUNT(*)::int AS api_requests,
                COALESCE(ROUND(SUM(cost_usd)::numeric, 2), 0) AS total_cost_usd,
                COALESCE(SUM(input_tokens), 0)::bigint AS total_input_tokens,
                COALESCE(SUM(output_tokens), 0)::bigint AS total_output_tokens,
                COALESCE(ROUND(AVG(duration_ms)::numeric, 2), 0) AS avg_duration_ms
            FROM events
            WHERE event_name = 'api_request'
            GROUP BY model
            ORDER BY total_cost_usd DESC, api_requests DESC
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query).mappings().all()
        return [
            ModelSummary(
                model=row["model"],
                api_requests=row["api_requests"],
                total_cost_usd=_to_float(row["total_cost_usd"]),
                total_input_tokens=row["total_input_tokens"],
                total_output_tokens=row["total_output_tokens"],
                avg_duration_ms=_to_float(row["avg_duration_ms"]),
            )
            for row in rows
        ]

    def get_tool_summary(self) -> list[ToolSummary]:
        query = text(
            """
            WITH decisions AS (
                SELECT
                    tool_name,
                    COUNT(*)::int AS tool_decisions,
                    COUNT(*) FILTER (WHERE decision = 'accept')::int AS accepted_decisions,
                    COUNT(*) FILTER (WHERE decision = 'reject')::int AS rejected_decisions
                FROM events
                WHERE event_name = 'tool_decision' AND tool_name IS NOT NULL
                GROUP BY tool_name
            ),
            results AS (
                SELECT
                    tool_name,
                    COUNT(*)::int AS tool_results,
                    COALESCE(ROUND(AVG(duration_ms)::numeric, 2), 0) AS avg_duration_ms,
                    COALESCE(ROUND(AVG(CASE WHEN tool_success THEN 1.0 ELSE 0.0 END)::numeric * 100, 2), 0) AS success_rate_pct
                FROM events
                WHERE event_name = 'tool_result' AND tool_name IS NOT NULL
                GROUP BY tool_name
            )
            SELECT
                COALESCE(decisions.tool_name, results.tool_name) AS tool_name,
                COALESCE(decisions.tool_decisions, 0) AS tool_decisions,
                COALESCE(decisions.accepted_decisions, 0) AS accepted_decisions,
                COALESCE(decisions.rejected_decisions, 0) AS rejected_decisions,
                COALESCE(results.tool_results, 0) AS tool_results,
                COALESCE(results.success_rate_pct, 0) AS success_rate_pct,
                COALESCE(results.avg_duration_ms, 0) AS avg_duration_ms
            FROM decisions
            FULL OUTER JOIN results
                ON decisions.tool_name = results.tool_name
            ORDER BY tool_decisions DESC, tool_results DESC
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query).mappings().all()
        return [
            ToolSummary(
                tool_name=row["tool_name"],
                tool_decisions=row["tool_decisions"],
                accepted_decisions=row["accepted_decisions"],
                rejected_decisions=row["rejected_decisions"],
                tool_results=row["tool_results"],
                success_rate_pct=_to_float(row["success_rate_pct"]),
                avg_duration_ms=_to_float(row["avg_duration_ms"]),
            )
            for row in rows
        ]

    def get_error_summary(self, limit: int = 10) -> list[ErrorSummary]:
        query = text(
            """
            SELECT
                COALESCE(status_code, 'unknown') AS status_code,
                COALESCE(error_message, 'Unknown error') AS error_message,
                COUNT(*)::int AS error_count
            FROM events
            WHERE event_name = 'api_error'
            GROUP BY 1, 2
            ORDER BY error_count DESC, status_code
            LIMIT :limit
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query, {"limit": limit}).mappings().all()
        return [
            ErrorSummary(
                status_code=row["status_code"],
                error_message=row["error_message"],
                error_count=row["error_count"],
            )
            for row in rows
        ]

    def get_peak_usage_hours(self) -> list[PeakUsageHour]:
        query = text(
            """
            SELECT
                event_hour,
                COUNT(DISTINCT user_email)::int AS active_users,
                COUNT(DISTINCT session_id)::int AS total_sessions,
                COUNT(*)::int AS total_events
            FROM events
            GROUP BY event_hour
            ORDER BY event_hour
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query).mappings().all()
        return [
            PeakUsageHour(
                event_hour=row["event_hour"],
                active_users=row["active_users"],
                total_sessions=row["total_sessions"],
                total_events=row["total_events"],
            )
            for row in rows
        ]

    def get_top_sessions(self, limit: int = 10) -> list[SessionHighlight]:
        query = text(
            """
            SELECT
                session_id,
                user_email,
                employee_practice,
                total_events,
                total_cost_usd,
                session_duration_ms
            FROM session_facts
            ORDER BY total_cost_usd DESC, total_events DESC
            LIMIT :limit
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query, {"limit": limit}).mappings().all()
        return [
            SessionHighlight(
                session_id=row["session_id"],
                user_email=row["user_email"],
                employee_practice=row["employee_practice"],
                total_events=row["total_events"],
                total_cost_usd=_to_float(row["total_cost_usd"]),
                session_duration_ms=row["session_duration_ms"],
            )
            for row in rows
        ]

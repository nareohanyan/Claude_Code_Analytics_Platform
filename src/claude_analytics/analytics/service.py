from __future__ import annotations

from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text

from claude_analytics.analytics.schemas import (
    AdoptionBreakdown,
    ErrorSummary,
    ModelSummary,
    OverviewKPIs,
    PeakUsageHour,
    PredictiveAnomaly,
    PredictiveForecast,
    PredictivePoint,
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


PREDICTIVE_METRIC_LABELS: dict[str, str] = {
    "total_cost_usd": "Daily API Cost (USD)",
    "api_requests": "Daily API Requests",
    "total_tokens": "Daily Tokens",
    "api_errors": "Daily API Errors",
}


class AnalyticsService:
    """Reusable analytics queries over the normalized PostgreSQL schema."""

    def __init__(self, database_url: str) -> None:
        self._session_factory = create_session_factory(database_url)

    def _get_daily_predictive_frame(self) -> pd.DataFrame:
        query = text(
            """
            SELECT
                event_date::date AS event_date,
                COALESCE(SUM(cost_usd), 0)::double precision AS total_cost_usd,
                COUNT(*) FILTER (WHERE event_name = 'api_request')::int AS api_requests,
                COALESCE(SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)), 0)::bigint AS total_tokens,
                COUNT(*) FILTER (WHERE event_name = 'api_error')::int AS api_errors
            FROM events
            GROUP BY event_date
            ORDER BY event_date
            """
        )
        with self._session_factory() as session:
            rows = session.execute(query).mappings().all()
        frame = pd.DataFrame(rows)
        if frame.empty:
            return frame
        frame["event_date"] = pd.to_datetime(frame["event_date"])
        return frame

    @staticmethod
    def _fit_trend_with_weekday(
        dates: pd.Series,
        values: pd.Series,
    ) -> tuple[float, float, dict[int, float]]:
        x = np.arange(len(values), dtype=float)
        y = values.astype(float).to_numpy()

        if len(y) == 1:
            slope = 0.0
            intercept = float(y[0])
        else:
            slope, intercept = np.polyfit(x, y, 1)

        trend = intercept + slope * x
        residuals = y - trend
        weekday_effects = (
            pd.DataFrame({"weekday": dates.dt.weekday, "residual": residuals})
            .groupby("weekday", dropna=False)["residual"]
            .mean()
            .to_dict()
        )
        return float(slope), float(intercept), {int(k): float(v) for k, v in weekday_effects.items()}

    @staticmethod
    def _predict_with_weekday(
        dates: pd.Series,
        start_index: int,
        slope: float,
        intercept: float,
        weekday_effects: dict[int, float],
    ) -> np.ndarray:
        x = np.arange(start_index, start_index + len(dates), dtype=float)
        trend = intercept + slope * x
        weekday = dates.dt.weekday.to_numpy()
        adjustments = np.array([weekday_effects.get(int(day), 0.0) for day in weekday], dtype=float)
        return np.maximum(trend + adjustments, 0.0)

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

    def get_predictive_forecast(
        self,
        metric: str = "total_cost_usd",
        *,
        horizon_days: int = 7,
        backtest_days: int = 7,
    ) -> PredictiveForecast:
        if metric not in PREDICTIVE_METRIC_LABELS:
            valid = ", ".join(sorted(PREDICTIVE_METRIC_LABELS))
            raise ValueError(f"Unsupported metric '{metric}'. Expected one of: {valid}")
        if horizon_days < 1:
            raise ValueError("horizon_days must be >= 1")
        if backtest_days < 1:
            raise ValueError("backtest_days must be >= 1")

        frame = self._get_daily_predictive_frame()
        if frame.empty:
            raise ValueError("No daily telemetry data available for forecasting.")

        series = frame[["event_date", metric]].rename(columns={metric: "value"}).copy()
        series["value"] = series["value"].astype(float)
        total_days = len(series)
        if total_days < 10:
            raise ValueError("At least 10 daily points are required for predictive analytics.")

        effective_backtest = min(backtest_days, max(1, total_days - 3))
        split_index = total_days - effective_backtest

        train = series.iloc[:split_index].reset_index(drop=True)
        test = series.iloc[split_index:].reset_index(drop=True)

        slope_train, intercept_train, weekday_train = self._fit_trend_with_weekday(
            train["event_date"],
            train["value"],
        )
        test_predictions = self._predict_with_weekday(
            test["event_date"],
            start_index=len(train),
            slope=slope_train,
            intercept=intercept_train,
            weekday_effects=weekday_train,
        )

        test_actual = test["value"].to_numpy(dtype=float)
        mae = float(np.mean(np.abs(test_actual - test_predictions)))
        non_zero_mask = test_actual != 0
        if np.any(non_zero_mask):
            mape_pct = float(
                np.mean(
                    np.abs((test_actual[non_zero_mask] - test_predictions[non_zero_mask]) / test_actual[non_zero_mask])
                )
                * 100
            )
        else:
            mape_pct = 0.0

        slope_full, intercept_full, weekday_full = self._fit_trend_with_weekday(
            series["event_date"],
            series["value"],
        )
        full_predictions = self._predict_with_weekday(
            series["event_date"],
            start_index=0,
            slope=slope_full,
            intercept=intercept_full,
            weekday_effects=weekday_full,
        )

        future_dates = pd.Series(
            pd.date_range(
                start=series["event_date"].iloc[-1] + pd.Timedelta(days=1),
                periods=horizon_days,
                freq="D",
            )
        )
        future_predictions = self._predict_with_weekday(
            future_dates,
            start_index=total_days,
            slope=slope_full,
            intercept=intercept_full,
            weekday_effects=weekday_full,
        )

        history_window = min(30, max(0, split_index))
        history_start = split_index - history_window
        points: list[PredictivePoint] = []
        for index in range(history_start, split_index):
            points.append(
                PredictivePoint(
                    date=series.iloc[index]["event_date"].date().isoformat(),
                    actual=round(float(series.iloc[index]["value"]), 4),
                    predicted=round(float(full_predictions[index]), 4),
                    split="history",
                )
            )
        for idx, row in test.iterrows():
            points.append(
                PredictivePoint(
                    date=row["event_date"].date().isoformat(),
                    actual=round(float(row["value"]), 4),
                    predicted=round(float(test_predictions[idx]), 4),
                    split="backtest",
                )
            )
        for idx, date_value in enumerate(future_dates):
            points.append(
                PredictivePoint(
                    date=date_value.date().isoformat(),
                    actual=None,
                    predicted=round(float(future_predictions[idx]), 4),
                    split="forecast",
                )
            )

        residuals = series["value"].to_numpy(dtype=float) - full_predictions
        residual_std = float(np.std(residuals))
        anomalies: list[PredictiveAnomaly] = []
        if residual_std > 0:
            z_scores = residuals / residual_std
            anomaly_candidates: list[tuple[int, float]] = [
                (idx, float(z_scores[idx])) for idx in range(total_days) if abs(z_scores[idx]) >= 2.0
            ]
            anomaly_candidates.sort(key=lambda pair: abs(pair[1]), reverse=True)
            for idx, z_score in anomaly_candidates[:10]:
                actual_value = float(series.iloc[idx]["value"])
                predicted_value = float(full_predictions[idx])
                anomalies.append(
                    PredictiveAnomaly(
                        date=series.iloc[idx]["event_date"].date().isoformat(),
                        actual=round(actual_value, 4),
                        predicted=round(predicted_value, 4),
                        z_score=round(z_score, 4),
                        abs_error=round(abs(actual_value - predicted_value), 4),
                    )
                )

        return PredictiveForecast(
            metric=metric,
            metric_label=PREDICTIVE_METRIC_LABELS[metric],
            horizon_days=horizon_days,
            backtest_days=effective_backtest,
            train_days=len(train),
            mae=round(mae, 4),
            mape_pct=round(mape_pct, 4),
            trend_slope_per_day=round(float(slope_full), 6),
            last_actual_value=round(float(series.iloc[-1]["value"]), 4),
            last_predicted_value=round(float(future_predictions[-1]), 4),
            points=points,
            anomalies=anomalies,
        )

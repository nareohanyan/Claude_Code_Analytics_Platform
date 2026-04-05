from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from claude_analytics.analytics import AnalyticsService
from claude_analytics.config import AppConfig


def _frame(rows: list[object]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([asdict(row) for row in rows])


def load_dashboard_data() -> dict[str, object]:
    service = AnalyticsService(AppConfig.from_env().database_url)
    return {
        "overview": service.get_overview_kpis(),
        "adoption_practice": _frame(service.get_adoption_by_dimension("practice")),
        "adoption_level": _frame(service.get_adoption_by_dimension("level")),
        "adoption_location": _frame(service.get_adoption_by_dimension("location")),
        "adoption_terminal": _frame(service.get_adoption_by_dimension("terminal")),
        "adoption_os": _frame(service.get_adoption_by_dimension("os")),
        "daily_trend": _frame(service.get_daily_usage_trend()),
        "models": _frame(service.get_model_summary()),
        "tools": _frame(service.get_tool_summary()),
        "errors": _frame(service.get_error_summary(10)),
        "peak_hours": _frame(service.get_peak_usage_hours()),
        "top_sessions": _frame(service.get_top_sessions(10)),
    }

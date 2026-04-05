from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
API_TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "15"))


def _frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _request_json(path: str, params: dict[str, Any] | None = None) -> Any:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{DEFAULT_API_BASE_URL}{path}{query}"
    with urlopen(url, timeout=API_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(f"API request failed ({response.status}): {url}")
        return json.loads(response.read().decode("utf-8"))


def load_dashboard_data() -> dict[str, object]:
    payload = _request_json("/dashboard")
    return {
        "overview": payload["overview"],
        "adoption_practice": _frame(payload["adoption_practice"]),
        "adoption_level": _frame(payload["adoption_level"]),
        "adoption_location": _frame(payload["adoption_location"]),
        "adoption_terminal": _frame(payload["adoption_terminal"]),
        "adoption_os": _frame(payload["adoption_os"]),
        "daily_trend": _frame(payload["daily_trend"]),
        "models": _frame(payload["models"]),
        "tools": _frame(payload["tools"]),
        "errors": _frame(payload["errors"]),
        "peak_hours": _frame(payload["peak_hours"]),
        "top_sessions": _frame(payload["top_sessions"]),
    }


def load_predictive_data(
    metric: str,
    *,
    horizon_days: int = 7,
    backtest_days: int = 7,
) -> dict[str, object]:
    payload = _request_json(
        "/predictive/forecast",
        params={
            "metric": metric,
            "horizon_days": horizon_days,
            "backtest_days": backtest_days,
        },
    )
    return {
        "metric": payload["metric"],
        "metric_label": payload["metric_label"],
        "horizon_days": payload["horizon_days"],
        "backtest_days": payload["backtest_days"],
        "train_days": payload["train_days"],
        "mae": payload["mae"],
        "mape_pct": payload["mape_pct"],
        "trend_slope_per_day": payload["trend_slope_per_day"],
        "last_actual_value": payload["last_actual_value"],
        "last_predicted_value": payload["last_predicted_value"],
        "points": _frame(payload["points"]),
        "anomalies": _frame(payload["anomalies"]),
    }

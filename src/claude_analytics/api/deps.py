from __future__ import annotations

from functools import lru_cache

from claude_analytics.analytics import AnalyticsService
from claude_analytics.config import AppConfig


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    config = AppConfig.from_env()
    return AnalyticsService(config.database_url)

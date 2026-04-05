from __future__ import annotations

from enum import Enum

from fastapi import APIRouter, Depends, Query

from claude_analytics.analytics import AnalyticsService
from claude_analytics.api.deps import get_analytics_service


class AdoptionDimension(str, Enum):
    practice = "practice"
    level = "level"
    location = "location"
    terminal = "terminal"
    os = "os"


router = APIRouter(tags=["analytics"])


@router.get("/overview")
def get_overview(service: AnalyticsService = Depends(get_analytics_service)) -> dict[str, object]:
    return service.get_overview_kpis().to_dict()


@router.get("/adoption")
def get_adoption(
    dimension: AdoptionDimension = Query(default=AdoptionDimension.practice),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict[str, object]]:
    rows = service.get_adoption_by_dimension(dimension.value)
    return [row.to_dict() for row in rows]


@router.get("/trend/daily")
def get_daily_trend(service: AnalyticsService = Depends(get_analytics_service)) -> list[dict[str, object]]:
    rows = service.get_daily_usage_trend()
    return [row.to_dict() for row in rows]


@router.get("/models")
def get_models(service: AnalyticsService = Depends(get_analytics_service)) -> list[dict[str, object]]:
    rows = service.get_model_summary()
    return [row.to_dict() for row in rows]


@router.get("/tools")
def get_tools(service: AnalyticsService = Depends(get_analytics_service)) -> list[dict[str, object]]:
    rows = service.get_tool_summary()
    return [row.to_dict() for row in rows]


@router.get("/errors")
def get_errors(
    limit: int = Query(default=10, ge=1, le=100),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict[str, object]]:
    rows = service.get_error_summary(limit=limit)
    return [row.to_dict() for row in rows]


@router.get("/usage/peak-hours")
def get_peak_hours(service: AnalyticsService = Depends(get_analytics_service)) -> list[dict[str, object]]:
    rows = service.get_peak_usage_hours()
    return [row.to_dict() for row in rows]


@router.get("/sessions/top")
def get_top_sessions(
    limit: int = Query(default=10, ge=1, le=100),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict[str, object]]:
    rows = service.get_top_sessions(limit=limit)
    return [row.to_dict() for row in rows]


@router.get("/dashboard")
def get_dashboard_payload(
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, object]:
    return {
        "overview": service.get_overview_kpis().to_dict(),
        "adoption_practice": [row.to_dict() for row in service.get_adoption_by_dimension("practice")],
        "adoption_level": [row.to_dict() for row in service.get_adoption_by_dimension("level")],
        "adoption_location": [row.to_dict() for row in service.get_adoption_by_dimension("location")],
        "adoption_terminal": [row.to_dict() for row in service.get_adoption_by_dimension("terminal")],
        "adoption_os": [row.to_dict() for row in service.get_adoption_by_dimension("os")],
        "daily_trend": [row.to_dict() for row in service.get_daily_usage_trend()],
        "models": [row.to_dict() for row in service.get_model_summary()],
        "tools": [row.to_dict() for row in service.get_tool_summary()],
        "errors": [row.to_dict() for row in service.get_error_summary(10)],
        "peak_hours": [row.to_dict() for row in service.get_peak_usage_hours()],
        "top_sessions": [row.to_dict() for row in service.get_top_sessions(10)],
    }

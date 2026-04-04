from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class OverviewKPIs:
    total_employees: int
    active_users: int
    total_sessions: int
    total_events: int
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    total_api_errors: int
    api_error_rate_pct: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AdoptionBreakdown:
    dimension: str
    active_users: int
    total_sessions: int
    total_events: int
    total_cost_usd: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class UsageTrendPoint:
    event_date: str
    active_users: int
    total_sessions: int
    total_events: int
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ModelSummary:
    model: str
    api_requests: int
    total_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    avg_duration_ms: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ToolSummary:
    tool_name: str
    tool_decisions: int
    accepted_decisions: int
    rejected_decisions: int
    tool_results: int
    success_rate_pct: float
    avg_duration_ms: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ErrorSummary:
    status_code: str
    error_message: str
    error_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PeakUsageHour:
    event_hour: int
    active_users: int
    total_sessions: int
    total_events: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SessionHighlight:
    session_id: str
    user_email: str
    employee_practice: str | None
    total_events: int
    total_cost_usd: float
    session_duration_ms: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

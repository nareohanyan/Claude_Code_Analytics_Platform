from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from claude_analytics.db.base import Base


class Employee(Base):
    __tablename__ = "employees"

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    practice: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("idx_events_timestamp", "event_timestamp"),
        Index("idx_events_event_name", "event_name"),
        Index("idx_events_session_id", "session_id"),
        Index("idx_events_user_email", "user_email"),
        Index("idx_events_model", "model"),
        Index("idx_events_tool_name", "tool_name"),
    )

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    batch_timestamp_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    batch_year: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_month: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_day: Mapped[int] = mapped_column(Integer, nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    log_group: Mapped[str] = mapped_column(String(255), nullable=False)
    log_stream: Mapped[str] = mapped_column(String(255), nullable=False)
    event_body: Mapped[str] = mapped_column(String(100), nullable=False)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    organization_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    terminal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    user_account_uuid: Mapped[str] = mapped_column(String(64), nullable=False)
    user_email: Mapped[str] = mapped_column(ForeignKey("employees.email"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    scope_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope_version: Mapped[str] = mapped_column(String(50), nullable=False)
    service_name: Mapped[str | None] = mapped_column(String(255))
    service_version: Mapped[str | None] = mapped_column(String(50))
    host_arch: Mapped[str | None] = mapped_column(String(50))
    host_name: Mapped[str | None] = mapped_column(String(255))
    os_type: Mapped[str | None] = mapped_column(String(50))
    os_version: Mapped[str | None] = mapped_column(String(50))
    resource_practice: Mapped[str | None] = mapped_column(String(100))
    resource_profile: Mapped[str | None] = mapped_column(String(100))
    resource_serial: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cache_read_tokens: Mapped[int | None] = mapped_column(Integer)
    cache_creation_tokens: Mapped[int | None] = mapped_column(Integer)
    tool_name: Mapped[str | None] = mapped_column(String(100))
    decision: Mapped[str | None] = mapped_column(String(20))
    decision_source: Mapped[str | None] = mapped_column(String(50))
    decision_type: Mapped[str | None] = mapped_column(String(20))
    decision_source_raw: Mapped[str | None] = mapped_column(String(50))
    tool_success: Mapped[bool | None]
    tool_result_size_bytes: Mapped[int | None] = mapped_column(Integer)
    prompt_length: Mapped[int | None] = mapped_column(Integer)
    attempt: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    status_code: Mapped[str | None] = mapped_column(String(20))


class SessionMetric(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("idx_sessions_user_email", "user_email"),
        Index("idx_sessions_session_date", "session_date"),
    )

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_email: Mapped[str] = mapped_column(ForeignKey("employees.email"), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(64), nullable=False)
    terminal_type: Mapped[str | None] = mapped_column(String(100))
    os_type: Mapped[str | None] = mapped_column(String(50))
    scope_version: Mapped[str | None] = mapped_column(String(50))
    session_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    session_duration_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_events: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    api_request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    api_error_count: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_decision_count: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_result_count: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_tool_count: Mapped[int] = mapped_column(Integer, nullable=False)
    rejected_tool_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    total_input_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_output_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_cache_read_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_cache_creation_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    avg_api_duration_ms: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))

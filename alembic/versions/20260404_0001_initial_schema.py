"""Initial analytics schema.

Revision ID: 20260404_0001
Revises: None
Create Date: 2026-04-04 12:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260404_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("email", sa.String(length=255), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("practice", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=False),
    )

    op.create_table(
        "events",
        sa.Column("event_id", sa.String(length=128), primary_key=True),
        sa.Column("batch_timestamp_ms", sa.BigInteger(), nullable=False),
        sa.Column("batch_year", sa.Integer(), nullable=False),
        sa.Column("batch_month", sa.Integer(), nullable=False),
        sa.Column("batch_day", sa.Integer(), nullable=False),
        sa.Column("message_type", sa.String(length=50), nullable=False),
        sa.Column("log_group", sa.String(length=255), nullable=False),
        sa.Column("log_stream", sa.String(length=255), nullable=False),
        sa.Column("event_body", sa.String(length=100), nullable=False),
        sa.Column("event_name", sa.String(length=100), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("event_hour", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("terminal_type", sa.String(length=100), nullable=False),
        sa.Column("user_account_uuid", sa.String(length=64), nullable=False),
        sa.Column("user_email", sa.String(length=255), sa.ForeignKey("employees.email"), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("scope_name", sa.String(length=255), nullable=False),
        sa.Column("scope_version", sa.String(length=50), nullable=False),
        sa.Column("service_name", sa.String(length=255)),
        sa.Column("service_version", sa.String(length=50)),
        sa.Column("host_arch", sa.String(length=50)),
        sa.Column("host_name", sa.String(length=255)),
        sa.Column("os_type", sa.String(length=50)),
        sa.Column("os_version", sa.String(length=50)),
        sa.Column("resource_practice", sa.String(length=100)),
        sa.Column("resource_profile", sa.String(length=100)),
        sa.Column("resource_serial", sa.String(length=100)),
        sa.Column("model", sa.String(length=100)),
        sa.Column("cost_usd", sa.Numeric(18, 6)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cache_read_tokens", sa.Integer()),
        sa.Column("cache_creation_tokens", sa.Integer()),
        sa.Column("tool_name", sa.String(length=100)),
        sa.Column("decision", sa.String(length=20)),
        sa.Column("decision_source", sa.String(length=50)),
        sa.Column("decision_type", sa.String(length=20)),
        sa.Column("decision_source_raw", sa.String(length=50)),
        sa.Column("tool_success", sa.Boolean()),
        sa.Column("tool_result_size_bytes", sa.Integer()),
        sa.Column("prompt_length", sa.Integer()),
        sa.Column("attempt", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("status_code", sa.String(length=20)),
    )

    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(length=64), primary_key=True),
        sa.Column("user_email", sa.String(length=255), sa.ForeignKey("employees.email"), nullable=False),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("terminal_type", sa.String(length=100)),
        sa.Column("os_type", sa.String(length=50)),
        sa.Column("scope_version", sa.String(length=50)),
        sa.Column("session_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_duration_ms", sa.BigInteger(), nullable=False),
        sa.Column("total_events", sa.Integer(), nullable=False),
        sa.Column("prompt_count", sa.Integer(), nullable=False),
        sa.Column("api_request_count", sa.Integer(), nullable=False),
        sa.Column("api_error_count", sa.Integer(), nullable=False),
        sa.Column("tool_decision_count", sa.Integer(), nullable=False),
        sa.Column("tool_result_count", sa.Integer(), nullable=False),
        sa.Column("accepted_tool_count", sa.Integer(), nullable=False),
        sa.Column("rejected_tool_count", sa.Integer(), nullable=False),
        sa.Column("total_cost_usd", sa.Numeric(18, 6), nullable=False),
        sa.Column("total_input_tokens", sa.BigInteger(), nullable=False),
        sa.Column("total_output_tokens", sa.BigInteger(), nullable=False),
        sa.Column("total_cache_read_tokens", sa.BigInteger(), nullable=False),
        sa.Column("total_cache_creation_tokens", sa.BigInteger(), nullable=False),
        sa.Column("avg_api_duration_ms", sa.Numeric(14, 3)),
    )

    op.create_index("idx_events_timestamp", "events", ["event_timestamp"], unique=False)
    op.create_index("idx_events_event_name", "events", ["event_name"], unique=False)
    op.create_index("idx_events_session_id", "events", ["session_id"], unique=False)
    op.create_index("idx_events_user_email", "events", ["user_email"], unique=False)
    op.create_index("idx_events_model", "events", ["model"], unique=False)
    op.create_index("idx_events_tool_name", "events", ["tool_name"], unique=False)
    op.create_index("idx_sessions_user_email", "sessions", ["user_email"], unique=False)
    op.create_index("idx_sessions_session_date", "sessions", ["session_date"], unique=False)

    op.execute(
        """
        CREATE VIEW event_facts AS
        SELECT
            e.*,
            emp.full_name AS employee_full_name,
            emp.practice AS employee_practice,
            emp.level AS employee_level,
            emp.location AS employee_location
        FROM events AS e
        LEFT JOIN employees AS emp
            ON emp.email = e.user_email;
        """
    )
    op.execute(
        """
        CREATE VIEW session_facts AS
        SELECT
            s.*,
            emp.full_name AS employee_full_name,
            emp.practice AS employee_practice,
            emp.level AS employee_level,
            emp.location AS employee_location
        FROM sessions AS s
        LEFT JOIN employees AS emp
            ON emp.email = s.user_email;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS session_facts")
    op.execute("DROP VIEW IF EXISTS event_facts")
    op.drop_index("idx_sessions_session_date", table_name="sessions")
    op.drop_index("idx_sessions_user_email", table_name="sessions")
    op.drop_index("idx_events_tool_name", table_name="events")
    op.drop_index("idx_events_model", table_name="events")
    op.drop_index("idx_events_user_email", table_name="events")
    op.drop_index("idx_events_session_id", table_name="events")
    op.drop_index("idx_events_event_name", table_name="events")
    op.drop_index("idx_events_timestamp", table_name="events")
    op.drop_table("sessions")
    op.drop_table("events")
    op.drop_table("employees")

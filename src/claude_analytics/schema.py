from __future__ import annotations

EMPLOYEE_COLUMNS = (
    "email",
    "full_name",
    "practice",
    "level",
    "location",
)

REFRESH_SESSIONS_SQL = """
DELETE FROM sessions;

INSERT INTO sessions (
    session_id,
    user_email,
    organization_id,
    terminal_type,
    os_type,
    scope_version,
    session_start,
    session_end,
    session_date,
    session_duration_ms,
    total_events,
    prompt_count,
    api_request_count,
    api_error_count,
    tool_decision_count,
    tool_result_count,
    accepted_tool_count,
    rejected_tool_count,
    total_cost_usd,
    total_input_tokens,
    total_output_tokens,
    total_cache_read_tokens,
    total_cache_creation_tokens,
    avg_api_duration_ms
)
SELECT
    session_id,
    MIN(user_email) AS user_email,
    MIN(organization_id) AS organization_id,
    MIN(terminal_type) AS terminal_type,
    MIN(os_type) AS os_type,
    MIN(scope_version) AS scope_version,
    MIN(event_timestamp) AS session_start,
    MAX(event_timestamp) AS session_end,
    MIN(event_date) AS session_date,
    CAST(EXTRACT(EPOCH FROM (MAX(event_timestamp) - MIN(event_timestamp))) * 1000 AS BIGINT) AS session_duration_ms,
    COUNT(*) AS total_events,
    COUNT(*) FILTER (WHERE event_name = 'user_prompt') AS prompt_count,
    COUNT(*) FILTER (WHERE event_name = 'api_request') AS api_request_count,
    COUNT(*) FILTER (WHERE event_name = 'api_error') AS api_error_count,
    COUNT(*) FILTER (WHERE event_name = 'tool_decision') AS tool_decision_count,
    COUNT(*) FILTER (WHERE event_name = 'tool_result') AS tool_result_count,
    COUNT(*) FILTER (WHERE event_name = 'tool_decision' AND decision = 'accept') AS accepted_tool_count,
    COUNT(*) FILTER (WHERE event_name = 'tool_decision' AND decision = 'reject') AS rejected_tool_count,
    ROUND(COALESCE(SUM(cost_usd), 0)::numeric, 6) AS total_cost_usd,
    SUM(COALESCE(input_tokens, 0)) AS total_input_tokens,
    SUM(COALESCE(output_tokens, 0)) AS total_output_tokens,
    SUM(COALESCE(cache_read_tokens, 0)) AS total_cache_read_tokens,
    SUM(COALESCE(cache_creation_tokens, 0)) AS total_cache_creation_tokens,
    ROUND(AVG(duration_ms) FILTER (WHERE event_name = 'api_request')::numeric, 3) AS avg_api_duration_ms
FROM events
GROUP BY session_id;
"""

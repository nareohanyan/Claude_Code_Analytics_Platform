from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Iterator

from claude_analytics.schema import EMPLOYEE_COLUMNS


def _parse_iso_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _to_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _to_bool(value: str | None) -> bool | None:
    if value in (None, ""):
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"Unsupported boolean value: {value}")


def iter_employee_rows(csv_path: Path) -> Iterator[dict[str, object]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {column: row[column] for column in EMPLOYEE_COLUMNS}


def _normalize_event_row(
    batch: dict[str, object],
    log_event: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    attributes = event["attributes"]
    resource = event["resource"]
    scope = event["scope"]

    event_timestamp = _parse_iso_timestamp(attributes["event.timestamp"])

    normalized = {
        "event_id": log_event["id"],
        "batch_timestamp_ms": log_event["timestamp"],
        "batch_year": batch["year"],
        "batch_month": batch["month"],
        "batch_day": batch["day"],
        "message_type": batch["messageType"],
        "log_group": batch["logGroup"],
        "log_stream": batch["logStream"],
        "event_body": event["body"],
        "event_name": attributes["event.name"],
        "event_timestamp": event_timestamp.isoformat(),
        "event_date": event_timestamp.date().isoformat(),
        "event_hour": event_timestamp.hour,
        "organization_id": attributes["organization.id"],
        "session_id": attributes["session.id"],
        "terminal_type": attributes["terminal.type"],
        "user_account_uuid": attributes["user.account_uuid"],
        "user_email": attributes["user.email"],
        "user_id": attributes["user.id"],
        "scope_name": scope["name"],
        "scope_version": scope["version"],
        "service_name": resource.get("service.name"),
        "service_version": resource.get("service.version"),
        "host_arch": resource.get("host.arch"),
        "host_name": resource.get("host.name"),
        "os_type": resource.get("os.type"),
        "os_version": resource.get("os.version"),
        "resource_practice": resource.get("user.practice"),
        "resource_profile": resource.get("user.profile"),
        "resource_serial": resource.get("user.serial"),
        "model": attributes.get("model"),
        "cost_usd": _to_float(attributes.get("cost_usd")),
        "duration_ms": _to_int(attributes.get("duration_ms")),
        "input_tokens": _to_int(attributes.get("input_tokens")),
        "output_tokens": _to_int(attributes.get("output_tokens")),
        "cache_read_tokens": _to_int(attributes.get("cache_read_tokens")),
        "cache_creation_tokens": _to_int(attributes.get("cache_creation_tokens")),
        "tool_name": attributes.get("tool_name"),
        "decision": attributes.get("decision"),
        "decision_source": attributes.get("decision_source"),
        "decision_type": attributes.get("decision_type"),
        "decision_source_raw": attributes.get("source"),
        "tool_success": _to_bool(attributes.get("success")),
        "tool_result_size_bytes": _to_int(attributes.get("tool_result_size_bytes")),
        "prompt_length": _to_int(attributes.get("prompt_length")),
        "attempt": _to_int(attributes.get("attempt")),
        "error_message": attributes.get("error"),
        "status_code": attributes.get("status_code"),
    }
    return normalized


def iter_event_rows(jsonl_path: Path) -> Iterator[dict[str, object]]:
    with jsonl_path.open(encoding="utf-8") as handle:
        for line in handle:
            batch = json.loads(line)
            for log_event in batch["logEvents"]:
                event = json.loads(log_event["message"])
                yield _normalize_event_row(batch, log_event, event)

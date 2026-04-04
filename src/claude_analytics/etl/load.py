from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from typing import Iterable, Iterator, Type

from sqlalchemy import delete, func, inspect, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from claude_analytics.config import AppConfig
from claude_analytics.db.base import Base
from claude_analytics.db.models import Employee, Event, SessionMetric
from claude_analytics.db.session import create_session_factory, create_sqlalchemy_engine
from claude_analytics.etl.parser import iter_employee_rows, iter_event_rows
from claude_analytics.schema import REFRESH_SESSIONS_SQL


@dataclass(frozen=True)
class LoadSummary:
    database_dsn: str
    employees_loaded: int
    events_loaded: int
    sessions_built: int


def _chunked(rows: Iterable[dict[str, object]], chunk_size: int) -> Iterator[list[dict[str, object]]]:
    iterator = iter(rows)
    while True:
        chunk = list(islice(iterator, chunk_size))
        if not chunk:
            break
        yield chunk


def _validate_schema(database_url: str) -> None:
    engine = create_sqlalchemy_engine(database_url)
    try:
        inspector = inspect(engine)
        required = {"employees", "events", "sessions"}
        existing = set(inspector.get_table_names())
        missing = required - existing
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise RuntimeError(
                f"Missing database tables: {missing_str}. Run `alembic upgrade head` first."
            )
    finally:
        engine.dispose()


def _load_table(
    session,
    model: Type[Base],
    rows: Iterable[dict[str, object]],
    chunk_size: int,
    *,
    use_upsert: bool,
) -> int:
    inserted = 0
    for chunk in _chunked(rows, chunk_size):
        if use_upsert:
            statement = pg_insert(model).values(chunk)
            primary_keys = [column.name for column in model.__table__.primary_key.columns]
            update_map = {
                column.name: getattr(statement.excluded, column.name)
                for column in model.__table__.columns
                if column.name not in primary_keys
            }
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=primary_keys,
                    set_=update_map,
                )
            )
        else:
            session.execute(model.__table__.insert(), chunk)
        session.commit()
        inserted += len(chunk)
    return inserted


def load_dataset(config: AppConfig, *, reset_existing: bool = True, chunk_size: int = 5000) -> LoadSummary:
    config.validate_inputs()
    _validate_schema(config.database_url)

    session_factory = create_session_factory(config.database_url)
    with session_factory() as session:
        if reset_existing:
            session.execute(delete(SessionMetric))
            session.execute(delete(Event))
            session.execute(delete(Employee))
            session.commit()

        employees_loaded = _load_table(
            session,
            Employee,
            iter_employee_rows(config.employees_path),
            chunk_size,
            use_upsert=not reset_existing,
        )
        events_loaded = _load_table(
            session,
            Event,
            iter_event_rows(config.telemetry_path),
            chunk_size,
            use_upsert=not reset_existing,
        )
        session.execute(text(REFRESH_SESSIONS_SQL))
        session.commit()
        sessions_built = int(
            session.execute(select(func.count()).select_from(SessionMetric)).scalar_one()
        )

        return LoadSummary(
            database_dsn=config.database.display_dsn(),
            employees_loaded=employees_loaded,
            events_loaded=events_loaded,
            sessions_built=sessions_built,
        )

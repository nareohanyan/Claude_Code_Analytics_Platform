from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DATA_DIR = PROJECT_ROOT / "claude_code_telemetry (1)" / "output"
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE if ENV_FILE.exists() else None)


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "claude_code_analytics")
    user: str = os.getenv("POSTGRES_USER", "claude")
    password: str = os.getenv("POSTGRES_PASSWORD", "claude")
    sqlalchemy_url: str = os.getenv("DATABASE_URL", "")

    def resolved_sqlalchemy_url(self) -> str:
        if self.sqlalchemy_url:
            return self.sqlalchemy_url
        user = quote_plus(self.user)
        password = quote_plus(self.password)
        return f"postgresql+psycopg://{user}:{password}@{self.host}:{self.port}/{self.database}"

    def display_dsn(self) -> str:
        return f"{self.host}:{self.port}/{self.database}"


@dataclass(frozen=True)
class AppConfig:
    telemetry_path: Path = DEFAULT_RAW_DATA_DIR / "telemetry_logs.jsonl"
    employees_path: Path = DEFAULT_RAW_DATA_DIR / "employees.csv"
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    def validate_inputs(self) -> None:
        missing = [
            str(path)
            for path in (self.telemetry_path, self.employees_path)
            if not path.exists()
        ]
        if missing:
            raise FileNotFoundError(
                "Missing required input files:\n" + "\n".join(missing)
            )

    @property
    def database_url(self) -> str:
        return self.database.resolved_sqlalchemy_url()

    @classmethod
    def from_env(
        cls,
        *,
        telemetry_path: Path | None = None,
        employees_path: Path | None = None,
        database_url: str | None = None,
    ) -> "AppConfig":
        db_config = DatabaseConfig(sqlalchemy_url=database_url or os.getenv("DATABASE_URL", ""))
        return cls(
            telemetry_path=telemetry_path or DEFAULT_RAW_DATA_DIR / "telemetry_logs.jsonl",
            employees_path=employees_path or DEFAULT_RAW_DATA_DIR / "employees.csv",
            database=db_config,
        )

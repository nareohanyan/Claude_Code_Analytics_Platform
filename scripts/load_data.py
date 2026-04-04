from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from claude_analytics.config import AppConfig  # noqa: E402
from claude_analytics.etl.load import load_dataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load Claude Code telemetry into the local analytics database."
    )
    parser.add_argument(
        "--telemetry",
        type=Path,
        default=None,
        help="Path to telemetry_logs.jsonl",
    )
    parser.add_argument(
        "--employees",
        type=Path,
        default=None,
        help="Path to employees.csv",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="SQLAlchemy database URL override",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=5000,
        help="Number of rows to batch per insert operation",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Append/replace rows without clearing existing tables first",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = AppConfig.from_env(
        telemetry_path=args.telemetry,
        employees_path=args.employees,
        database_url=args.database_url,
    )
    summary = load_dataset(
        config,
        reset_existing=not args.no_reset,
        chunk_size=args.chunk_size,
    )
    print("Database ready:")
    print(f"  database: {summary.database_dsn}")
    print(f"  employees_loaded: {summary.employees_loaded}")
    print(f"  events_loaded: {summary.events_loaded}")
    print(f"  sessions_built: {summary.sessions_built}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

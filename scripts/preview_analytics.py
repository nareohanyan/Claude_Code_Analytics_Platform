from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from claude_analytics.analytics import AnalyticsService  # noqa: E402
from claude_analytics.config import AppConfig  # noqa: E402


def main() -> int:
    service = AnalyticsService(AppConfig.from_env().database_url)

    payload = {
        "overview": service.get_overview_kpis().to_dict(),
        "adoption_by_practice": [row.to_dict() for row in service.get_adoption_by_dimension("practice")[:5]],
        "daily_trend_sample": [row.to_dict() for row in service.get_daily_usage_trend()[:5]],
        "models": [row.to_dict() for row in service.get_model_summary()[:5]],
        "tools": [row.to_dict() for row in service.get_tool_summary()[:5]],
        "errors": [row.to_dict() for row in service.get_error_summary(5)],
        "peak_hours": [row.to_dict() for row in service.get_peak_usage_hours()[:5]],
        "top_sessions": [row.to_dict() for row in service.get_top_sessions(5)],
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

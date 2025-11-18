from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from ..storage import load_reports
from ..analytics import build_dashboard_report


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard():
    rs = load_reports()
    return build_dashboard_report(rs)


def _avg_param(reports: List[Dict[str, Any]], key: str) -> Optional[float]:
    # kept for backward imports; unused after refactor
    return None


def _latest_date(reports: List[Dict[str, Any]]) -> Optional[str]:
    # kept for backward imports; unused after refactor
    return reports[-1].get("date") if reports else None

import csv
import os
import pathlib
from typing import Any, Dict, List, Sequence


DATA_PATH = pathlib.Path(os.environ.get("DATA_DIR", "data"))
DATA_PATH.mkdir(parents=True, exist_ok=True)

FILE = DATA_PATH / "reports.csv"

HEADERS: Sequence[str] = (
    "BoreholeID",
    "ProjectName",
    "SiteName",
    "Latitude",
    "Longitude",
    "GroundElevation_mRL",
    "StartDate",
    "EndDate",
    "DrillingMethod",
    "BoreholeDiameter_mm",
    "TargetDepth_m",
    "FinalDepth_m",
    "CasingInstalled_mm",
    "GroundwaterDepth_m",
    "GroundwaterEncountered",
    "SoilDescription",
    "USCS_Class",
    "Avg_SPT_N60",
    "Contractor",
    "LoggingGeologist",
    "Remarks",
    "SubmittedBy",
)


def _to_row(report: Dict[str, Any]) -> Dict[str, Any]:
    row = {key: "" for key in HEADERS}
    for key in HEADERS:
        if key in report and report[key] is not None:
            row[key] = report[key]
    return row


def _detect_existing_headers() -> Sequence[str] | None:
    if not FILE.exists():
        return None
    with FILE.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return None
        return header


def save_report(report: Dict[str, Any], submitted_by: str | None = None) -> None:
    headers = _detect_existing_headers()
    if headers and list(headers) != list(HEADERS):
        raise RuntimeError(
            "Existing reports.csv schema does not match soil boring schema. "
            "Please migrate or remove the file before continuing."
        )
    payload = dict(report)
    if submitted_by:
        payload["SubmittedBy"] = submitted_by
    row = _to_row(payload)
    new_file = not FILE.exists() or (headers is None)
    with FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def load_reports() -> List[Dict[str, Any]]:
    if not FILE.exists():
        return []
    with FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items: List[Dict[str, Any]] = []
        for row in reader:
            items.append(dict(row))
        return items


def _write_reports(items: List[Dict[str, Any]]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    with FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in items:
            writer.writerow(_to_row(row))


def delete_report(borehole_id: str) -> bool:
    """Remove the first report matching the BoreholeID. Returns True if deleted."""
    reports = load_reports()
    remaining: List[Dict[str, Any]] = []
    deleted = False
    for row in reports:
        if not deleted and str(row.get("BoreholeID")) == str(borehole_id):
            deleted = True
            continue
        remaining.append(row)
    if deleted:
        _write_reports(remaining)
    return deleted


def update_report(borehole_id: str, updates: Dict[str, Any]) -> bool:
    """Update a report matching BoreholeID. Returns True if updated."""
    reports = load_reports()
    updated = False
    new_reports: List[Dict[str, Any]] = []
    for row in reports:
        if not updated and str(row.get("BoreholeID")) == str(borehole_id):
            merged = dict(row)
            merged.update(updates or {})
            new_reports.append(merged)
            updated = True
        else:
            new_reports.append(row)
    if updated:
        _write_reports(new_reports)
    return updated

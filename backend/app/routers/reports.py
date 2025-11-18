from fastapi import APIRouter, Body, Depends, HTTPException

from ..models import Report
from ..storage import save_report, load_reports, delete_report, update_report
from ..auth import get_current_user


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("")
def create_report(
    r: dict = Body(...),
    user=Depends(get_current_user),
):
    # Accept raw dict so the form can submit fields matching existing CSV headers
    if isinstance(r, dict):
        save_report(r, submitted_by=user["email"])
    else:
        # Fallback: try model parse
        save_report(Report(**r).model_dump(), submitted_by=user["email"])
    return {"status": "ok"}


@router.get("")
def list_reports(user=Depends(get_current_user)):
    return load_reports()


@router.delete("/{borehole_id}")
def remove_report(borehole_id: str, user=Depends(get_current_user)):
    if not delete_report(borehole_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "deleted"}


@router.put("/{borehole_id}")
def edit_report(
    borehole_id: str,
    r: dict = Body(...),
    user=Depends(get_current_user),
):
    if not update_report(borehole_id, r or {}):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "updated"}

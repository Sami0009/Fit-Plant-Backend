from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..crud.report import get_report, get_reports, create_report, update_report, delete_report
from ..schemas.report import Report, ReportCreate, ReportUpdate, PaginatedReports
from ..auth.auth import get_current_admin

router = APIRouter()

@router.post("/", response_model=Report)
def create_report_endpoint(report: ReportCreate, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    return create_report(db=db, report=report)

@router.get("/{report_id}", response_model=Report)
def read_report(report_id: str, db: Session = Depends(get_db), response: Response = None):
    db_report = get_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if response:
        response.headers["Cache-Control"] = "no-cache"
    return db_report

@router.get("/", response_model=PaginatedReports)
def read_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), response: Response = None):
    reports, total = get_reports(db, skip=skip, limit=limit)
    if response:
        response.headers["Cache-Control"] = "no-cache"
    return PaginatedReports(reports=reports, total=total, skip=skip, limit=limit)

@router.put("/{report_id}", response_model=Report)
def update_report_endpoint(report_id: str, report: ReportUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    db_report = update_report(db, report_id=report_id, report_update=report)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return db_report

@router.delete("/{report_id}")
def delete_report_endpoint(report_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_admin)):
    db_report = delete_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"detail": "Report deleted"}
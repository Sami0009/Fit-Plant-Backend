from sqlalchemy.orm import Session
from ..models.report import Report
from ..schemas.report import ReportCreate, ReportUpdate

def get_report(db: Session, report_id: str):
    return db.query(Report).filter(Report.report_id == report_id).first()

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    query = db.query(Report)
    total = query.count()
    reports = query.offset(skip).limit(limit).all()
    print(f"DEBUG: Total reports in DB: {total}, returning {len(reports)} reports")
    return reports, total

def create_report(db: Session, report: ReportCreate):
    db_report = Report(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    print(f"DEBUG: Created report {db_report.report_id}")
    return db_report

def update_report(db: Session, report_id: str, report_update: ReportUpdate):
    db_report = get_report(db, report_id)
    if db_report:
        for key, value in report_update.dict(exclude_unset=True).items():
            setattr(db_report, key, value)
        db.commit()
        db.refresh(db_report)
    return db_report

def delete_report(db: Session, report_id: str):
    db_report = get_report(db, report_id)
    if db_report:
        db.delete(db_report)
        db.commit()
        print(f"DEBUG: Deleted report {report_id}")
    return db_report
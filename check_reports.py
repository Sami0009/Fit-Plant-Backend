from app.database import SessionLocal
from app.models.report import Report

db = SessionLocal()
reports = db.query(Report).all()
print(f"Total reports: {len(reports)}")
for r in reports:
    print(f'ID: {r.report_id}, Title: {r.title}, Status: {r.status}')
db.close()
from sqlalchemy import Column, String, DateTime, JSON
from ..database import Base

class Report(Base):
    __tablename__ = "reports"

    report_id = Column(String, primary_key=True, index=True)
    title = Column(String)
    assigned_to_name = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime)
    image = Column(JSON)
    prediction_details = Column(JSON)
    disease_info = Column(JSON)
    recommendations = Column(JSON)
    severity_level = Column(String)
    status = Column(String)
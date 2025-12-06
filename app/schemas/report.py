from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List

class ReportBase(BaseModel):
    report_id: str
    title: str
    assigned_to_name: str
    created_by: str
    created_at: datetime
    image: Dict
    prediction_details: Dict
    disease_info: Dict
    recommendations: Dict
    severity_level: str
    status: str

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    assigned_to_name: Optional[str] = None
    status: Optional[str] = None
    severity_level: Optional[str] = None

class Report(ReportBase):
    class Config:
        from_attributes = True

class PaginatedReports(BaseModel):
    reports: List[Report]
    total: int
    skip: int
    limit: int
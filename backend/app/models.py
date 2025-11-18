from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class Report(BaseModel):
    BoreholeID: str
    ProjectName: str
    SiteName: str
    Latitude: Optional[str] = None
    Longitude: Optional[str] = None
    GroundElevation_mRL: Optional[str] = None
    StartDate: str
    EndDate: str
    DrillingMethod: str
    BoreholeDiameter_mm: Optional[str] = None
    TargetDepth_m: Optional[str] = None
    FinalDepth_m: str
    CasingInstalled_mm: Optional[str] = None
    GroundwaterDepth_m: Optional[str] = None
    GroundwaterEncountered: Optional[str] = None
    SoilDescription: Optional[str] = None
    USCS_Class: Optional[str] = None
    Avg_SPT_N60: Optional[str] = None
    Contractor: str
    LoggingGeologist: Optional[str] = None
    Remarks: Optional[str] = None


class Query(BaseModel):
    question: str
    context: Optional[str] = None
    # Optional conversational history for follow-ups
    history: Optional[List[Dict[str, str]]] = None  # items like {"role": "user"|"assistant", "content": "..."}


class Summary(BaseModel):
    period: str
    text: str

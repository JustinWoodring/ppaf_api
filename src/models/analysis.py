import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

class SingleDocumentAnalysisBase(SQLModel):
    document_id: int
    kind: ["BASE", "GPDR", "COPPA", "HIPPA", "FERPA"]

class SingleDocumentAnalysisCreate(SingleDocumentAnalysisBase):
    pass

class SingleDocumentAnalysis(SingleDocumentAnalysisBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    contents: str
    state: ["Pending" | "In Progress" | "Complete" | "Failed"]
    analysis_date: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class SingleDocumentAnalysisReadShort(SingleDocumentAnalysisBase):
    id: int
    state: ["Pending" | "In Progress" | "Complete" | "Failed"]
    analysis_date: datetime.datetime

class SingleDocumentAnalysisRead(SingleDocumentAnalysisReadShort):
    contents: str
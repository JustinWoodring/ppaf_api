import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

class SingleDocumentAnalysisKinds():
    BASE: str = "BASE"
    GDPR: str = "GDPR"
    COPPA: str = "COPPA"
    HIPPA: str = "HIPPA"
    FERPA: str = "FERPA"
        
class SingleDocumentAnalysisStates():
    PENDING: str = "Pending"
    IN_PROGRESS: str = "In Progress"
    COMPLETE: str = "Complete"
    FAILED: str = "Failed"

class SingleDocumentAnalysisBase(SQLModel):
    document_id: int = Field(foreign_key="document.id")
    kind: str

class SingleDocumentAnalysisCreate(SingleDocumentAnalysisBase):
    pass

class SingleDocumentAnalysis(SingleDocumentAnalysisBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    contents: Optional[str] = Field(default=None)
    state: str
    analysis_date: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class SingleDocumentAnalysisReadShort(SingleDocumentAnalysisBase):
    id: int
    state: str
    analysis_date: datetime.datetime

class SingleDocumentAnalysisRead(SingleDocumentAnalysisReadShort):
    contents: Optional[str]
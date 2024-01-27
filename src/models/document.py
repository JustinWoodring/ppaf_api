import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

class DocumentBase(SQLModel):
    title: str
    url: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    contents: str
    content_access_date: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class DocumentReadShort(DocumentBase):
    id: int
    content_access_date: datetime.datetime

class DocumentRead(DocumentBase):
    id: int
    contents: str
    content_access_date: datetime.datetime
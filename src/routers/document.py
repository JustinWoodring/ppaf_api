from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from langchain_community.document_loaders import WebBaseLoader

from ..infrastructure.dependencies import get_db
from ..models.document import *

router = APIRouter(
    prefix="/document"
)

@router.get("/", response_model=List[DocumentReadShort])
async def get_user_documents(db: Session = Depends(get_db)):
    documents = db.exec(select(Document)).all()
    return documents

@router.post("/", response_model=DocumentRead)
async def create_user_document(*, db: Session = Depends(get_db), document: DocumentCreate):
    loader = WebBaseLoader(document.url)
    content = loader.load()

    db_document = Document(
        title=document.title,
        url=document.url,
        user_id=0,
        contents=content[0].page_content
    )

    db_document = Document.model_validate(db_document)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document
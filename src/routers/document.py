from typing import Annotated, List

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import Session, select

from langchain_community.document_loaders import WebBaseLoader
from src.infrastructure.auth import get_current_active_user

from src.models.user import User
from src.tasks.single_document_analysis.base import perform_base_analysis

from ..infrastructure.dependencies import get_db
from ..models.document import *

router = APIRouter(
    prefix="/document"
)

@router.get("/{document_id}", response_model=DocumentRead)
async def get_user_document(document_id: int, user: Annotated[User, Depends(get_current_active_user)], db: Session = Depends(get_db)):
    document = db.exec(select(Document).where(Document.user_id==user.id).where(Document.id==document_id)).first()
    return document

@router.get("/", response_model=List[DocumentReadShort])
async def get_user_documents(user: Annotated[User, Depends(get_current_active_user)], db: Session = Depends(get_db)):
    documents = db.exec(select(Document).where(Document.user_id==user.id)).all()
    return documents

@router.post("/", response_model=DocumentRead)
async def create_user_document(*, user: Annotated[User, Depends(get_current_active_user)], db: Session = Depends(get_db),  background_tasks: BackgroundTasks, document: DocumentCreate):
    loader = WebBaseLoader(document.url)
    content = loader.load()

    db_document = Document(
        title=document.title,
        url=document.url,
        user_id=user.id,
        contents=content[0].page_content
    )

    db_document = Document.model_validate(db_document)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    background_tasks.add_task(perform_base_analysis, db_document.id)
    return db_document
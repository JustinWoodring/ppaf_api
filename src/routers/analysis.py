from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from src.infrastructure.auth import get_current_active_user
from src.infrastructure.dependencies import get_db

from src.models.analysis import SingleDocumentAnalysis, SingleDocumentAnalysisRead
from src.models.user import User


router = APIRouter(
    prefix="/analysis"
)

@router.get("/singular/{analysis_id}", response_model=SingleDocumentAnalysisRead)
async def get_user_single_document_analysis(analysis_id: int, user: Annotated[User, Depends(get_current_active_user)], db: Session = Depends(get_db)):
    analysis = db.exec(select(SingleDocumentAnalysis).where(SingleDocumentAnalysis.user_id==user.id).where(SingleDocumentAnalysis.id==analysis_id)).first()
    return analysis
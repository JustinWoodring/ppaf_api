from sqlmodel import Session, select
from src.infrastructure.dependencies import get_db
from src.models.document import Document
from src.models.analysis import SingleDocumentAnalysis, SingleDocumentAnalysisKinds, SingleDocumentAnalysisStates

def reset_and_run_broken_base_analyses():
    db : Session = next(get_db())

    broken_jobs = db.exec(
        select(SingleDocumentAnalysis)
        .where(SingleDocumentAnalysis.kind == SingleDocumentAnalysisKinds.BASE)
        .where(SingleDocumentAnalysis.state == SingleDocumentAnalysisStates.IN_PROGRESS)
    ).all()

    for job in broken_jobs:
        job.state = SingleDocumentAnalysisStates.PENDING

    db.commit()

    for job in broken_jobs:
        run_base_analysis()

def request_base_analysis(document_id):
    db : Session = next(get_db())

    document = db.exec(select(Document).where(Document.id==document_id)).first()

    # Create Pending Analysis
    db_analysis = SingleDocumentAnalysis(
        document_id=document_id,
        kind=SingleDocumentAnalysisKinds.BASE,
        user_id=document.user_id,
        state=SingleDocumentAnalysisStates.PENDING
    )

    db_analysis = SingleDocumentAnalysis.model_validate(db_analysis)
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    run_base_analysis(db_analysis)

def run_base_analysis(db_analysis : SingleDocumentAnalysis):
    db : Session = next(get_db())

    db_analysis = db.exec(
        select(SingleDocumentAnalysis)
        .where(SingleDocumentAnalysis.id == db_analysis.id)
    ).first()
    
    db.refresh(db_analysis)

    # Move to In Progress
    db_analysis.state=SingleDocumentAnalysisStates.IN_PROGRESS
    db.commit()
    db.refresh(db_analysis)

    # Begin Analysis
    failure_count = 0
    failure = False
    content = ""

    while(failure_count>5):
        failure = False
        try:
            ###TODO LLM CODE HERE
            pass
        except Exception:
            failure = True
            failure_count+=1

        if failure is False:
            break

    if failure is True:
        db_analysis.state = SingleDocumentAnalysisStates.FAILED
    else:
        db_analysis.state = SingleDocumentAnalysisStates.COMPLETE
        db_analysis.contents = content

    # Move to Complete or Failed
    db.commit()
    db.refresh(db_analysis)
    
    
        

    
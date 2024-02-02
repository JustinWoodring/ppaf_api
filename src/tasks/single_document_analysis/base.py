import json
import langchain
from sqlmodel import Session, select
from src.infrastructure.dependencies import get_db
from src.models.document import Document
from src.models.analysis import SingleDocumentAnalysis, SingleDocumentAnalysisKinds, SingleDocumentAnalysisStates

from typing import List
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
import re

from src.tasks.single_document_analysis.base_llm import text_splitter, summarizer_chain, final_scope_chain, final_score_chain

from langchain.docstore.document import Document as LangchainDoc


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

    while(failure_count<5):
        failure = False
        try:
            document = db.exec(select(Document).where(Document.id==db_analysis.document_id)).first()

            docs =  [LangchainDoc(page_content=document.contents, metadata={"source": "local"})]

            split_docs = text_splitter.split_documents(docs)

            print("length",len(split_docs))
            result_text = summarizer_chain.run(split_docs)
            summary_scopes = final_scope_chain.invoke({"summary": result_text})

            print(summary_scopes)

            summary_score = final_score_chain.invoke({"summary": result_text})

            value = {
                "summary": result_text,
                "scopes": summary_scopes['text']['scopes'],
                "score": summary_score['text']['score']
            }

            content=json.dumps(value)
        except Exception as e:
            print("Error ", e)
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
    
    
        

    
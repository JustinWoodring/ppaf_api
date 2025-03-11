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
import random

from src.tasks.single_document_analysis.base_llm import text_splitter, summarizer_chain, shared_map_chain, collected_map_chain, security_map_chain, final_scope_chain, final_score_chain, final_color_chain, final_shared_chain, final_collected_chain, final_security_chain

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
        run_base_analysis(job)

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
            shared_text = shared_map_chain.run(split_docs)
            collected_text = collected_map_chain.run(split_docs)
            security_text = security_map_chain.run(split_docs)

            #each scope shared,collected,security
            summary_scopes = final_scope_chain.invoke({"summary": result_text})
            shared = final_shared_chain.invoke({"summary": shared_text})
            collected = final_collected_chain.invoke({"summary": collected_text})
            security = final_security_chain.invoke({"summary": security_text})

            print(summary_scopes)
            print(shared)
            print(collected)
            print(security)

            summary_score = final_score_chain.invoke({"summary": result_text})

            # Generating a random number in between 0 and 2^24
            color = random.randrange(0, 2**24)
            
            # Converting that number from base-10 (decimal) to base-16 (hexadecimal)
            hex_color = hex(color)
            
            std_color = "#" + hex_color[2:]
            
            summary_color = {"text":{"color": std_color}}
            try:
                summary_color = final_color_chain.invoke({"summary": result_text})
            except Exception as e:
                pass

            value = {
                "summary": result_text,
                "scopes":summary_scopes['text']['scopes'],
                "shared": shared['text']['shared'],
                "collected": collected['text']['collected'],
                "security": security['text']['security'],
                "score": summary_score['text']['score'],
                "color": summary_color['text']['color']
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
    
    
        

    
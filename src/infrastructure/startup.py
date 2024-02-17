from src.tasks.single_document_analysis.gdpr import reset_and_run_broken_gdpr_analyses
from src.tasks.single_document_analysis.base import reset_and_run_broken_base_analyses
from .database import create_db_and_tables
from multiprocessing import Process


def on_startup():
    create_db_and_tables()
    p = Process(target=reset_and_run_broken_base_analyses, args=())
    p.start()
    p = Process(target=reset_and_run_broken_gdpr_analyses, args=())
    p.start()

from src.tasks.single_document_analysis.base import reset_and_run_broken_base_analyses
from .database import create_db_and_tables

def on_startup():
    create_db_and_tables()
    reset_and_run_broken_base_analyses()

from .database import create_db_and_tables

def on_startup():
    create_db_and_tables()

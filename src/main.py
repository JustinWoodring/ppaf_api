from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from .infrastructure.startup import on_startup
from .infrastructure.middleware import middleware
from .infrastructure.database import engine, SQLModel
from .routers import document

SQLModel.metadata.create_all(engine)

app = FastAPI()

app.add_event_handler("startup", on_startup)
#app.add_middleware(middleware)
app.include_router(document.router)
app.mount("/", StaticFiles(directory="../ppaf_client/build"), name="static")

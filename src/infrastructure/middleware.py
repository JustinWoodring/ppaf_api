from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware import Middleware

## CORS
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

def configure_middleware(app: FastAPI):
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    return app
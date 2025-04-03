import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from src.routes.resume import resume_router
from src.routes.job import job_router

def start_db():
    mongo_uri = os.getenv('MONGO_URI')  
    client = MongoClient(mongo_uri)
    db_name = os.getenv('MONGO_DB_NAME', 'resume_parser_db')  
    return client[db_name] 

app = FastAPI(
    title="Resume Parser API",
    description="API for parsing resume PDF files",
    version="1.0.0"
)

db = start_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(
    resume_router,
    prefix="/api/resume",
    tags=["Resume Parsing"]
)

app.include_router(
    job_router,
    prefix="/api/job",
    tags=["Job Postings"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
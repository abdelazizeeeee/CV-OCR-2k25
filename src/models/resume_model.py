from pymongo import MongoClient
import os
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db_name = os.getenv('MONGO_DB_NAME', 'resume_parser_db')
db = client[db_name]

resume_collection = db["parsed_resumes"]

class ResumeSchema(BaseModel):
    Name: Optional[str] = Field(None, title="Candidate's Name")
    LinkedIn_Link: Optional[str] = Field(None, title="LinkedIn Profile URL")
    Skills: Optional[List[str]] = Field(None, title="List of Skills")
    Certification: Optional[List[str]] = Field(None, title="List of Certifications")
    Worked_As: Optional[List[str]] = Field(None, title="Previous Job Titles")
    Years_Of_Experience: Optional[List[str]] = Field(None, title="Years of Experience")
    file_name: str = Field(..., title="Uploaded Resume File Name")
    uploaded_at: datetime = Field(default_factory=datetime.now(), title="Upload Timestamp")

def save_parsed_resume(parsed_data: dict):
    parsed_data["uploaded_at"] = datetime.now()
    resume_collection.insert_one(parsed_data)

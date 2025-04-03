from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from pymongo import MongoClient
import os

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db_name = os.getenv('MONGO_DB_NAME', 'resume_parser_db')
db = client[db_name]

job_collection = db["job_offers"]

class JobOfferSchema(BaseModel):
    title: str = Field(..., title="Job Title")
    description: Optional[str] = Field(None, title="Job Description")
    required_skills: List[str] = Field(..., title="Required Skills")
    preferred_certifications: Optional[List[str]] = Field(None, title="Preferred Certifications")
    experience_requirements: Optional[List[str]] = Field(None, title="Experience Requirements")
    min_years_experience: Optional[int] = Field(None, title="Minimum Years of Experience")
    created_at: datetime = Field(default_factory=datetime.now, title="Creation Timestamp")

def save_job_offer(job_data: dict):
    job_data["created_at"] = datetime.now()
    return job_collection.insert_one(job_data)

def get_all_job_offers():
    return list(job_collection.find())

def get_job_offer_by_id(job_id: str):
    from bson import ObjectId
    return job_collection.find_one({"_id": ObjectId(job_id)})
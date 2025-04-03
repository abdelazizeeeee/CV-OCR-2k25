from fastapi import APIRouter, HTTPException
from bson import ObjectId
from typing import List, Dict, Any
import re
from src.models.resume_model import resume_collection
from src.models.job import JobOfferSchema, save_job_offer, get_all_job_offers, get_job_offer_by_id
from pymongo import MongoClient
import os

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db_name = os.getenv('MONGO_DB_NAME', 'resume_parser_db')
db = client[db_name]

job_collection = db["job_offers"]

job_router = APIRouter()

@job_router.post("/jobs", response_model=Dict[str, Any])
async def create_job_offer(job_data: JobOfferSchema):
    """Create a new job offer"""
    result = save_job_offer(job_data.dict())
    
    job_id = str(result.inserted_id)
    job = job_data.dict()
    job["id"] = job_id
    
    return job

@job_router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_job_offers():
    """Get all job offers"""
    jobs = get_all_job_offers()
    
    for job in jobs:
        job["id"] = str(job["_id"])
        del job["_id"]
    
    return jobs

@job_router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_offer(job_id: str):
    """Get a specific job offer by ID"""
    try:
        job = get_job_offer_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job offer not found")
        
        job["id"] = str(job["_id"])
        del job["_id"]
        
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@job_router.get("/match/{job_id}/{resume_id}", response_model=Dict[str, Any])
async def match_resume_to_job(job_id: str, resume_id: str):
    """Match a resume to a job and return a matching score"""
    try:
        job = get_job_offer_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job offer not found")
        
        resume = resume_collection.find_one({"_id": ObjectId(resume_id)})
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        matching_result = calculate_matching_score(job, resume)
        
        return matching_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_matching_score(job: Dict[str, Any], resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate the matching score between a job offer and a resume
    Returns a dictionary with the overall score and scores for each category
    """
    scores = {
        "skills_score": 0,
        "certifications_score": 0,
        "experience_score": 0,
        "overall_score": 0
    }
    
    if job.get("required_skills") and resume.get("Skills"):
        job_skills = [skill.lower() for skill in job["required_skills"]]
        resume_skills = [skill.lower() for skill in resume["Skills"]]
        
        matched_skills = [skill for skill in resume_skills if any(job_skill in skill for job_skill in job_skills)]
        
        total_required = len(job_skills)
        matched_count = len(matched_skills)
        
        if total_required > 0:
            scores["skills_score"] = (matched_count / total_required) * 100
        
        scores["matched_skills"] = matched_skills
    
    if job.get("preferred_certifications") and resume.get("Certification"):
        job_certs = [cert.lower() for cert in job["preferred_certifications"]]
        resume_certs = [cert.lower() for cert in resume["Certification"]]
        
        matched_certs = [cert for cert in resume_certs if any(job_cert in cert for job_cert in job_certs)]
        
        total_preferred = len(job_certs)
        matched_count = len(matched_certs)
        
        if total_preferred > 0:
            scores["certifications_score"] = (matched_count / total_preferred) * 100
        
        scores["matched_certifications"] = matched_certs
    
    experience_score = 0
    if job.get("experience_requirements") and resume.get("Worked_As"):
        job_exp = [exp.lower() for exp in job["experience_requirements"]]
        resume_exp = [exp.lower() for exp in resume["Worked_As"]]
        
        matched_exp = [exp for exp in resume_exp if any(job_e in exp for job_e in job_exp)]
        
        total_required = len(job_exp)
        matched_count = len(matched_exp)
        
        if total_required > 0:
            experience_score = (matched_count / total_required) * 50 
        
        scores["matched_experience"] = matched_exp
    
    if job.get("min_years_experience") and resume.get("Years_Of_Experience"):
        years_pattern = r'(\d+)\s*(?:an|année|ans|year|years)'
        months_pattern = r'(\d+)\s*(?:mois|month|months)'
        
        total_months = 0
        for exp in resume["Years_Of_Experience"]:
            years_match = re.search(years_pattern, exp.lower())
            if years_match:
                total_months += int(years_match.group(1)) * 12
            
            months_match = re.search(months_pattern, exp.lower())
            if months_match:
                total_months += int(months_match.group(1))
        
        resume_years = total_months / 12
        required_years = job["min_years_experience"]
        
        if resume_years >= required_years:
            years_score = 50 
        else:
            years_score = (resume_years / required_years) * 50
        
        experience_score += years_score
        scores["years_of_experience"] = resume_years
    
    scores["experience_score"] = experience_score
    
    non_zero_scores = [score for score in [scores["skills_score"], scores["certifications_score"], scores["experience_score"]] if score > 0]
    if non_zero_scores:
        scores["overall_score"] = sum(non_zero_scores) / len(non_zero_scores)
    
    scores["candidate_name"] = resume.get("Name", "Unknown")
    
    return scores
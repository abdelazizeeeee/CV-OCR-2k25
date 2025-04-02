from fastapi import APIRouter, UploadFile, HTTPException
import os
import spacy
import fitz
import re
import tempfile
import shutil
from datetime import datetime
from src.models.resume_model import ResumeSchema, save_parsed_resume

resume_router = APIRouter()

@resume_router.post("/parse")
async def parse_resume_endpoint(file: UploadFile):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = parse_resume(temp_path)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to parse resume")
        
        result["file_name"] = file.filename
        result["uploaded_at"] = datetime.utcnow()
        
        validated_data = ResumeSchema(**result)
        save_parsed_resume(validated_data.dict())
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

def parse_resume(file_path):
    try:
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 "ResumeModel/output/model-best")
        nlp = spacy.load(model_path)
 
        doc = fitz.open(file_path)
 
        text_of_resume = " ".join([page.get_text() for page in doc])
 
        dic = {}
 
        doc = nlp(text_of_resume)
        for ent in doc.ents:
            dic.setdefault(ent.label_, []).append(ent.text)

        
 
        parsed_data = {
            "Name": dic.get('NAME', [None])[0],
            "LinkedIn_Link": re.sub('\n', '', dic.get('LINKEDIN LINK', [None])[0]) if dic.get('LINKEDIN LINK') else None,
            "Skills": dic.get('SKILLS', None),
            "Certification": dic.get('CERTIFICATION', None),
            "Worked_As": dic.get('WORKED AS', None),
            "Years_Of_Experience": dic.get('YEARS OF EXPERIENCE', [None])
        }
 
        return parsed_data
 
    except Exception as e:
        print(f"Exception Occurred: {str(e)}")
        return None

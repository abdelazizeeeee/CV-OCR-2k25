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

def extract_contact_info(text):
    phone_patterns = [
        r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',  
        r'\b(?:\+\d{1,3}[-.\s]?)?\d{10,12}\b',  
        r'\b(?:\+\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'  
    ]
    
    birthday_patterns = [
        r'\b(?:Birth(?:day|date)|DOB|Date\s+of\s+Birth)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        r'\b(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{2,4})\b',
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{2,4}\b'
    ]
    
    phone_number = None
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            phone_number = matches[0]
            break
    
    birthday = None
    for pattern in birthday_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            birthday = matches[0]
            break
    
    return {
        "phone_number": phone_number,
        "birthday": birthday
    }

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

        contact_info = extract_contact_info(text_of_resume)
        
        parsed_data = {
            "Name": dic.get('NAME', [None])[0],
            "LinkedIn_Link": re.sub('\n', '', dic.get('LINKEDIN LINK', [None])[0]) if dic.get('LINKEDIN LINK') else None,
            "Skills": dic.get('SKILLS', None),
            "Certification": dic.get('CERTIFICATION', None),
            "Worked_As": dic.get('WORKED AS', None),
            "Years_Of_Experience": dic.get('YEARS OF EXPERIENCE', [None])[0],
            "Phone_Number": contact_info["phone_number"],
            "Birthday": contact_info["birthday"]
        }
 
        return parsed_data
 
    except Exception as e:
        print(f"Exception Occurred: {str(e)}")
        return None
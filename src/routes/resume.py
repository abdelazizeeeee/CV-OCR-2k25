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
    print("Searching for phone numbers in text...")
    
    coordonnees_pattern = r'Coordonnées[\s\S]{1,200}?(\+216\s*\d{8}|\+216\s*\d{2}\s*\d{3}\s*\d{3}|\d{8}|\d{2}\s*\d{3}\s*\d{3})'
    mobile_pattern = r'(?:Mobile|Tel|Phone|Tél|GSM|Téléphone)(?::|.)?[\s:]*(\+216\s*\d{8}|\+216\s*\d{2}\s*\d{3}\s*\d{3}|\d{8}|\d{2}\s*\d{3}\s*\d{3})'
    
    phone_number = None
    
    coord_match = re.search(coordonnees_pattern, text, re.IGNORECASE)
    if coord_match:
        raw_number = coord_match.group(1)
        clean_number = re.sub(r'[^\d+]', '', raw_number)
        
        if len(clean_number) == 8 and not clean_number.startswith('+'):
            phone_number = f"+216{clean_number}"
        else:
            phone_number = clean_number
            
        print(f"Found phone number near Coordonnées: {phone_number}")
    
    if not phone_number:
        mobile_match = re.search(mobile_pattern, text, re.IGNORECASE)
        if mobile_match:
            raw_number = mobile_match.group(1)
            clean_number = re.sub(r'[^\d+]', '', raw_number)
            
            if len(clean_number) == 8 and not clean_number.startswith('+'):
                phone_number = f"+216{clean_number}"
            else:
                phone_number = clean_number
                
            print(f"Found phone number near Mobile/Tel label: {phone_number}")
    
    if not phone_number:
        mobile_label_match = re.search(r'(\d{8})\s*\(Mobile\)', text)
        if mobile_label_match:
            raw_number = mobile_label_match.group(1)
            phone_number = f"+216{raw_number}"
            print(f"Found phone number with (Mobile) label: {phone_number}")
    
    birthday_patterns = [
        r'\b(?:Birth(?:day|date)|DOB|Date\s+of\s+Birth)?\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        r'\b(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{2,4})\b',
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{2,4}\b'
    ]
    
    birthday = None
    for pattern in birthday_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            birthday = matches[0]
            print(f"Found birthday: {birthday}")
            break
    
    return {
        "phone_number": phone_number,
        "birthday": birthday
    }

def parse_resume(file_path):
    try:
        print("Parsing Resume...")
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 "ResumeModel/output/model-best")
        print(f"Model Path: {model_path}")
        
        if not os.path.exists(model_path):
            print(f"ERROR: Model path does not exist: {model_path}")
            return None
            
        try:
            nlp = spacy.load(model_path)
            print('Loaded Model')
        except Exception as model_error:
            print(f"ERROR loading model: {str(model_error)}")
            return None
            
        doc = fitz.open(file_path)
        print("Loading Resume...")
 
        text_of_resume = " ".join([page.get_text() for page in doc])
        print("Extracting Information...")
        dic = {}
 
        doc = nlp(text_of_resume)
        for ent in doc.ents:
            dic.setdefault(ent.label_, []).append(ent.text)

        print("the doc is   ")
        print(text_of_resume)
        
        contact_info = extract_contact_info(text_of_resume)
        print("Parsing Completed...") 
        
        experience = dic.get('YEARS OF EXPERIENCE', [])
        if experience and not isinstance(experience, list):
            experience = [experience]
        
        print(dic.get('NAME', [None])[0])
        if experience:
            print(experience[0])
        else:
            print("No years of experience found")
            
        parsed_data = {
            "Name": dic.get('NAME', [None])[0],
            "LinkedIn_Link": re.sub('\n', '', dic.get('LINKEDIN LINK', [None])[0]) if dic.get('LINKEDIN LINK') else None,
            "Skills": dic.get('SKILLS', None),
            "Certification": dic.get('CERTIFICATION', None),
            "Worked_As": dic.get('WORKED AS', None),
            "Years_Of_Experience": dic.get('YEARS OF EXPERIENCE', []),  
            "Phone_Number": contact_info["phone_number"],
            "Birthday": contact_info["birthday"]
        }
 
        return parsed_data
 
    except Exception as e:
        print(f"Exception Occurred: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None
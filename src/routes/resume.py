from fastapi import APIRouter, UploadFile, HTTPException
import os
import spacy
import fitz
import re
import tempfile
import shutil

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
 
        label_list = []
        text_list = []
        dic = {}
 
        doc = nlp(text_of_resume)
        for ent in doc.ents:
            label_list.append(ent.label_)
            text_list.append(ent.text)
 
        for i in range(len(label_list)):
            if label_list[i] in dic:
                dic[label_list[i]].append(text_list[i])
            else:
                dic[label_list[i]] = [text_list[i]]
 
        value_name = dic.get('NAME', [None])[0]
        value_linkedin = dic.get('LINKEDIN LINK', [None])[0]
        value_linkedin = re.sub('\n', '', value_linkedin) if value_linkedin else None
        value_skills = dic.get('SKILLS', None)
        value_certificate = dic.get('CERTIFICATION', None)
        value_workedAs = dic.get('WORKED AS', None)
        value_experience = dic.get('YEARS OF EXPERIENCE', None)
 
        parsed_data = {
            "Name": value_name,
            "LinkedIn_Link": value_linkedin,
            "Skills": value_skills,
            "Certification": value_certificate,
            "Worked_As": value_workedAs,
            "Years_Of_Experience": value_experience
        }
 
        return parsed_data
 
    except Exception as e:
        print(f"Exception Occurred: {str(e)}")
        return None 
import os
import re
import spacy
import fitz
import base64
from urllib.parse import parse_qs
from dotenv import load_dotenv
from passlib.context import CryptContext
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException, security

def is_valid_email(email: str) -> bool:
    pat = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if re.match(pat, email):
        return True
    return False


def is_valid_phone_number(phone_number: str) -> bool:
    pat = "^[0-9]{8}$"

    if re.match(pat, phone_number):
        return True
    return False


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def generate_verification_code():
    return secrets.token_urlsafe(6)


def get_smtp_connection():
    smtp_server = "smtp.sendgrid.net"
    smtp_port = 587
    smtp_username = "apikey"
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    smtp_password = sendgrid_api_key
    smtp_from_email = "oussema.benhassena@horizon-tech.tn"
    return smtp_server, smtp_port, smtp_username, smtp_password, smtp_from_email


async def send_verification_email(to_email: str, verification_code: str):
    (
        smtp_server,
        smtp_port,
        smtp_username,
        smtp_password,
        smtp_from_email,
    ) = get_smtp_connection()

    # Create the MIME message
    subject = "Email Verification Code"
    body = f"Your verification code is: {verification_code}"

    message = MIMEMultipart()
    message["From"] = smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from_email, to_email, message.as_string())



def parse_resume(file_path):
    try:
        # Load spaCy model for entity recognitio
        nlp = spacy.load('/app/src/resume-model/ResumeModel/output/model-best')
 
        # Open the resume file
        doc = fitz.open(file_path)
 
        # Extract text from the resume
        text_of_resume = " ".join([page.get_text() for page in doc])
 
        label_list = []
        text_list = []
        dic = {}
 
        doc = nlp(text_of_resume)
        for ent in doc.ents:
            label_list.append(ent.label_)
            text_list.append(ent.text)
 
        # Organize extracted information into a dictionary
        for i in range(len(label_list)):
            if label_list[i] in dic:
                dic[label_list[i]].append(text_list[i])
            else:
                dic[label_list[i]] = [text_list[i]]
 
        # Extract specific information
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
 
# # Example usage:
# resume_file_path = "cv-pipline/input_data/Profile.pdf"
# text_file_path, parsed_data = parse_resume(resume_file_path)
 
# if text_file_path and parsed_data:
#     print(f"Text of the resume saved to: {text_file_path}")
#     print("Parsed Resume Data:")
#     print(parsed_data)
# else:
#     print("Failed to parse resume.")
 
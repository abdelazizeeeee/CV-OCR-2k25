from beanie import Document
from pydantic import BaseModel
from typing import List, Optional


class Application(Document):
    offre_id: int
    cv_file: str
    years_of_experience: Optional[List[str]]
    skills: Optional[List[str]]
    worked_as: Optional[List[str]]
    certificate: Optional[List[str]]
    name: Optional[str]
    linkedin_link: Optional[str]
    user_id: Optional[str]


class ApplicationIn(BaseModel):
    offre_id: int
    cv_file: bytes

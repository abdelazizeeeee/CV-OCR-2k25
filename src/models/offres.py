from beanie import Document # type: ignore
from pydantic import BaseModel


class Offre(Document):
    years_of_experience: int
    domain: list[str]
    stack: list[str]
    diploma: list[str]
    offre_id: int


class OffreIn(BaseModel):
    years_of_experience: int
    domain: list[str]
    stack: list[str]
    diploma: list[str]

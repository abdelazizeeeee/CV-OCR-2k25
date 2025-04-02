from pydantic import BaseModel
from datetime import datetime


class User_id(BaseModel):
    user_id: str

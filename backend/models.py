# models.py
from pydantic import BaseModel
from typing import List
from datetime import datetime

class UserCreate(BaseModel):
    user_id: str
    user_name: str

class User(BaseModel):
    user_id: str
    user_name: str

class ReviewCreate(BaseModel):
    program_id: str
    program_title: str
    user_id: str
    rating: int
    review_text: str

class Review(BaseModel):
    review_id: str
    program_id: str
    program_title: str
    user_id: str
    rating: int
    review_text: str
    created_at: datetime

from datetime import datetime
from typing import List
from pydantic import BaseModel

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    tokens_used: int
    cost: float

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    created_at: datetime
    messages: List[MessageResponse] = []
    total_cost: float
    
    class Config:
        from_attributes = True
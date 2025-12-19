from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship

from app.database import Base

class ChatSession(Base):
    __tablename__ = "sessions" 
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_cost = Column(Float, default=0.0)
    
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String)  
    content = Column(Text) 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tokens_used = Column(Integer, default=0) 
    cost = Column(Float, default=0.0)  

    session = relationship("ChatSession", back_populates="messages")
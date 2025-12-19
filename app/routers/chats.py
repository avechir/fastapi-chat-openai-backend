from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
import app.models as models
import app.schemas as schemas
from app.services import chat_service
from app.logger import logger

router = APIRouter()

@router.post("/chats", response_model=schemas.SessionResponse)
def create_session(db: Session = Depends(get_db)):
    new_session = models.ChatSession()
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.info(f"Created new session ID: {new_session.id}")
    return new_session

@router.post("/chats/{session_id}/messages", response_model=schemas.MessageResponse)
def send_message(session_id: int, msg: schemas.MessageCreate, db: Session = Depends(get_db)):

    # check session existence
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # save user text to db
    user_message = models.Message(session_id=session_id, role="user", content=msg.content)
    db.add(user_message)
    db.commit()
    logger.info(f"Session {session_id}. User sent message: '{msg.content[:20]}...'")

    # ai answer
    history = [{"role": m.role, "content": m.content} for m in session.messages]
    try:
        assistant_text, prompt_tokens, response_tokens = chat_service.get_response(history)
    except Exception as e:
        logger.error(f"OpenAI Error in session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")
    
    input_cost, output_cost = chat_service.calculate_cost(prompt_tokens, response_tokens)
    user_message.tokens_used = prompt_tokens
    user_message.cost = input_cost
    db.add(user_message)

    # save ai text
    assistant_message = models.Message(
        session_id=session_id,
        role="assistant",
        content=assistant_text,
        tokens_used=response_tokens,
        cost=output_cost
    )
    db.add(assistant_message)
    current_total = session.total_cost or 0.0
    session.total_cost = current_total + output_cost + input_cost
    
    db.commit()
    db.refresh(assistant_message)
    logger.info(f"Session {session_id}. AI answered, cost: {input_cost + output_cost:.8f}")
    return assistant_message

@router.get("/chats/{session_id}", response_model=schemas.SessionResponse)
def get_chat_history(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session:
        logger.warning(f"Get history failed: Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info(f"Session {session_id} history retrieved")
    return session

@router.delete("/chats/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):

    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    logger.info(f"Session {session_id} has been deleted")
    return {"message": f"Session {session_id} has been deleted."}
import os
import time
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from openai import OpenAI
from dotenv import load_dotenv
from database import engine, get_db
import dbstructure
import schemas

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-5-nano"
dbstructure.Base.metadata.create_all(bind=engine)

if API_KEY:
    client = OpenAI(api_key=API_KEY)
    print('there is a key')
else:
    print('no key')
    client = OpenAI(api_key="sk-demo-mode-key")

# client = OpenAI(api_key=API_KEY)

PRICE_PER_1M_INPUT = 0.05  
PRICE_PER_1M_OUTPUT = 0.4

def calculate_cost(input_tokens, output_tokens):
    input_cost = (input_tokens / 1000000) * PRICE_PER_1M_INPUT
    output_cost = (output_tokens / 1000000) * PRICE_PER_1M_OUTPUT
    return input_cost + output_cost

app = FastAPI(title="Chat API")

@app.post("/chats", response_model=schemas.SessionResponse)
def create_session(db: Session = Depends(get_db)):
    new_session = dbstructure.ChatSession()
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@app.post("/chats/{session_id}/messages", response_model=schemas.MessageResponse)
def send_message(session_id: int, msg: schemas.MessageCreate, db: Session = Depends(get_db)):

    # check session existence
    session = db.query(dbstructure.ChatSession).filter(dbstructure.ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # save user text to db
    user_message = dbstructure.Message(session_id=session_id, role="user", content=msg.content)
    db.add(user_message)
    db.commit()

    # ai answer
    prompt_tokens = 0
    completion_tokens = 0
    if not API_KEY:
        time.sleep(1) 
        assistant_text = f"no key. could be answer for '{msg.content}'"
        prompt_tokens = 10
        completion_tokens = 20
    else:
        history = [{"role": m.role, "content": m.content} for m in session.messages]
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=history
            )
            assistant_text = response.choices[0].message.content
            usage = response.usage
            prompt_tokens = usage.prompt_tokens         
            completion_tokens = usage.completion_tokens
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")

    total_tokens = prompt_tokens + completion_tokens
    cost_amount = calculate_cost(prompt_tokens, completion_tokens)

    # save ai text
    assistant_message = dbstructure.Message(
        session_id=session_id,
        role="assistant",
        content=assistant_text,
        tokens_used=total_tokens,
        cost=cost_amount
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    return assistant_message

@app.get("/chats/{session_id}", response_model=schemas.SessionResponse)
def get_chat_history(session_id: int, db: Session = Depends(get_db)):
    session = db.query(dbstructure.ChatSession).filter(dbstructure.ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.delete("/chats/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):

    session = db.query(dbstructure.ChatSession).filter(dbstructure.ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    
    return {"message": f"Session {session_id} has been deleted."}
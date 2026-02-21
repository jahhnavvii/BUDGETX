"""
BudgetX - Chat Module (Refactored for SQLAlchemy)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import json
import os
from auth import verify_token
from database import get_db, ChatMessage, UploadedFile

router = APIRouter(prefix="/api", tags=["chat"])

genai = None
model = None

def _init_gemini():
    global genai, model
    if model is not None: return
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Debug: check if file exists
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                if "GEMINI_API_KEY=" in f.read():
                    print("DEBUG: .env exists and contains key, but os.environ doesn't have it.")
        return

    
    try:
        import google.generativeai as _genai
        _genai.configure(api_key=api_key)
        
        # Probing available models...
        probe_models = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-2.0-flash-exp", "models/gemini-2.0-flash-exp", "gemini-pro"]
        for m_name in probe_models:
            try:
                temp_model = _genai.GenerativeModel(m_name)
                # Test the model with a tiny prompt
                temp_model.generate_content("test")
                genai = _genai
                model = temp_model
                print(f"Successfully initialized Gemini with model: {m_name}")
                return
            except Exception:
                continue
        print("Gemini initialized but all probed models failed.")
    except Exception as e:
        print(f"Gemini initialization error: {str(e)}")





SYSTEM_PROMPT = """You are BudgetX AI, a financial optimization assistant. Be concise, professional, and friendly. Base answers on provided numbers. Format lists with dashes."""

class ChatRequest(BaseModel):
    message: str
    file_id: Optional[int] = None

@router.post("/chat")
async def chat(req: ChatRequest, current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    _init_gemini()
    user_id = current_user["user_id"]
    analytics_context = ""
    if req.file_id:
        f = db.query(UploadedFile).filter(UploadedFile.id == req.file_id, UploadedFile.user_id == user_id).first()
        if f and f.analytics_json:
            analytics_context = f"\n\nContext:\n{f.analytics_json}\n"

    new_msg = ChatMessage(user_id=user_id, role="user", content=req.message)
    db.add(new_msg)
    db.commit()

    ai_reply = ""
    if model:
        try:
            history = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
            prompt = SYSTEM_PROMPT + analytics_context + "\n".join([f"{m.role}: {m.content}" for m in reversed(history)])
            response = model.generate_content(prompt)
            ai_reply = response.text.strip()
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            ai_reply = f"I'm having trouble reaching the AI service (Error: {str(e)}). Please verify your Gemini API key in the .env file or your system environment variables."
    else:
        print("Gemini API Key missing: No 'GEMINI_API_KEY' found in .env or environment.")
        ai_reply = "Gemini API Key is missing. Please add 'GEMINI_API_KEY=your_key' to the backend/.env file and restart the server."


    assistant_msg = ChatMessage(user_id=user_id, role="assistant", content=ai_reply)
    db.add(assistant_msg)
    db.commit()
    return {"role": "assistant", "content": ai_reply}

@router.get("/chat/history")
def get_history(current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    history = db.query(ChatMessage).filter(ChatMessage.user_id == current_user["user_id"]).order_by(ChatMessage.timestamp.asc()).all()
    return [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in history]

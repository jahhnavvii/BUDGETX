"""
BudgetX - Chat Module (Refactored for SQLAlchemy)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
from auth import verify_token
from database import get_db, ChatMessage, UploadedFile

load_dotenv()

router = APIRouter(prefix="/api", tags=["chat"])

# Global AI state
ai_model = None

def _init_gemini():
    global ai_model
    if ai_model is not None:
        return
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return


    
    try:
        genai.configure(api_key=api_key, transport='rest')
        # Proactively find the best available flash/pro model
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority: flash-latest, flash, flash-exp, pro
        priority = ["models/gemini-1.5-flash-latest", "models/gemini-1.5-flash", "models/gemini-2.0-flash-exp", "models/gemini-pro"]
        target_model = None
        for p in priority:
            if p in available_models:
                target_model = p
                break
        
        if not target_model and available_models:
            target_model = available_models[0]
            
        if target_model:
            ai_model = genai.GenerativeModel(target_model)
            print(f"Gemini AI Initialized with model: {target_model}")
        else:
            print("CRITICAL: No flash or pro models found for this API key.")
    except Exception as e:
        print(f"Gemini API Init Error: {str(e)}")






async def get_auto_analysis(analytics_json: str):
    """Programmatic access to Gemini for auto-analysis on upload"""
    _init_gemini()
    if ai_model is None:
        return "AI analysis unavailable (key missing)."
    
    prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{analytics_json}\n\nPlease provide a brief, professional summary of this data and highlight 2-3 key takeaway insights."
    try:
        response = ai_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Auto-analysis failed: {str(e)}"

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
    if ai_model is not None:
        try:
            history = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
            prompt = SYSTEM_PROMPT + analytics_context + "\n".join([f"{m.role}: {m.content}" for m in reversed(history)])
            response = ai_model.generate_content(prompt)
            ai_reply = response.text.strip()
        except Exception as e:
            print(f"Gemini API Request Error: {str(e)}")
            ai_reply = f"I'm having trouble reaching the AI service (Error: {str(e)}). Please verify your Gemini API key."
    else:
        ai_reply = "Gemini API Key is missing or service failed to initialize. Please check your backend/.env file."


    assistant_msg = ChatMessage(user_id=user_id, role="assistant", content=ai_reply)
    db.add(assistant_msg)
    db.commit()
    return {"role": "assistant", "content": ai_reply}

@router.get("/chat/history")
def get_history(current_user: dict = Depends(verify_token), db: Session = Depends(get_db)):
    history = db.query(ChatMessage).filter(ChatMessage.user_id == current_user["user_id"]).order_by(ChatMessage.timestamp.asc()).all()
    return [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in history]

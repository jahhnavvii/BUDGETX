"""
BudgetX - Chat Module
Handles the AI chat interface powered by Google Gemini 1.5 Flash.
LLM is used ONLY for explanation — analytics are deterministic.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json
import os
from auth import verify_token
import database

router = APIRouter(prefix="/api", tags=["chat"])

# ---------------------------------------------------------------------------
# Gemini setup
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

genai = None
model = None

def _init_gemini():
    global genai, model
    if genai is not None:
        return
    if not GEMINI_API_KEY:
        return
    try:
        import google.generativeai as _genai
        _genai.configure(api_key=GEMINI_API_KEY)
        genai = _genai
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        pass


SYSTEM_PROMPT = """You are BudgetX AI, a financial optimization assistant.
You help users understand their spending patterns and provide actionable advice.

Rules:
- Be concise, professional, and friendly.
- When analytics data is provided, base your answers on the ACTUAL numbers.
- Do NOT invent or hallucinate financial figures.
- Provide specific, actionable recommendations.
- Use plain language — no emojis, no markdown headers.
- Format lists with dashes, keep responses under 300 words unless asked for detail.
"""


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    file_id: Optional[int] = None  # optional: attach analytics context


class ChatMessage(BaseModel):
    role: str
    content: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat")
async def chat(req: ChatRequest, current_user: dict = Depends(verify_token)):
    """Send a message and get an AI response."""
    _init_gemini()

    user_id = current_user["user_id"]

    # Build context from analytics if a file_id is provided
    analytics_context = ""
    if req.file_id:
        f = database.get_file_by_id(req.file_id, user_id)
        if f and f["analytics_json"]:
            analytics = json.loads(f["analytics_json"])
            analytics_context = (
                f"\n\nUser's financial analytics (from uploaded CSV '{f['original_filename']}'):\n"
                f"{json.dumps(analytics, indent=2)}\n"
            )

    # Save user message to DB
    database.save_chat_message(user_id, "user", req.message)

    # Build conversation history for the LLM
    history = database.get_chat_history(user_id, limit=20)

    if model is not None:
        try:
            # Construct messages for Gemini
            prompt_parts = [SYSTEM_PROMPT + analytics_context + "\n\nConversation:\n"]
            for msg in history:
                role_label = "User" if msg["role"] == "user" else "BudgetX AI"
                prompt_parts.append(f"{role_label}: {msg['content']}\n")
            prompt_parts.append("BudgetX AI:")

            full_prompt = "".join(prompt_parts)
            response = model.generate_content(full_prompt)
            ai_reply = response.text.strip()
        except Exception as e:
            ai_reply = f"I encountered an issue generating a response. Please try again. (Error: {str(e)})"
    else:
        # Fallback when Gemini is not configured
        if analytics_context:
            # Provide a basic deterministic summary
            try:
                analytics = json.loads(database.get_file_by_id(req.file_id, user_id)["analytics_json"])
                ai_reply = _generate_fallback_response(req.message, analytics)
            except Exception:
                ai_reply = (
                    "Gemini API key is not configured. "
                    "Set the GEMINI_API_KEY environment variable to enable AI-powered responses. "
                    "Your financial data has been analyzed — check the analytics panel for details."
                )
        else:
            ai_reply = (
                "Welcome to BudgetX. I can help you analyze your finances. "
                "Upload a CSV file with your financial data (columns: date, category, amount, type) "
                "and I will provide personalized insights and recommendations. "
                "Note: Set the GEMINI_API_KEY environment variable for full AI-powered analysis."
            )

    # Save AI response to DB
    database.save_chat_message(user_id, "assistant", ai_reply)

    return {"role": "assistant", "content": ai_reply}


@router.get("/chat/history")
def get_history(current_user: dict = Depends(verify_token)):
    """Return the current user's chat history."""
    history = database.get_chat_history(current_user["user_id"], limit=100)
    return history


@router.delete("/chat/history")
def clear_history(current_user: dict = Depends(verify_token)):
    """Clear the current user's chat history."""
    database.clear_chat_history(current_user["user_id"])
    return {"message": "Chat history cleared"}


# ---------------------------------------------------------------------------
# Fallback response (no Gemini)
# ---------------------------------------------------------------------------

def _generate_fallback_response(message: str, analytics: dict) -> str:
    """Generate a basic response from analytics without the LLM."""
    lines = ["Based on your financial data:"]
    lines.append(f"- Total Income: ${analytics.get('total_income', 0):,.2f}")
    lines.append(f"- Total Expenses: ${analytics.get('total_expenses', 0):,.2f}")
    lines.append(f"- Net Surplus: ${analytics.get('net_surplus', 0):,.2f}")
    lines.append(f"- Savings Rate: {analytics.get('savings_rate', 0):.1f}%")

    overspending = analytics.get("overspending_flags", [])
    if overspending:
        lines.append("\nOverspending detected in:")
        for flag in overspending:
            lines.append(f"- {flag['category']}: {flag['percentage']:.1f}% of expenses (${flag['amount']:,.2f})")

    lines.append(
        "\nFor detailed AI-powered recommendations, configure your GEMINI_API_KEY environment variable."
    )
    return "\n".join(lines)

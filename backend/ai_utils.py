"""
BudgetX - AI Utilities for Gemini
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

ai_model = None

def get_gemini_model():
    """Returns an initialized Gemini model."""
    global ai_model
    if ai_model is not None:
        return ai_model
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("CRITICAL: GEMINI_API_KEY not found in environment.")
        return None

    try:
        genai.configure(api_key=api_key, transport='rest')
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
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
            return ai_model
        else:
            print("CRITICAL: No flash or pro models found for this API key.")
            return None
    except Exception as e:
        print(f"Gemini API Init Error: {str(e)}")
        return None

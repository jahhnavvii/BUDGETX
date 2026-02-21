import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

def test_model(model_name):
    print(f"Testing {model_name}...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello")
        print(f"Success! {model_name} responded: {response.text[:50]}...")
        return True
    except Exception as e:
        print(f"Failed {model_name}: {str(e)}")
        return False

models_to_test = ["models/gemini-1.5-flash", "gemini-1.5-flash", "models/gemini-2.0-flash-exp", "gemini-pro"]

for m in models_to_test:
    if test_model(m):
        print(f"\nUSE THIS MODEL: {m}")
        break

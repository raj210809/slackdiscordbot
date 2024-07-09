import google.generativeai as genai
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def generate_response(user_text):
    try:
        response = model.generate_content(user_text)
        return response.text
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I couldn't generate any response."

#test
#print(generate_response("Is Earth flat?"))
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print(f"Testing model: gemini-2.5-flash")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello, identify yourself."
    )
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

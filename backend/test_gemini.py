import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("ERROR: Gemini API key not found in .env")
    raise SystemExit(1)

try:
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents="Say hello in one short sentence."
    )

    print("\nSUCCESS: Gemini API is working!")
    print("Gemini response:")
    print(response.text)

except Exception as e:
    print("\nFAILED: Gemini API test did not work.")
    print("Error:", str(e))
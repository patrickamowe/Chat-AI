from google import genai

from ..core.config import settings

# Automatically grabs your GEMINI_API_KEY environment variable
client = genai.Client(api_key=settings.GEMINI_API_KEY)
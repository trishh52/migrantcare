import os
import sys
import io
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Configure Gemini with the API key from the environment
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

genai.configure(api_key=api_key)

# Create the Gemini model
model = genai.GenerativeModel('gemini-2.5-flash')

# Call the model with the prompt
prompt = "Summarize this in simple Hindi: A migrant worker needs to find the nearest hospital"
response = model.generate_content(prompt)

# Print the response text (handling encoding for Windows console)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(response.text)

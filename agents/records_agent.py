import sys
import os
import json
import io
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Fix windows console encoding for Hindi text
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path to allow importing from database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import SupabaseClient

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure Gemini with the API key from the environment
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

genai.configure(api_key=api_key)

class RecordsAgent:
    def __init__(self):
        self.client = SupabaseClient()
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def add_record(self, worker_id, raw_text):
        prompt = f"""
        Extract the following information from the medical text below.
        Return ONLY a JSON object with keys 'diagnosis', 'medication', and 'dosage'.
        If multiple medications or dosages, join them with commas. If a field is missing, use 'Unknown'.
        Text: {raw_text}
        """
        response = self.model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError:
            print("Failed to parse JSON from Gemini response:", response_text)
            extracted_data = {"diagnosis": "Unknown", "medication": "Unknown", "dosage": "Unknown"}

        data = {
            "worker_id": worker_id,
            "diagnosis": extracted_data.get("diagnosis", "Unknown"),
            "medication": extracted_data.get("medication", "Unknown"),
            "dosage": extracted_data.get("dosage", "Unknown")
        }

        try:
            res = self.client.supabase.table("health_records").insert(data).execute()
            return res
        except Exception as e:
            print(f"Error saving to health_records: {e}")
            return None

    def get_summary(self, worker_id):
        try:
            res = self.client.supabase.table("health_records").select("*").eq("worker_id", worker_id).execute()
            
            # Handle different supabase-py versions returning data differently
            records = getattr(res, 'data', res)
            if isinstance(records, dict) and 'data' in records:
                records = records['data']
            elif not isinstance(records, list):
                records = []
                
            if not records:
                return "Koi health records nahi mile."
                
            records_text = "\n".join([f"- Diagnosis: {r.get('diagnosis')}, Medication: {r.get('medication')} ({r.get('dosage')})" for r in records])
            
            prompt = f"""
            Here are the health records for a patient:
            {records_text}
            Generate a 5-line summary in simple plain Hindi explaining the patient's health status and history.
            """
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error getting summary: {e}")
            return f"Error: {e}"

    def get_emergency_info(self, worker_id):
        try:
            # Get worker info
            worker_res = self.client.supabase.table("workers").select("*").eq("id", worker_id).execute()
            worker_data = getattr(worker_res, 'data', worker_res)
            
            if isinstance(worker_data, dict) and 'data' in worker_data:
                worker_data = worker_data['data']
            
            if not worker_data or (isinstance(worker_data, list) and len(worker_data) == 0):
                return "Worker not found."
                
            worker = worker_data[0] if isinstance(worker_data, list) else worker_data
            
            # Get medications from health_records
            records_res = self.client.supabase.table("health_records").select("medication").eq("worker_id", worker_id).execute()
            records_data = getattr(records_res, 'data', records_res)
            
            if isinstance(records_data, dict) and 'data' in records_data:
                records_data = records_data['data']
            elif not isinstance(records_data, list):
                records_data = []
                
            medications = [r.get('medication') for r in records_data if r.get('medication') and str(r.get('medication')).lower() != 'unknown']
            medications_str = ", ".join(set(medications)) if medications else "None"
            
            blood_group = worker.get('blood_group', 'Unknown')
            allergies = worker.get('allergies', 'Unknown')
            
            return f"Emergency Info - Blood Group: {blood_group} | Allergies: {allergies} | Current Medications: {medications_str}"
        except Exception as e:
            print(f"Error getting emergency info: {e}")
            return f"Error: {e}"

if __name__ == '__main__':
    agent = RecordsAgent()
    test_worker_id = 'c9a188d4-84f8-4bdc-b119-7e6174cc0261'
    
    print(f"Testing add_record for worker {test_worker_id}...")
    raw_text = 'Patient has diabetes, prescribed Metformin 500mg twice daily'
    res = agent.add_record(test_worker_id, raw_text)
    print("Add record result:", res)
    
    print(f"\nTesting get_summary for worker {test_worker_id}...")
    summary = agent.get_summary(test_worker_id)
    print("Summary (in Hindi):\n" + summary)
    
    print(f"\nTesting get_emergency_info for worker {test_worker_id}...")
    info = agent.get_emergency_info(test_worker_id)
    print("Emergency Info:", info)

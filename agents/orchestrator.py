import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path to allow importing agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.identity_agent import IdentityAgent
from agents.records_agent import RecordsAgent
from agents.clinic_agent import ClinicAgent

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

class Orchestrator:
    def __init__(self):
        self.identity_agent = IdentityAgent()
        self.records_agent = RecordsAgent()
        self.clinic_agent = ClinicAgent()
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def detect_intent(self, message):
        prompt = f"""
        Classify the following user message into exactly ONE of these intents: 
        REGISTER, FETCH_RECORDS, ADD_RECORD, FIND_CLINIC, EMERGENCY, UNKNOWN.
        Return ONLY the intent word, nothing else.
        
        Message: "{message}"
        """
        try:
            response = self.model.generate_content(prompt)
            intent = response.text.strip().upper()
            
            valid_intents = ["REGISTER", "FETCH_RECORDS", "ADD_RECORD", "FIND_CLINIC", "EMERGENCY", "UNKNOWN"]
            for valid in valid_intents:
                if valid in intent:
                    return valid
            return "UNKNOWN"
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return "UNKNOWN"

    def handle_message(self, phone_number, message):
        intent = self.detect_intent(message)
        
        user_data = self.identity_agent.verify_user(phone_number)
        worker_id = user_data.get('id') if user_data else None

        if intent == "REGISTER":
            if user_data:
                return "Aap already registered hain"
            else:
                return "Kripya apna naam, blood group, allergies aur medical conditions batayein."
                
        elif intent == "FETCH_RECORDS":
            if not worker_id:
                return "Kripya pehle register karein."
            return self.records_agent.get_summary(worker_id)
            
        elif intent == "FIND_CLINIC":
            match = re.search(r'\b\d{6}\b', message)
            if match:
                pincode = match.group()
                return self.clinic_agent.find_nearby(pincode)
            else:
                return "Kripya 6-digit pincode message mein likhein, jaise: clinic dhoondo 110001"
                
        elif intent == "EMERGENCY":
            if not worker_id:
                return "Kripya pehle register karein."
            return self.records_agent.get_emergency_info(worker_id)
            
        elif intent == "ADD_RECORD":
            if not worker_id:
                return "Kripya pehle register karein."
            self.records_agent.add_record(worker_id, message)
            return "Aapka health record add ho gaya hai."
            
        else: # UNKNOWN
            return "Maaf kijiye, main aapki baat samajh nahi paya. Kripya apna sawal safar tarike se puchein. (Jaise: 'register karna hai', 'records dikhao', 'clinic 110001', 'emergency')"

if __name__ == '__main__':
    import io
    
    # Fix windows console encoding for Hindi text
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
    orchestrator = Orchestrator()
    phone = "8888888888"
    
    test_messages = [
        "Mujhe naya account banana hai",
        "Mera purana health records ka summary dikhao",
        "Mujhe kal raat bukhar tha aur maine paracetamol khayi",
        "Mera pincode 110001 hai, aas paas clinic batao",
        "Emergency hai, jaldi madad karo",
        "Tum kaun ho?"
    ]
    
    for msg in test_messages:
        print(f"\nUser ({phone}): {msg}")
        response = orchestrator.handle_message(phone, msg)
        print(f"Bot: {response}")

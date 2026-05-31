import sys
import os

# Add parent directory to path to allow importing from database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import SupabaseClient

class IdentityAgent:
    def __init__(self):
        self.client = SupabaseClient()

    def verify_user(self, phone_number):
        try:
            response = self.client.get_worker_by_phone(phone_number)
            if response and hasattr(response, 'data') and response.data:
                return response.data[0]
            # Fallback for dict-like response
            elif isinstance(response, dict) and response.get('data'):
                return response['data'][0]
            elif response and not hasattr(response, 'data') and isinstance(response, list) and len(response) > 0:
                return response[0]
            return None
        except Exception as e:
            print(f"Error verifying user: {e}")
            return None

    def register_user(self, phone_number, name, blood_group, allergies, conditions):
        try:
            self.client.create_worker(phone_number, name, blood_group, allergies, conditions)
            return "Aapka registration ho gaya!"
        except Exception as e:
            return f"Error: {str(e)}"

if __name__ == '__main__':
    agent = IdentityAgent()
    
    print("Registering user with phone 8888888888...")
    reg_response = agent.register_user(
        phone_number="8888888888",
        name="Test User 888",
        blood_group="A+",
        allergies="None",
        conditions="None"
    )
    print(reg_response)
    
    print("\nVerifying user with phone 8888888888...")
    user_data = agent.verify_user("8888888888")
    if user_data:
        print("User verified. Data:", user_data)
    else:
        print("User not found.")

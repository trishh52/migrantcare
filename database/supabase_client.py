import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

class SupabaseClient:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file")
        self.supabase: Client = create_client(url, key)

    def create_worker(self, phone_number, name, blood_group, allergies, conditions):
        """Inserts a new worker into the workers table."""
        data = {
            "phone_number": phone_number,
            "name": name,
            "blood_group": blood_group,
            "allergies": allergies,
            "chronic_conditions": conditions
        }
        response = self.supabase.table("workers").insert(data).execute()
        return response

    def get_worker_by_phone(self, phone_number):
        """Fetches a worker by their phone number."""
        try:
            response = self.supabase.table("workers").select("*").eq("phone_number", phone_number).execute()
            return response
        except Exception as e:
            if "permission" in str(e).lower() or "denied" in str(e).lower():
                return None
            raise

if __name__ == '__main__':
    # Initialize the client
    client = SupabaseClient()
    
    # Create a test worker
    print("Creating test worker with phone 9999999999...")
    try:
        create_res = client.create_worker(
            phone_number="9999999999",
            name="Test User",
            blood_group="O+",
            allergies="None",
            conditions="None"
        )
        print("Create response:", create_res)
    except Exception as e:
        print("Failed to create worker:", e)

    # Fetch the test worker
    print("\nFetching worker with phone 9999999999...")
    try:
        fetch_res = client.get_worker_by_phone("9999999999")
        print("Fetch response:", fetch_res)
    except Exception as e:
        print("Failed to fetch worker:", e)

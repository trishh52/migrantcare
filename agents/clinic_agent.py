import requests
import sys
import io

class ClinicAgent:
    def find_nearby(self, pincode):
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': f'government hospital near {pincode} India',
            'format': 'json',
            'limit': 3
        }
        headers = {
            'User-Agent': 'MigrantCare/1.0'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return "क्षमा करें, इस पिनकोड के पास कोई सरकारी अस्पताल या PHC नहीं मिला।"
            
            message = "आपके पिनकोड के पास स्थित 3 सरकारी अस्पताल इस प्रकार हैं:\n\n"
            for idx, place in enumerate(data, start=1):
                name = place.get('name', 'अस्पताल')
                if not name:
                    name = "सरकारी अस्पताल"
                address = place.get('display_name', 'पता उपलब्ध नहीं')
                message += f"{idx}. {name}\nपता: {address}\n\n"
            
            return message.strip()
        except requests.RequestException as e:
            return f"अस्पतालों की खोज करते समय नेटवर्क त्रुटि हुई: {e}"
        except Exception as e:
            return f"त्रुटि: {e}"

if __name__ == '__main__':
    # Fix windows console encoding for Hindi text
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        
    agent = ClinicAgent()
    test_pincode = '110001'
    print(f"Testing find_nearby for pincode {test_pincode}...\n")
    
    result = agent.find_nearby(test_pincode)
    print(result)

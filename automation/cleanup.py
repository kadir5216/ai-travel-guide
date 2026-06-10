import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_url = os.getenv("STRAPI_URL", "http://localhost:1337").rstrip("/")
token = os.getenv("STRAPI_API_TOKEN", "")
headers = {"Authorization": f"Bearer {token}"}

def run_cleanup():
    print("Fetching all places...")
    response = requests.get(f"{api_url}/api/places?populate=*", headers=headers)
    if response.status_code != 200:
        print("Failed to fetch places:", response.text)
        return
        
    data = response.json()
    places = data.get("data", [])
    print(f"Found {len(places)} total places.")
    
    seen = {}
    to_delete = []
    
    for place in places:
        # Handle both Strapi v4 and v5 structures
        pid = place.get("documentId") or place.get("id")
        attrs = place.get("attributes", place)
        
        desc_en = attrs.get("description_en")
        
        city_data = attrs.get("city", {})
        city_id = None
        if isinstance(city_data, dict):
            if "data" in city_data and city_data["data"]:
                city_id = city_data["data"].get("id")
            else:
                city_id = city_data.get("id")
                
        # Group by city and english description to identify exact duplicates
        key = f"{city_id}_{desc_en}"
        
        if key in seen:
            existing_pid = seen[key]["id"]
            existing_attrs = seen[key]["attrs"]
            
            # If current place has name_en but existing doesn't, current is the new one
            if attrs.get("name_en") and not existing_attrs.get("name_en"):
                to_delete.append(existing_pid)
                seen[key] = {"id": pid, "attrs": attrs}
            else:
                to_delete.append(pid)
        else:
            seen[key] = {"id": pid, "attrs": attrs}
            
    print(f"Found {len(to_delete)} duplicate places to delete.")
    
    for pid in to_delete:
        print(f"Deleting duplicate place {pid}...")
        del_url = f"{api_url}/api/places/{pid}"
        res = requests.delete(del_url, headers=headers)
        if res.status_code in [200, 204]:
            print("Successfully deleted.")
        else:
            print(f"Failed to delete {pid}: {res.status_code} {res.text}")

if __name__ == "__main__":
    run_cleanup()

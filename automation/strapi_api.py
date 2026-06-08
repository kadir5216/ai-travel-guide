import os
import requests
import logging

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class StrapiAPI:
    """
    Helper class to communicate with Strapi CMS REST API.
    """
    def __init__(self, api_url=None, token=None):
        self.api_url = api_url or os.getenv("STRAPI_URL", "http://localhost:1337")
        self.token = token or os.getenv("STRAPI_API_TOKEN", "")
        
        # Base headers. Do not specify Content-Type here because 
        # file uploads require multipart boundaries set by the requests package.
        self.headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        # Test the connection settings
        if not self.token:
            logger.warning("STRAPI_API_TOKEN is empty. API requests might fail if public permissions are not configured.")

    def get_or_create_city(self, name: str, country: str, short_info: str) -> int:
        """
        Checks if a city exists by name. If it does, returns its ID. If not, creates it.
        
        Args:
            name (str): City name.
            country (str): Country name.
            short_info (str): Short description of the city.
            
        Returns:
            int: City ID or None if error.
        """
        url = f"{self.api_url}/api/cities"
        params = {
            "filters[name][$eq]": name
        }
        
        try:
            logger.info(f"Checking if city '{name}' exists in Strapi...")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # If city exists, return its ID
            if data.get("data") and len(data["data"]) > 0:
                city_id = data["data"][0]["id"]
                logger.info(f"City '{name}' found. ID: {city_id}")
                return city_id
            
            # If not, create it
            logger.info(f"City '{name}' not found. Creating a new record...")
            payload = {
                "data": {
                    "name": name,
                    "country": country,
                    "short_info": short_info
                }
            }
            json_headers = {**self.headers, "Content-Type": "application/json"}
            create_response = requests.post(url, headers=json_headers, json=payload, timeout=10)
            create_response.raise_for_status()
            
            created_data = create_response.json()
            city_id = created_data["data"]["id"]
            logger.info(f"City '{name}' successfully created. ID: {city_id}")
            return city_id
            
        except Exception as e:
            logger.error(f"Error in get_or_create_city for '{name}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response details: {e.response.text}")
            return None

    def upload_image(self, file_path: str) -> int:
        """
        Uploads a local image to Strapi's Media Library.
        
        Args:
            file_path (str): The local path of the image file.
            
        Returns:
            int: Strapi Media ID or None if upload failed.
        """
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Image path is invalid or does not exist: {file_path}")
            return None
            
        url = f"{self.api_url}/api/upload"
        
        try:
            logger.info(f"Uploading image '{os.path.basename(file_path)}' to Strapi Media Library...")
            
            with open(file_path, "rb") as image_file:
                files = {
                    "files": (os.path.basename(file_path), image_file, "image/jpeg")
                }
                # Do NOT pass Content-Type header; requests handles multipart boundary automatically
                response = requests.post(url, headers=self.headers, files=files, timeout=30)
                response.raise_for_status()
                
                uploaded_files = response.json()
                if isinstance(uploaded_files, list) and len(uploaded_files) > 0:
                    media_id = uploaded_files[0]["id"]
                    logger.info(f"Image uploaded successfully. Media ID: {media_id}")
                    return media_id
                else:
                    logger.error(f"Unexpected upload response format: {uploaded_files}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response details: {e.response.text}")
            return None

    def create_place(self, name: str, description_tr: str, description_en: str, rating: float, city_id: int, image_id: int = None) -> bool:
        """
        Creates a new Place record in Strapi.
        
        Args:
            name (str): Name of the place.
            description_tr (str): Description in Turkish.
            description_en (str): Description in English.
            rating (float): Star rating of the place.
            city_id (int): City ID relation.
            image_id (int, optional): Cover image media ID relation.
            
        Returns:
            bool: True if created successfully, False otherwise.
        """
        url = f"{self.api_url}/api/places"
        
        # Check if the place already exists in that city to avoid duplicate insertions
        try:
            check_params = {
                "filters[name][$eq]": name,
                "filters[city][id][$eq]": city_id
            }
            check_response = requests.get(url, headers=self.headers, params=check_params, timeout=10)
            if check_response.status_code == 200:
                check_data = check_response.json()
                if check_data.get("data") and len(check_data["data"]) > 0:
                    logger.info(f"Place '{name}' already exists in city ID {city_id}. Skipping creation.")
                    return True
        except Exception as e:
            logger.warning(f"Failed to check duplicate for place '{name}': {e}")
            
        # Create place payload
        payload = {
            "data": {
                "name": name,
                "description_tr": description_tr,
                "description_en": description_en,
                "rating": rating,
                "city": city_id
            }
        }
        
        if image_id:
            payload["data"]["cover_image"] = image_id
            
        json_headers = {**self.headers, "Content-Type": "application/json"}
        
        try:
            logger.info(f"Creating place '{name}' in Strapi...")
            response = requests.post(url, headers=json_headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Place '{name}' successfully created in Strapi.")
            return True
        except Exception as e:
            logger.error(f"Error creating place '{name}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response details: {e.response.text}")
            return False

if __name__ == "__main__":
    # Standard quick check
    api = StrapiAPI()
    print("Strapi Client initialized. Base URL:", api.api_url)

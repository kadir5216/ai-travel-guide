import os
import mimetypes
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

    @staticmethod
    def _content_ref(entry: dict):
        """Return the safest REST identifier for Strapi v5/v4 content entries."""
        return entry.get("documentId") or entry.get("id")

    @staticmethod
    def _db_id(entry: dict):
        """Return the numeric database id when Strapi includes it in the response."""
        return entry.get("id")

    def _city_ref(self, entry: dict) -> dict:
        return {
            "id": self._db_id(entry),
            "documentId": self._content_ref(entry),
        }

    def get_or_create_city(self, name: str, name_en: str, country: str, country_en: str, short_info: str, short_info_en: str) -> dict:
        """
        Checks if a city exists by name. If it does, returns its ID. If not, creates it.
        Also updates translations for existing cities if possible.
        
        Args:
            name (str): City name (TR).
            name_en (str): City name in English.
            country (str): Country name (TR).
            country_en (str): Country name in English.
            short_info (str): Short description of the city (TR).
            short_info_en (str): Short description of the city in English.
            
        Returns:
            dict: City reference with id/documentId, or None if error.
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
            
            # If city exists, return its ID and try updating translations
            if data.get("data") and len(data["data"]) > 0:
                city_ref = self._city_ref(data["data"][0])
                city_document_id = city_ref["documentId"]
                logger.info(f"City '{name}' found. Ref: {city_document_id}. Updating translations...")
                try:
                    update_payload = {
                        "data": {
                            "name_en": name_en,
                            "country_en": country_en,
                            "short_info_en": short_info_en
                        }
                    }
                    json_headers = {**self.headers, "Content-Type": "application/json"}
                    update_response = requests.put(f"{url}/{city_document_id}", headers=json_headers, json=update_payload, timeout=10)
                    update_response.raise_for_status()
                except Exception as ue:
                    logger.warning(f"Could not update city translations (schema might not support them): {ue}")
                return city_ref
            
            # If not, create it
            logger.info(f"City '{name}' not found. Creating a new record...")
            json_headers = {**self.headers, "Content-Type": "application/json"}
            
            try:
                # Try creating with English translation fields
                payload = {
                    "data": {
                        "name": name,
                        "name_en": name_en,
                        "country": country,
                        "country_en": country_en,
                        "short_info": short_info,
                        "short_info_en": short_info_en
                    }
                }
                create_response = requests.post(url, headers=json_headers, json=payload, timeout=10)
                create_response.raise_for_status()
            except requests.exceptions.HTTPError as he:
                if he.response is not None and he.response.status_code == 400:
                    logger.warning("Strapi returned 400. Schema might be missing multilingual fields. Retrying with basic fields...")
                    payload = {
                        "data": {
                            "name": name,
                            "country": country,
                            "short_info": short_info
                        }
                    }
                    create_response = requests.post(url, headers=json_headers, json=payload, timeout=10)
                    create_response.raise_for_status()
                else:
                    raise he
            
            created_data = create_response.json()
            city_ref = self._city_ref(created_data["data"])
            logger.info(f"City '{name}' successfully created. Ref: {city_ref['documentId']}")
            return city_ref
            
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
                # Detect MIME type automatically instead of hardcoding image/jpeg
                mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
                files = {
                    "files": (os.path.basename(file_path), image_file, mime_type)
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

    def create_place(self, name: str, name_en: str, description_tr: str, description_en: str, rating: float, city_ref, image_id: int = None) -> bool:
        """
        Creates a new Place record in Strapi.
        
        Args:
            name (str): Name of the place (TR).
            name_en (str): Name of the place in English.
            description_tr (str): Description in Turkish.
            description_en (str): Description in English.
            rating (float): Star rating of the place.
            city_ref: City relation reference returned by get_or_create_city.
            image_id (int, optional): Cover image media ID relation.
            
        Returns:
            bool: True if created successfully, False otherwise.
        """
        url = f"{self.api_url}/api/places"
        city_document_id = city_ref.get("documentId") if isinstance(city_ref, dict) else city_ref
        city_db_id = city_ref.get("id") if isinstance(city_ref, dict) else city_ref
        city_relation_value = city_document_id or city_db_id
        city_relation_fallback = city_db_id or city_document_id
        
        # Check if the place already exists in that city to avoid duplicate insertions
        place_exists = False
        place_id = None
        try:
            base_check_params = {
                "filters[$or][0][name][$eq]": name,
                "filters[$or][1][name_en][$eq]": name_en,
            }
            relation_filters = []
            if city_document_id and city_document_id != city_db_id:
                relation_filters.extend([
                    {"filters[city][documentId][$eq]": city_document_id},
                    {"filters[cities][documentId][$eq]": city_document_id},
                ])
            if city_db_id:
                relation_filters.extend([
                    {"filters[city][id][$eq]": city_db_id},
                    {"filters[cities][id][$eq]": city_db_id},
                ])
            # i18n-enabled relation filters can be strict; fall back to matching place names.
            relation_filters.append({})

            for relation_filter in relation_filters:
                check_params = dict(base_check_params)
                check_params.update(relation_filter)
                check_response = requests.get(url, headers=self.headers, params=check_params, timeout=10)
                if check_response.status_code != 200:
                    continue

                check_data = check_response.json()
                if check_data.get("data") and len(check_data["data"]) > 0:
                    place_exists = True
                    place_id = check_data["data"][0].get("documentId") or check_data["data"][0].get("id")
                    break
        except Exception as e:
            logger.warning(f"Failed to check duplicate for place '{name}': {e}")
            
        if place_exists and place_id is not None:
            try:
                logger.info(f"Place '{name}' already exists in city ref {city_relation_value} (ID: {place_id}). Updating record...")
                payload = {
                    "data": {
                        "name": name,
                        "name_en": name_en,
                        "description_tr": description_tr,
                        "description_en": description_en,
                        "rating": rating,
                        "city": {"connect": [city_relation_value]} if city_relation_value else None,
                    }
                }
                if payload["data"]["city"] is None:
                    payload["data"].pop("city")
                if image_id is not None:
                    payload["data"]["cover_image"] = image_id
                    
                json_headers = {**self.headers, "Content-Type": "application/json"}
                response = requests.put(f"{url}/{place_id}", headers=json_headers, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"Place '{name}' successfully updated in Strapi.")
                return True
            except requests.exceptions.HTTPError as he:
                if he.response is not None and he.response.status_code == 400:
                    logger.warning("Strapi returned 400 during update. Retrying without name_en...")
                    payload = {
                        "data": {
                            "name": name,
                            "description_tr": description_tr,
                            "description_en": description_en,
                            "rating": rating,
                            "city": {"connect": [city_relation_value]} if city_relation_value else None,
                        }
                    }
                    if payload["data"]["city"] is None:
                        payload["data"].pop("city")
                    if image_id is not None:
                        payload["data"]["cover_image"] = image_id
                    json_headers = {**self.headers, "Content-Type": "application/json"}
                    response = requests.put(f"{url}/{place_id}", headers=json_headers, json=payload, timeout=10)
                    response.raise_for_status()
                    logger.info(f"Place '{name}' successfully updated without name_en.")
                    return True
                else:
                    logger.error(f"Error updating place '{name}' (ID: {place_id}): {he}")
                    return False
            except Exception as e:
                logger.error(f"Error updating place '{name}' (ID: {place_id}): {e}")
                return False
            
        # Create place payload
        payload = {
            "data": {
                "name": name,
                "name_en": name_en,
                "description_tr": description_tr,
                "description_en": description_en,
                "rating": rating,
                "city": {"connect": [city_relation_value]} if city_relation_value else None
            }
        }
        if payload["data"]["city"] is None:
            payload["data"].pop("city")
        
        if image_id:
            payload["data"]["cover_image"] = image_id
            
        json_headers = {**self.headers, "Content-Type": "application/json"}
        
        try:
            logger.info(f"Creating place '{name}' in Strapi...")
            response = requests.post(url, headers=json_headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Place '{name}' successfully created in Strapi.")
            return True
        except requests.exceptions.HTTPError as he:
            if he.response is not None and he.response.status_code == 400:
                logger.warning("Strapi returned 400 during creation. Retrying with fallback relation payload...")
                payload = {
                    "data": {
                        "name": name,
                        "name_en": name_en,
                        "description_tr": description_tr,
                        "description_en": description_en,
                        "rating": rating,
                        "city": city_relation_fallback
                    }
                }
                if image_id:
                    payload["data"]["cover_image"] = image_id
                try:
                    response = requests.post(url, headers=json_headers, json=payload, timeout=10)
                    response.raise_for_status()
                    logger.info(f"Place '{name}' successfully created with fallback relation payload.")
                    return True
                except requests.exceptions.HTTPError as second_he:
                    if second_he.response is not None and second_he.response.status_code == 400:
                        logger.warning("Fallback relation payload returned 400. Retrying without name_en...")
                        payload["data"].pop("name_en", None)
                        try:
                            response = requests.post(url, headers=json_headers, json=payload, timeout=10)
                            response.raise_for_status()
                            logger.info(f"Place '{name}' successfully created without name_en.")
                            return True
                        except Exception as final_e:
                            logger.error(f"Final fallback failed for place '{name}': {final_e}")
                            if hasattr(final_e, 'response') and final_e.response is not None:
                                logger.error(f"Response details: {final_e.response.text}")
                            return False
                    logger.error(f"Fallback relation payload failed for place '{name}': {second_he}")
                    if second_he.response is not None:
                        logger.error(f"Response details: {second_he.response.text}")
                    return False
            else:
                logger.error(f"Error creating place '{name}': {he}")
                if he.response is not None:
                    logger.error(f"Response details: {he.response.text}")
                return False
        except Exception as e:
            logger.error(f"Error creating place '{name}': {e}")
            return False

if __name__ == "__main__":
    # Standard quick check
    api = StrapiAPI()
    print("Strapi Client initialized. Base URL:", api.api_url)

import os
import requests
import logging
from dotenv import load_dotenv

# Load frontend env variables
load_dotenv()

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class StrapiClient:
    """
    Client for querying Strapi API in Streamlit frontend.
    Handles data fetching and parsing for both Strapi v4 and v5 formats.
    """
    def __init__(self):
        api_url = os.getenv("STRAPI_URL", "").strip().rstrip("/")
        internal_hostport = os.getenv("STRAPI_INTERNAL_HOSTPORT", "").strip().rstrip("/")

        if not api_url and internal_hostport:
            api_url = f"http://{internal_hostport}"
        elif not api_url:
            api_url = "http://localhost:1337"
        elif not api_url.startswith("http"):
            api_url = f"https://{api_url}"

        self.api_url = api_url
        self.token = os.getenv("STRAPI_API_TOKEN", "")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def fetch_cities(self):
        """
        Fetches all cities from Strapi.
        
        Returns:
            list: List of parsed city dictionaries.
        """
        url = f"{self.api_url}/api/cities"
        try:
            logger.info("Fetching cities from Strapi...")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            res_data = response.json()
            
            raw_cities = res_data.get("data", [])
            parsed_cities = []
            
            for item in raw_cities:
                cid = item.get("id")
                # Handle Strapi v4 (attributes) and Strapi v5 (flat)
                attrs = item.get("attributes", {})
                if attrs:
                    parsed_cities.append({
                        "id": cid,
                        "name": attrs.get("name"),
                        "name_en": attrs.get("name_en") or attrs.get("name"),
                        "country": attrs.get("country"),
                        "country_en": attrs.get("country_en") or attrs.get("country"),
                        "short_info": attrs.get("short_info"),
                        "short_info_en": attrs.get("short_info_en") or attrs.get("short_info")
                    })
                else:
                    parsed_cities.append({
                        "id": cid,
                        "name": item.get("name"),
                        "name_en": item.get("name_en") or item.get("name"),
                        "country": item.get("country"),
                        "country_en": item.get("country_en") or item.get("country"),
                        "short_info": item.get("short_info"),
                        "short_info_en": item.get("short_info_en") or item.get("short_info")
                    })
            
            logger.info(f"Loaded {len(parsed_cities)} cities.")
            return parsed_cities
            
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Strapi. Is the server running?")
            return None  # None = connection error (different from empty list)
        except Exception as e:
            logger.error(f"Error fetching cities: {e}")
            return None

    def fetch_places(self, city_id: int):
        """
        Fetches places for a specific city, populated with relations (cover_image, city).
        The relation field can be named "cities" or "city" depending on the
        Strapi content-type schema, so both filters are tried.
        
        Args:
            city_id (int): City ID to filter.
            
        Returns:
            list: List of parsed place dictionaries.
        """
        url = f"{self.api_url}/api/places"

        try:
            logger.info(f"Fetching places for city ID {city_id} from Strapi...")
            response = None
            last_error = None
            filter_params = [
                {"filters[city][id][$eq]": city_id, "populate": "*"},
                {"filters[cities][id][$eq]": city_id, "populate": "*"},
            ]

            for params in filter_params:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                if response.ok:
                    break
                last_error = response

            if response is None or not response.ok:
                if last_error is not None:
                    last_error.raise_for_status()
                return []

            res_data = response.json()
            
            raw_places = res_data.get("data", [])
            parsed_places = []
            
            for item in raw_places:
                pid = item.get("id")
                attrs = item.get("attributes", {})
                
                if attrs:  # Strapi v4 structure
                    name = attrs.get("name")
                    name_en = attrs.get("name_en") or attrs.get("name")
                    desc_tr = attrs.get("description_tr")
                    desc_en = attrs.get("description_en")
                    rating = attrs.get("rating")
                    
                    # Resolve media attributes
                    cover_image_data = attrs.get("cover_image", {})
                    img_url = None
                    if cover_image_data and "data" in cover_image_data and cover_image_data["data"]:
                        img_attrs = cover_image_data["data"].get("attributes", {})
                        if img_attrs:
                            img_url = img_attrs.get("url")
                        else:
                            img_url = cover_image_data["data"].get("url")
                else:  # Strapi v5 or flat structure
                    name = item.get("name")
                    name_en = item.get("name_en") or item.get("name")
                    desc_tr = item.get("description_tr")
                    desc_en = item.get("description_en")
                    rating = item.get("rating")
                    
                    cover_image_data = item.get("cover_image")
                    img_url = cover_image_data.get("url") if cover_image_data else None
                
                # Format URL: prepend Strapi base URL if it's a relative path
                full_image_url = None
                if img_url:
                    if img_url.startswith("http"):
                        full_image_url = img_url
                    else:
                        full_image_url = f"{self.api_url}{img_url}"
                
                parsed_places.append({
                    "id": pid,
                    "name": name,
                    "name_en": name_en,
                    "description_tr": desc_tr,
                    "description_en": desc_en,
                    "rating": rating,
                    "image_url": full_image_url
                })
                
            logger.info(f"Loaded {len(parsed_places)} places.")
            return parsed_places
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Strapi for places (city {city_id}).")
            return None
        except Exception as e:
            logger.error(f"Error fetching places for city {city_id}: {e}")
            return []

if __name__ == "__main__":
    # Test fetch
    client = StrapiClient()
    print("Testing city fetch:")
    cities = client.fetch_cities()
    print("Cities found:", cities)

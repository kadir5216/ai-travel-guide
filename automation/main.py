import os
import json
import logging
from dotenv import load_dotenv

# Import our helper modules
from translator import translate_text
from content_enricher import enrich_city_info, enrich_place_description
from image_generator import generate_and_save_image
from strapi_api import StrapiAPI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load configuration from automation/.env regardless of the current working directory.
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting AI Travel Guide Automation Pipeline...")
    
    # Retrieve configuration parameters
    api_url = os.getenv("STRAPI_URL")
    api_token = os.getenv("STRAPI_API_TOKEN")
    
    # Provide helpful troubleshooting messages if not configured yet
    if not api_url or not api_token or api_token == "your_strapi_api_token_here":
        logger.error("Configuration Error: STRAPI_URL and STRAPI_API_TOKEN must be configured.")
        logger.error("Please configure your .env file in the automation directory before running this pipeline.")
        logger.info("Read README.md for step-by-step instructions on creating a Strapi token.")
        return

    # Initialize Strapi client
    strapi = StrapiAPI(api_url, api_token)
    
    # Path to input JSON
    data_path = os.path.join(BASE_DIR, "data", "places.json")
    if not os.path.exists(data_path):
        logger.error(f"Data file not found at path: {data_path}")
        return
        
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            cities_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read places.json data file: {e}")
        return
        
    logger.info(f"Successfully loaded {len(cities_data)} cities from data source.")
    
    # Process each city
    for item in cities_data:
        city_info = item.get("city", {})
        places_list = item.get("places", [])
        
        city_name = city_info.get("name")
        country = city_info.get("country")
        short_info = city_info.get("short_info")
        
        if not city_name:
            logger.warning("Skipping entry with empty city name.")
            continue
            
        logger.info("\n" + "="*50 + f"\nProcessing City: {city_name} ({country})\n" + "="*50)
        
        # Enrich city intro with AI, then translate it to English
        enriched_short_info = enrich_city_info(city_name, country, short_info)
        city_name_en = translate_text(city_name, source="tr", target="en") or city_name
        country_en = translate_text(country, source="tr", target="en") or country
        short_info_en = translate_text(enriched_short_info, source="tr", target="en") or enriched_short_info
        
        # 1. Resolve City ID (Get or Create)
        city_ref = strapi.get_or_create_city(
            name=city_name,
            name_en=city_name_en,
            country=country,
            country_en=country_en,
            short_info=enriched_short_info,
            short_info_en=short_info_en
        )
        if not city_ref:
            logger.error(f"Could not resolve City ID for '{city_name}'. Skipping all associated places...")
            continue
            
        # Process all places in the city
        for place in places_list:
            place_name = place.get("name")
            desc_tr = place.get("description_tr")
            rating = place.get("rating", 5.0)
            
            if not place_name or not desc_tr:
                logger.warning(f"Place '{place_name}' has missing information. Skipping...")
                continue
                
            logger.info(f"\n--- Processing Place: {place_name} ---")
            
            # Determine appropriate names for Turkish and English contexts
            is_turkish_context = (country.lower() == "türkiye" or country.lower() == "turkey")
            if is_turkish_context:
                name_tr = place_name
                name_en = translate_text(place_name, source="tr", target="en") or place_name
            else:
                name_en = place_name
                name_tr = translate_text(place_name, source="en", target="tr") or place_name
            
            # 2. Enrich Turkish description with AI, then translate it to English
            enriched_desc_tr = enrich_place_description(place_name, city_name, country, desc_tr)
            desc_en = translate_text(enriched_desc_tr, source="tr", target="en")
            if not desc_en:
                logger.warning(f"Translation returned empty. Falling back to Turkish description.")
                desc_en = enriched_desc_tr
                
            # 3. Generate image using Pollinations AI (with HuggingFace/picsum fallback)
            local_image_path = generate_and_save_image(place_name, city_name, output_dir=os.path.join(BASE_DIR, "images"))
            
            # 4. Upload image to Strapi Media Library
            image_id = None
            if local_image_path:
                image_id = strapi.upload_image(local_image_path)
                if not image_id:
                    logger.warning(f"Image upload failed for '{place_name}'. Placing without cover image...")
            else:
                logger.warning(f"Image generation failed for '{place_name}'. Placing without cover image...")
                
            # 5. Create Place record in Strapi
            success = strapi.create_place(
                name=name_tr,
                name_en=name_en,
                description_tr=enriched_desc_tr,
                description_en=desc_en,
                rating=rating,
                city_ref=city_ref,
                image_id=image_id
            )
            
            if success:
                logger.info(f"Finished processing place '{place_name}' successfully.")
            else:
                logger.error(f"Failed to add place '{place_name}' to database.")
                
    logger.info("\n" + "="*50 + "\nAutomation Pipeline Completed!\n" + "="*50)

if __name__ == "__main__":
    main()

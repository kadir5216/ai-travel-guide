import os
import json
import logging
from dotenv import load_dotenv

# Import our helper modules
from translator import translate_text
from image_generator import generate_and_save_image
from strapi_api import StrapiAPI

# Load configuration from .env
load_dotenv()

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
    data_path = os.path.join("data", "places.json")
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
        
        # 1. Resolve City ID (Get or Create)
        city_id = strapi.get_or_create_city(city_name, country, short_info)
        if not city_id:
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
            
            # 2. Translate Turkish description to English
            desc_en = translate_text(desc_tr, source="tr", target="en")
            if not desc_en:
                logger.warning(f"Translation returned empty. Falling back to Turkish description.")
                desc_en = desc_tr
                
            # 3. Generate image using Pollinations AI
            local_image_path = generate_and_save_image(place_name, city_name, output_dir="images")
            
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
                name=place_name,
                description_tr=desc_tr,
                description_en=desc_en,
                rating=rating,
                city_id=city_id,
                image_id=image_id
            )
            
            if success:
                logger.info(f"Finished processing place '{place_name}' successfully.")
            else:
                logger.error(f"Failed to add place '{place_name}' to database.")
                
    logger.info("\n" + "="*50 + "\nAutomation Pipeline Completed!\n" + "="*50)

if __name__ == "__main__":
    main()

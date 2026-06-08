import os
import re
import requests
import logging
import urllib.parse

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def slugify(text: str) -> str:
    """
    Converts text to a slug suitable for filenames.
    """
    # Replace Turkish chars
    translation_table = str.maketrans("ğüşıöçĞÜŞİÖÇ", "gusyocGUSYOC")
    text = text.translate(translation_table)
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def generate_and_save_image(place_name: str, city_name: str, output_dir: str = "images") -> str:
    """
    Generates an image for a specific place in a city using Pollinations AI and saves it locally.
    
    Args:
        place_name (str): Name of the tourist place.
        city_name (str): Name of the city it is located in.
        output_dir (str): Local directory to save the image (default 'images').
        
    Returns:
        str: Absolute path of the saved image, or None if failed.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Build prompt for a high-quality travel/scenic photograph
        prompt = f"Professional travel photography of {place_name} in {city_name}, highly detailed, beautiful lighting, scenic view, realistic, 4k"
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Pollinations AI URL
        # We specify width and height for card ratio, and nologo to remove watermark
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true"
        
        logger.info(f"Generating image for '{place_name}' using Pollinations AI...")
        logger.info(f"Prompt: {prompt}")
        
        # Request image bytes
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            filename = f"{slugify(city_name)}_{slugify(place_name)}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
                
            logger.info(f"Image successfully saved to: {filepath}")
            return os.path.abspath(filepath)
        else:
            logger.error(f"Failed to generate image from Pollinations AI. Status code: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating or saving image: {e}")
        return None

if __name__ == "__main__":
    # Quick self-test
    img_path = generate_and_save_image("Galata Tower", "Istanbul")
    print(f"Generated Image Path: {img_path}")

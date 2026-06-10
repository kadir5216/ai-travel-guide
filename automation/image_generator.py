import os
import re
import time
import requests
import logging
import urllib.parse
from translator import translate_text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """
    Converts text to a slug suitable for filenames.
    Handles Turkish special characters.
    """
    translation_table = str.maketrans("ğüşıöçĞÜŞİÖÇ", "gusyocGUSYOC")
    text = text.translate(translation_table)
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


def _build_prompt(place_name: str, city_name: str) -> str:
    """
    Builds an English AI image generation prompt from place and city names.
    Translates Turkish names to English for better prompt quality.
    
    Args:
        place_name (str): Name of the tourist place.
        city_name (str): Name of the city.
        
    Returns:
        str: English prompt string for AI image generation.
    """
    clean_place = translate_text(place_name, source="tr", target="en") or place_name
    clean_city = translate_text(city_name, source="tr", target="en") or city_name
    prompt = (
        f"Professional travel photography of {clean_place} in {clean_city}, "
        f"highly detailed, beautiful lighting, scenic view, realistic, 4k quality"
    )
    return prompt


def _generate_with_pollinations(prompt: str, filepath: str) -> bool:
    """
    Generates an image using Pollinations AI service.
    
    Pollinations AI image generation via a simple GET request.
    Current Pollinations unified API requires an API key.
    
    Args:
        prompt (str): The text prompt describing the desired image.
        filepath (str): Local file path to save the generated image.
        
    Returns:
        bool: True if image was successfully generated and saved.
    """
    pollinations_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    if not pollinations_key:
        logger.warning("POLLINATIONS_API_KEY is not set. Skipping Pollinations AI.")
        return False

    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
    params = {
        "width": 1024,
        "height": 768,
        "model": "flux",
    }
    headers = {"Authorization": f"Bearer {pollinations_key}"}
    
    try:
        logger.info(f"Generating image via Pollinations AI...")
        logger.info(f"Prompt: {prompt}")
        
        response = requests.get(url, headers=headers, params=params, timeout=90, allow_redirects=True)
        
        content_type = response.headers.get("content-type", "")
        if response.status_code == 200 and content_type.startswith("image/") and len(response.content) > 1000:
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info(f"Pollinations AI image successfully saved to: {filepath}")
            return True
        else:
            logger.error(
                f"Pollinations AI failed. Status: {response.status_code}, "
                f"Content-Type: {content_type}, Size: {len(response.content)} bytes"
            )
            return False
    except requests.exceptions.Timeout:
        logger.error("Pollinations AI request timed out (90s).")
        return False
    except Exception as e:
        logger.error(f"Error with Pollinations AI: {e}")
        return False


def _generate_with_huggingface(prompt: str, filepath: str, hf_token: str) -> bool:
    """
    Generates an image using HuggingFace Inference API (Stable Diffusion XL).
    
    Args:
        prompt (str): The text prompt describing the desired image.
        filepath (str): Local file path to save the generated image.
        hf_token (str): HuggingFace API token.
        
    Returns:
        bool: True if image was successfully generated and saved.
    """
    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}
    
    try:
        logger.info(f"Generating image via HuggingFace Stable Diffusion XL...")
        logger.info(f"Prompt: {prompt}")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200 and len(response.content) > 1000:
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info(f"HuggingFace AI image successfully saved to: {filepath}")
            return True
        else:
            logger.error(f"HuggingFace API failed. Status: {response.status_code}, Error: {response.text[:200]}")
            return False
    except Exception as e:
        logger.error(f"Error with HuggingFace: {e}")
        return False


def _generate_with_picsum(place_name: str, filepath: str) -> bool:
    """
    Downloads a fallback image from picsum.photos using place name as seed.
    
    Args:
        place_name (str): Name used as seed for consistent image selection.
        filepath (str): Local file path to save the image.
        
    Returns:
        bool: True if image was successfully downloaded and saved.
    """
    encoded_name = urllib.parse.quote(place_name)
    url = f"https://picsum.photos/seed/{encoded_name}/1024/768"
    
    try:
        logger.info(f"Downloading fallback image from picsum.photos...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            logger.info(f"Fallback image saved to: {filepath}")
            return True
        else:
            logger.error(f"Picsum failed. Status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error with picsum: {e}")
        return False


def generate_and_save_image(place_name: str, city_name: str, output_dir: str = "images") -> str:
    """
    Generates a travel image for a specific place using AI services.
    
    Uses a cascading fallback strategy:
      1. Pollinations AI (Primary - free, no API key needed)
      2. HuggingFace Stable Diffusion XL (Secondary - requires API key)
      3. picsum.photos (Last resort - random stock photo)
    
    Args:
        place_name (str): Name of the tourist place.
        city_name (str): Name of the city it is located in.
        output_dir (str): Local directory to save the image (default 'images').
        
    Returns:
        str: Absolute path of the saved image, or None if all methods failed.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{slugify(city_name)}_{slugify(place_name)}.jpg"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            logger.info(f"Using existing generated image: {filepath}")
            return os.path.abspath(filepath)
        
        # Build an English prompt for best AI results
        prompt = _build_prompt(place_name, city_name)
        
        # Strategy 1: Pollinations AI (Primary)
        logger.info(f"[1/3] Attempting Pollinations AI for '{place_name}'...")
        if _generate_with_pollinations(prompt, filepath):
            return os.path.abspath(filepath)
        
        # Strategy 2: HuggingFace Stable Diffusion (Secondary)
        hf_token = os.getenv("HUGGINGFACE_API_KEY")
        if hf_token:
            logger.info(f"[2/3] Attempting HuggingFace for '{place_name}'...")
            if _generate_with_huggingface(prompt, filepath, hf_token):
                return os.path.abspath(filepath)
        else:
            logger.warning("[2/3] HUGGINGFACE_API_KEY not set. Skipping HuggingFace.")
        
        # Strategy 3: Picsum (Last Resort)
        logger.warning(f"[3/3] AI generation failed. Using picsum.photos fallback for '{place_name}'...")
        clean_place = translate_text(place_name, source="tr", target="en") or place_name
        if _generate_with_picsum(clean_place, filepath):
            return os.path.abspath(filepath)
        
        logger.error(f"All image generation methods failed for '{place_name}'.")
        return None
        
    except Exception as e:
        logger.error(f"General error in generate_and_save_image: {e}")
        return None


if __name__ == "__main__":
    # Quick self-test
    print("Testing Pollinations AI image generation...")
    img_path = generate_and_save_image("Galata Kulesi", "İstanbul")
    print(f"Generated Image Path: {img_path}")

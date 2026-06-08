import logging
from deep_translator import GoogleTranslator

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def translate_text(text: str, source: str = "tr", target: str = "en") -> str:
    """
    Translates text from source language to target language.
    
    Args:
        text (str): The text to translate.
        source (str): Source language code (default 'tr').
        target (str): Target language code (default 'en').
        
    Returns:
        str: The translated text, or the original text if translation fails.
    """
    if not text:
        return ""
        
    try:
        logger.info(f"Translating text: '{text[:30]}...' from '{source}' to '{target}'")
        translated = GoogleTranslator(source=source, target=target).translate(text)
        logger.info("Translation completed successfully.")
        return translated
    except Exception as e:
        logger.error(f"Error during translation: {e}")
        # Return original text as a fallback
        return text

if __name__ == "__main__":
    # Quick self-test
    test_tr = "Galata Kulesi, İstanbul'un en eski ve en güzel yapılarından biridir."
    test_en = translate_text(test_tr)
    print(f"Original (TR): {test_tr}")
    print(f"Translated (EN): {test_en}")

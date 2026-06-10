import logging
import os
import re
import urllib.parse

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
POLLINATIONS_TEXT_API_URL = "https://gen.pollinations.ai/text"
POLLINATIONS_LEGACY_TEXT_API_URL = "https://text.pollinations.ai"


def _system_prompt() -> str:
    return (
        "Sen Turkce yazan profesyonel bir gezi rehberi editorusun. "
        "Cevaplarini tek paragraf halinde, akici ve bilgilendirici yaz. "
        "Markdown, baslik, secenek, madde isareti, fiyat, calisma saati veya kesin olmayan guncel bilgi kullanma. "
        "Temel aciklamada yer almiyorsa kesin yil, tarih veya tartismali ayrinti ekleme. "
        "Sadece istenen tanitim paragrafini dondur."
    )


def _clean_generated_text(text: str) -> str:
    """Normalize AI output into a single clean Turkish paragraph."""
    if not text:
        return ""

    text = text.strip()
    text = re.sub(r"^```(?:\w+)?|```$", "", text).strip()
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^(İşte|Iste|Elbette|Tabii)[^:]{0,120}:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(Seçenek|Secenek)\s*\d+\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \"'")


def _call_groq_text(prompt: str, *, max_tokens: int = 360) -> str:
    """
    Generate travel-guide text with Groq's OpenAI-compatible Chat Completions API.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"

    if not api_key:
        logger.warning("GROQ_API_KEY is not set. Groq text enrichment skipped.")
        return ""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.65,
        "max_tokens": max_tokens,
        "top_p": 0.9,
    }

    try:
        logger.info(f"Generating text with Groq model: {model}")
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return _clean_generated_text(content)
    except Exception as exc:
        logger.warning(f"Groq text enrichment failed: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            logger.warning(f"Response details: {exc.response.text[:300]}")
        return ""


def _call_pollinations_text(prompt: str, *, max_tokens: int = 360) -> str:
    """
    Fallback text generation with Pollinations.
    """
    api_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    model = os.getenv("POLLINATIONS_TEXT_MODEL", "nova-fast").strip() or "nova-fast"

    if not api_key:
        logger.warning("POLLINATIONS_API_KEY is not set. Pollinations text fallback skipped.")
        return ""

    encoded_prompt = urllib.parse.quote(prompt, safe="")
    url = f"{POLLINATIONS_TEXT_API_URL}/{encoded_prompt}"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "model": model,
        "temperature": 0.7,
        "system": _system_prompt(),
        "private": "true",
        "max_tokens": max_tokens,
    }

    try:
        logger.info(f"Generating fallback text with Pollinations model: {model}")
        response = requests.get(url, headers=headers, params=params, timeout=90)
        if response.status_code == 402:
            logger.warning("Pollinations balance is insufficient. Retrying with legacy public text endpoint.")
            legacy_url = f"{POLLINATIONS_LEGACY_TEXT_API_URL}/{encoded_prompt}"
            legacy_params = {
                "model": "mistral",
                "temperature": 0.7,
                "system": _system_prompt(),
            }
            response = requests.get(legacy_url, params=legacy_params, timeout=90)
        response.raise_for_status()
        return _clean_generated_text(response.text)
    except Exception as exc:
        logger.warning(f"Pollinations text enrichment failed: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            logger.warning(f"Response details: {exc.response.text[:300]}")
        return ""


def _generate_text(prompt: str, *, max_tokens: int) -> str:
    """
    Text generation strategy:
      1. Groq API (primary)
      2. Pollinations text API (fallback)
      3. Original source text (handled by caller)
    """
    return _call_groq_text(prompt, max_tokens=max_tokens) or _call_pollinations_text(prompt, max_tokens=max_tokens)


def enrich_city_info(city_name: str, country: str, base_info: str) -> str:
    """
    Enriches a city intro using Groq text generation.

    Falls back to the original text if generation fails.
    """
    prompt = (
        f"Sehir: {city_name}\n"
        f"Ulke: {country}\n"
        f"Temel bilgi: {base_info}\n\n"
        "Bu sehir icin 55-85 kelimelik, turistlere yonelik, dogal ve bilgilendirici "
        "bir Turkce tanitim paragrafi yaz. Sehrin kulturel atmosferini, gezilecek "
        "yer cesitliligini ve ziyaret deneyimini vurgula."
    )
    enriched = _generate_text(prompt, max_tokens=280)
    return enriched or base_info


def enrich_place_description(place_name: str, city_name: str, country: str, base_description: str) -> str:
    """
    Enriches a place description using Groq text generation.

    Falls back to the original text if generation fails.
    """
    prompt = (
        f"Mekan: {place_name}\n"
        f"Sehir: {city_name}\n"
        f"Ulke: {country}\n"
        f"Temel aciklama: {base_description}\n\n"
        "Bu mekan icin 80-120 kelimelik, turistik gezi rehberi uslubunda, "
        "bilgilendirici ve akici bir Turkce tanitim paragrafi yaz. Tarihi/kulturel "
        "onemi, ziyaretciye sundugu deneyim ve neden gorulmeye deger oldugu anlatilsin. "
        "Tek paragraf yaz."
    )
    enriched = _generate_text(prompt, max_tokens=420)
    return enriched or base_description


if __name__ == "__main__":
    sample = enrich_place_description(
        "Galata Kulesi",
        "İstanbul",
        "Türkiye",
        "İstanbul'un siluetini süsleyen tarihi kule.",
    )
    print(sample)

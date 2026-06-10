import json
import logging
import os

import requests
from dotenv import load_dotenv

from content_enricher import enrich_city_info, enrich_place_description
from translator import translate_text

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _record_ref(record: dict):
    return record.get("documentId") or record.get("id")


def _get_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _json_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _find_city(api_url: str, token: str, name: str) -> dict | None:
    response = requests.get(
        f"{api_url}/api/cities",
        headers=_get_headers(token),
        params={"filters[name][$eq]": name, "pagination[pageSize]": 1},
        timeout=15,
    )
    response.raise_for_status()
    records = response.json().get("data", [])
    return records[0] if records else None


def _find_place(api_url: str, token: str, name: str) -> dict | None:
    response = requests.get(
        f"{api_url}/api/places",
        headers=_get_headers(token),
        params={
            "filters[$or][0][name][$eq]": name,
            "filters[$or][1][name_en][$eq]": name,
            "pagination[pageSize]": 1,
        },
        timeout=15,
    )
    response.raise_for_status()
    records = response.json().get("data", [])
    return records[0] if records else None


def update_existing_content() -> None:
    api_url = os.getenv("STRAPI_URL", "http://localhost:1337").rstrip("/")
    token = os.getenv("STRAPI_API_TOKEN", "").strip()
    data_path = os.path.join("data", "places.json")

    if not token:
        logger.error("STRAPI_API_TOKEN is required.")
        return

    with open(data_path, "r", encoding="utf-8") as file:
        cities_data = json.load(file)

    updated_cities = 0
    updated_places = 0
    ai_city_count = 0
    ai_place_count = 0

    for city_item in cities_data:
        city = city_item.get("city", {})
        city_name = city.get("name")
        country = city.get("country")
        base_info = city.get("short_info")

        if not city_name or not country or not base_info:
            logger.warning("Skipping a city entry with missing fields.")
            continue

        logger.info(f"Enriching city intro: {city_name}")
        enriched_info = enrich_city_info(city_name, country, base_info)
        if enriched_info != base_info:
            ai_city_count += 1

        city_record = _find_city(api_url, token, city_name)
        if city_record:
            city_ref = _record_ref(city_record)
            city_name_en = translate_text(city_name, source="tr", target="en") or city_name
            country_en = translate_text(country, source="tr", target="en") or country
            enriched_info_en = translate_text(enriched_info, source="tr", target="en") or enriched_info
            payload = {
                "data": {
                    "name": city_name,
                    "name_en": city_name_en,
                    "country": country,
                    "country_en": country_en,
                    "short_info": enriched_info,
                    "short_info_en": enriched_info_en,
                }
            }
            response = requests.put(
                f"{api_url}/api/cities/{city_ref}",
                headers=_json_headers(token),
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            updated_cities += 1
        else:
            logger.warning(f"City not found in Strapi: {city_name}")

        for place in city_item.get("places", []):
            place_name = place.get("name")
            base_description = place.get("description_tr")
            if not place_name or not base_description:
                logger.warning("Skipping a place entry with missing fields.")
                continue

            logger.info(f"Enriching place description: {place_name}")
            enriched_description = enrich_place_description(place_name, city_name, country, base_description)
            if enriched_description != base_description:
                ai_place_count += 1

            place_record = _find_place(api_url, token, place_name)
            if not place_record:
                logger.warning(f"Place not found in Strapi: {place_name}")
                continue

            place_ref = _record_ref(place_record)
            description_en = translate_text(enriched_description, source="tr", target="en") or enriched_description
            payload = {
                "data": {
                    "description_tr": enriched_description,
                    "description_en": description_en,
                    "rating": place.get("rating", place_record.get("rating", 5.0)),
                }
            }
            response = requests.put(
                f"{api_url}/api/places/{place_ref}",
                headers=_json_headers(token),
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            updated_places += 1

    logger.info(
        "AI content enrichment completed. "
        f"Cities updated: {updated_cities} ({ai_city_count} AI-generated), "
        f"places updated: {updated_places} ({ai_place_count} AI-generated)."
    )


if __name__ == "__main__":
    update_existing_content()

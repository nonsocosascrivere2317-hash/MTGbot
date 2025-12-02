import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class VintedAPI:
    def __init__(self, country_code=".de"):
        self.session = requests.Session()
        self.base_url = f"https://www.vinted{country_code}"
        self.country_code = country_code

    def _get_headers(self) -> Dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
            "Referer": f"https://www.vinted{self.country_code}/",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty"
        }

    async def search_products(self, search_text: str):
        try:
            params = {
                "page": 1,
                "per_page": 20,
                "search_text": search_text,
                "order": "newest_first",
                "catalog_ids": "",
                "currency": "EUR",
                "is_for_sale": "1",
                "_vercel_no_cache": "1"
            }

            response = self.session.get(
                f"{self.base_url}/api/v2/catalog/items",
                params=params,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 403:
                logger.error("❌ Vinted blocked the request (403 Forbidden).")
                return []

            response.raise_for_status()
            data = response.json()

            items = []
            for item in data.get("items", []):
                # Immagine
                image_url = item.get("photos", [{}])[0].get("url", None)
                item["image_url"] = image_url

                items.append(item)

            return items

        except Exception as e:
            logger.error(f"Failed to search products: {e}")
            return []

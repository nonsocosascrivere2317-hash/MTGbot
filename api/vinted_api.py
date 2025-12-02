import requests
import logging
import json
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class VintedAPI:
    def __init__(self, country_code=".de", cookies_file="cookies.json"):
        self.session = requests.Session()
        self.country_code = country_code
        self.base_url = f"https://www.vinted{country_code}"
        self.cookies_file = cookies_file

        # Carica automaticamente i cookie
        self.load_cookies()

    # -----------------------------
    #  CARICA COOKIE DA cookies.json
    # -----------------------------
    def load_cookies(self):
        try:
            with open(self.cookies_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            for cookie in cookies:
                self.session.cookies.set(cookie["name"], cookie["value"])

            logger.info("🍪 Cookies caricati correttamente.")

        except Exception as e:
            logger.error(f"❌ Errore nel caricamento dei cookie: {e}")

    # -----------------------------
    #        HEADERS AGGIORNATI
    # -----------------------------
    def _get_headers(self) -> Dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9",
            "Referer": f"https://www.vinted{self.country_code}/",
            "X-XSRF-TOKEN": self.session.cookies.get("XSRF-TOKEN", ""),
            "X-Requested-With": "XMLHttpRequest",
        }

    # -----------------------------
    #       FUNZIONE DI RICERCA
    # -----------------------------
    async def search_products(self, search_text: str) -> List[Dict]:
        try:
            params = {
                "page": 1,
                "per_page": 20,
                "search_text": search_text,
                "order": "newest_first",
                "currency": "EUR",
                "is_for_sale": "1",
                "catalog_ids": "",
            }

            response = self.session.get(
                f"{self.base_url}/api/v2/catalog/items",
                params=params,
                headers=self._get_headers(),
                timeout=10
            )

            # BLOCCO ANTI 403
            if response.status_code == 403:
                logger.error("❌ Vinted ha bloccato la richiesta (403 Forbidden).")
                return []

            response.raise_for_status()
            data = response.json()

            items = []
            for item in data.get("items", []):
                # Immagine
                photos = item.get("photos", [])
                image_url = photos[0]["url"] if photos else None
                item["image_url"] = image_url

                items.append(item)

            return items

        except Exception as e:
            logger.error(f"❌ Errore nella ricerca prodotti: {e}")
            return []
